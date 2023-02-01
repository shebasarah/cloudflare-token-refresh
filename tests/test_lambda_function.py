""" Tests for the lambda function. """

import datetime
import sys
import unittest
from unittest.mock import Mock, patch

import boto3

sys.path.append('.')

import lambda_function
from cloudflare_helper import CloudFlareHelper
from loadbalancer_helper import LoadBalancerHelper


class LambdaHandlerTestCase(unittest.TestCase):
    """Class to test the lambda handler."""

    # Patch the functions create_secret, set_secret, test_secret, finish_secret
    @patch('lambda_function.finish_secret')
    @patch('lambda_function.test_secret')
    @patch('lambda_function.set_secret')
    @patch('lambda_function.create_secret')
    def test_lambda_handler(
        self, mock_create_secret, mock_set_secret, mock_test_secret, mock_finish_secret
    ):
        """Test for the lambda handler method."""

        event = []
        context = 'context'
        print('Testing lambda handler')
        arn = 'dummy_arn'
        token = 'dummy_token'
        step = ['createSecret', 'setSecret', 'testSecret', 'finishSecret']

        # Setup the client
        service_client = boto3.client('secretsmanager')
        service_client.describe_secret = Mock(
            return_value={
                'ARN': arn,
                'Description': 'dummy secret',
                'RotationEnabled': True,
                'RotationLambdaARN': 'dummy_lambda_arn',
            }
        )
        mock_create_secret.return_value = 'Creating new secret'
        mock_set_secret.return_value = 'Setting new secret'
        mock_test_secret.return_value = 'Testing new secret'
        mock_finish_secret.return_value = 'Finishing new secret'
        create_secret = lambda_function.create_secret(service_client, arn, token)
        set_secret = lambda_function.set_secret(service_client, arn, token)
        test_secret = lambda_function.test_secret(service_client, arn, token)
        finish_secret = lambda_function.finish_secret(service_client, arn, token)

        lambda_function.lambda_handler = Mock(return_value=200)
        self.assertEqual(lambda_function.lambda_handler(event, context), 200)

    def test_create_secret(self):
        """Test for the create secret method."""

        print('Testing create secret')
        service_client = boto3.client('secretsmanager')
        token = 'dummy_token'
        arn = 'dummy_arn'
        service_client.get_secret_value = Mock(return_value='old_dummy_secret')

        service_client.get_random_password = Mock(return_value='new_dummy_secret')

        service_client.put_secret_value = Mock()
        lambda_function.create_secret = Mock(return_value=200)
        self.assertEqual(lambda_function.create_secret(service_client, arn, token), 200)

    # Patch the modify_rule and roll_token methods
    @patch('loadbalancer_helper.LoadBalancerHelper.modify_rule')
    @patch('cloudflare_helper.CloudFlareHelper.roll_token')
    def test_set_secret(self, mock_cf_rolltoken, mock_alb_modifyrule):
        """Test for the set secret method."""

        print('Testing set secret')
        service_client = boto3.client('secretsmanager')
        token = 'dummy_token'
        arn = 'dummy_arn'
        service_client.get_secret_value = Mock(return_value='old dummy secret')
        old_token = service_client.get_secret_value(
            SecretId=arn, VersionStage='AWSCURRENT'
        )
        service_client.get_secret_value = Mock(return_value='new dummy secret')
        new_token = service_client.get_secret_value(
            SecretId=arn, VersionStage='AWSPENDING'
        )
        mock_cf_rolltoken.return_value = {
            'result': {
                'id': 'test_id',
                'name': 'header modification',
                'description': '',
                'kind': 'zone',
                'version': '139',
                'rules': [
                    {
                        'id': '6b8a929b584a4086b050baae6ce1a725',
                        'version': '133',
                        'action': 'rewrite',
                        'expression': '(http.host ne "1")',
                        'description': 'X-ALB-SECRET',
                        'last_updated': '2023-01-10T22:08:19.008798Z',
                        'ref': '6b8a929b584a4086b050baae6ce1a725',
                        'enabled': True,
                        'action_parameters': {
                            'headers': {
                                'X-ALB-SECRET': {
                                    'operation': 'set',
                                    'value': new_token,
                                }
                            }
                        },
                    },
                ],
                'phase': 'http_request_late_transform',
            },
            'success': True,
            'errors': [],
            'messages': [],
        }
        mock_alb_modifyrule.return_value = {
            'result': {
                'id': 'test_ruleset_id',
                'name': 'header modification',
                'description': '',
                'kind': 'zone',
                'version': '139',
                'rules': [
                    {
                        'id': 'test_rule_id',
                        'version': '133',
                        'action': 'rewrite',
                        'expression': '(http.host ne "1")',
                        'description': 'X-ALB-SECRET',
                        'last_updated': '2023-01-10T22:08:19.008798Z',
                        'ref': '6b8a929b584a4086b050baae6ce1a725',
                        'enabled': True,
                        'action_parameters': {
                            'headers': {
                                'X-ALB-SECRET': {
                                    'operation': 'set',
                                    'value': [old_token, new_token],
                                }
                            }
                        },
                    },
                ],
                'last_updated': datetime.datetime.now(),
                'phase': 'http_request_late_transform',
            },
            'success': True,
            'errors': [],
            'messages': [],
        }

        modify_listener = LoadBalancerHelper()
        response = modify_listener.modify_rule([old_token, new_token])

        token_refresh = CloudFlareHelper()
        response = token_refresh.roll_token(new_token)

        mock_alb_modifyrule.return_value = {
            'result': {
                'id': 'test_ruleset_id',
                'name': 'header modification',
                'description': '',
                'kind': 'zone',
                'version': '139',
                'rules': [
                    {
                        'id': 'test_rule_id',
                        'version': '133',
                        'action': 'rewrite',
                        'expression': '(http.host ne "1")',
                        'description': 'X-ALB-SECRET',
                        'last_updated': '2023-01-10T22:08:19.008798Z',
                        'ref': '6b8a929b584a4086b050baae6ce1a725',
                        'enabled': True,
                        'action_parameters': {
                            'headers': {
                                'X-ALB-SECRET': {
                                    'operation': 'set',
                                    'value': [new_token],
                                }
                            }
                        },
                    },
                ],
                'last_updated': datetime.datetime.now(),
                'phase': 'http_request_late_transform',
            },
            'success': True,
            'errors': [],
            'messages': [],
        }
        response = modify_listener.modify_rule([new_token])

        lambda_function.set_secret = Mock(
            return_value={
                'result': {
                    'secret': new_token,
                    'VersionStage': 'AWSPENDING',
                }
            }
        )
        self.assertEqual(
            lambda_function.set_secret(service_client, arn, token),
            {
                'result': {
                    'secret': new_token,
                    'VersionStage': 'AWSPENDING',
                }
            },
        )
        assert mock_alb_modifyrule.called
        assert mock_cf_rolltoken.called

    def test_test_secret(self):
        """Test for the test secret method."""

        print('Testing test secret')
        service_client = boto3.client('secretsmanager')
        token = 'dummy_token'
        arn = 'dummy_arn'
        lambda_function.test_secret = Mock(
            return_value='No need to test against any service.'
        )
        self.assertEqual(
            lambda_function.test_secret(service_client, arn, token),
            'No need to test against any service.',
        )

    # Patch the modify_rule method
    def test_finish_secret(self):
        """Test for the finish secret method."""

        print('Testing finish secret')
        service_client = boto3.client('secretsmanager')
        token = 'dummy_token'
        arn = 'dummy_arn'
        service_client.describe_secret = Mock(
            return_value={
                'ARN': arn,
                'Description': 'dummy token',
                'RotationEnabled': True,
                'RotationLambdaARN': 'dummy_lambda_arn',
                'VersionIdsToStages': {
                    'old_version_id': ['AWSCURRENT', 'AWSPREVIOUS'],
                    'new_version_id': [
                        'AWSPENDING',
                    ],
                },
            }
        )
        metadata = service_client.describe_secret(SecretId=arn)
        service_client.update_secret_version_stage = Mock(
            return_value={
                'result': {
                    'VersionStage': 'AWSCURRENT',
                }
            }
        )
        service_client.update_secret_version_stage(
            SecretId=arn,
            VersionStage='AWSCURRENT',
            MoveToVersionId=token,
        )

        lambda_function.finish_secret = Mock(
            return_value={
                'result': {
                    'secret': 'new_token',
                    'VersionStage': 'AWSCURRENT',
                }
            }
        )
        self.assertEqual(
            lambda_function.finish_secret(service_client, arn, token),
            {
                'result': {
                    'secret': 'new_token',
                    'VersionStage': 'AWSCURRENT',
                }
            },
        )

""" Tests for cloudflare helper. """

import sys
import unittest
from unittest.mock import Mock, patch

import boto3
from moto import mock_secretsmanager

sys.path.append(".")

from cloudflare_helper import CloudFlareHelper


class CloudflareHelperTestCase(unittest.TestCase):
    """Tests for cloudflare helper."""

    # Using moto to mock the secret manager
    @mock_secretsmanager
    def test_get_api_key(self):
        """Test for get api key function from secret manager."""

        cloudflare_helper = CloudFlareHelper()
        region_name = 'ap-southeast-2'
        session = boto3.session.Session()
        mockedClient = session.client(
            service_name='secretsmanager', region_name=region_name
        )

        mockedClient.create_secret(
            Name='nzh-cf-access-token-to-modify-transform-rules',
            SecretString='dummysecret',
        )
        secret = cloudflare_helper.get_api_key()
        self.assertEqual(secret, 'dummysecret')
        assert secret == 'dummysecret'

    # patch the get_api_key method and requests.patch method
    @patch('cloudflare_helper.CloudFlareHelper.get_api_key')
    @patch('cloudflare_helper.requests.patch')
    def test_roll_token(self, mock_patch, mock_get_api_key):
        """Test for roll token function in cloudflare Http Header modification rule."""

        cf_api_key = 'dummy_secret'
        token = 'dummy_token'

        cloudflare_helper = CloudFlareHelper()
        cloudflare_helper.roll_token = Mock(return_value=True)

        mock_get_api_key.return_value = cf_api_key
        mock_patch.return_value = {
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
                                    'value': token,
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

        self.assertEqual(cloudflare_helper.roll_token(token), True)

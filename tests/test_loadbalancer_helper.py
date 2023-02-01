""" Tests for loadbalancer helper. """

import datetime
import sys
import unittest
from unittest.mock import patch

sys.path.append('.')

from loadbalancer_helper import LoadBalancerHelper


class LoadBalancerHelperTestCase(unittest.TestCase):
    """ Tests for loadbalancer helper. """

    # Patch the modify_rule method
    @patch("loadbalancer_helper.LoadBalancerHelper.modify_rule")
    def test_modify_rule(self, mock_modify_rule):
        """ Test for the modify_rule function. """

        loadbalancer_helper = LoadBalancerHelper()
        token = 'dummy_token'
        mock_modify_rule.return_value = {
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
                                    'value': token,
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
        response = loadbalancer_helper.modify_rule(token)
        result = response['result']
        self.assertEqual(
            result['rules'],
            [
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
                                'value': token,
                            }
                        }
                    },
                }
            ],
        )
        assert mock_modify_rule.called

"""Module is to make an API call to roll the cloudflare WAF token in the HTTP Request Header Modification rule"""

import requests
import boto3
from botocore.exceptions import ClientError

CF_ZONE_ID = "72bab892f6318efaa9451b6fa18b9a26"
CF_RULSET_ID = "c3032c1ce882457eabf5a92822ff910d"
CF_RULE_ID = "fa091ae69f304775a1f5fee1e20b4a55"


class CloudflareHelper:
    """Cloudflare WAF token refresher class"""

    # roll cloudflare token secret
    def roll_token(self, token):
        """Roll token method"""

        # Get the cloudflare API key to access cloudflare
        cf_api_key = self.get_api_key()

        # Modify Token for Http Request Header
        try:
            response = requests.patch(
                f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/rulesets/{CF_RULSET_ID}/rules/{CF_RULE_ID}",
                headers={
                    "Authorization": f"Bearer {cf_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "action": "rewrite",
                    "expression": '(http.host ne "1")',
                    "description": "X-ALB-SECRET",
                    "enabled": True,
                    "action_parameters": {
                        "headers": {
                            "X-ALB-SECRET": {"operation": "set", "value": token}
                        }
                    },
                },
                timeout=10,
            )
            return response
        except Exception as error:
            return error

    # get cloudflare api key for access
    def get_api_key(self):
        """Method to get the API Key."""

        secret_name = "nzh-cf-access-token-to-modify-transform-rules"
        region_name = "ap-southeast-2"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        except ClientError as error:
            raise error

        # Decrypts secret using the associated KMS key
        secret = get_secret_value_response["SecretString"]

        return secret

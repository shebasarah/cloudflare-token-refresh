"""Module to modify the ELB Listener Rule"""

import boto3
from botocore.exceptions import ClientError


class LoadbalancerHelper:
    """Class to modify token in elb listener rule"""

    def modify_rule(self, token):
        """Method to modify listener rule"""

        region_name = "ap-southeast-2"

        # Create secret manager client
        session = boto3.session.Session()
        client = session.client(service_name="elbv2", region_name=region_name)
        try:
            response = client.modify_rule(
                RuleArn="arn:aws:elasticloadbalancing:ap-southeast-2:177970211836:listener-rule/app/sheba-loadbalancer/38a97bd60a7d8892/44531f4d8ead8087/526eb7337545c69d",
                Conditions=[
                    {
                        "Field": "http-header",
                        "HttpHeaderConfig": {
                            "HttpHeaderName": "X-ALB-SECRET",
                            "Values": token,
                        },
                    },
                    {
                        "Field": "path-pattern",
                        "PathPatternConfig": {"Values": ["embeds/*", "static/*"]},
                    },
                    {
                        "Field": "host-header",
                        "HostHeaderConfig": {
                            "Values": [
                                "sandbox-authoringtools.nzherald.co.nz",
                            ]
                        },
                    },
                ],
            )
            # print(response)
            return response
        except ClientError as error:
            raise error

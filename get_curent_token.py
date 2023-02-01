import boto3
from botocore.exceptions import ClientError

"""Save Token to Secret Manager Class"""


class GetToken:
    def get_token():

        secret_name = "cf-alb-token"
        region_name = "ap-southeast-2"
        """ Create a Secrets Manager client"""
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)
        try:
            response = client.get_secret_value(
                SecretId=secret_name, VersionStage="AWSCURRENT"
            )
            return response["SecretString"]
        except ClientError as e:
            raise e

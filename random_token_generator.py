import random
import string
import boto3
from botocore.exceptions import ClientError
import os

"""Random token generator class"""


class RandomTokenGenerator:
    def generate_random_token(self):

        region_name = "ap-southeast-2"
        exclude_characters = (
            os.environ["EXCLUDE_CHARACTERS"]
            if "EXCLUDE_CHARACTERS" in os.environ
            else "/@\"'\\"
        )

        # return "".join(random.choice(string.hexdigits) for _ in range(30))
        """ Create a Secrets Manager client"""
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)
        try:
            response = client.get_random_password(
                ExcludePunctuation=True, PasswordLength=32
            )
            return response["RandomPassword"]
        except ClientError as e:
            raise e

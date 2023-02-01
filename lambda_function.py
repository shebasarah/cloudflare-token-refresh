""" Module for Lambda handler for secret rotation. """

import boto3

from cloudflare_helper import CloudflareHelper
from loadbalancer_helper import LoadbalancerHelper


def lambda_handler(event, context):
    """Lambda handler function."""

    arn = event["SecretId"]
    token = event["ClientRequestToken"]
    step = event["Step"]

    # Setup the client
    service_client = boto3.client("secretsmanager")

    # Make sure the version is staged correctly
    metadata = service_client.describe_secret(SecretId=arn)
    if not metadata["RotationEnabled"]:
        raise ValueError(f"Secret {arn} is not enabled for rotation")

    if step == "createSecret":
        create_secret(service_client, arn, token)

    elif step == "setSecret":
        set_secret(service_client, arn, token)

    elif step == "testSecret":
        test_secret(service_client, arn, token)

    elif step == "finishSecret":
        finish_secret(service_client, arn, token)

    else:
        raise ValueError("Invalid step parameter")


def create_secret(service_client, arn, token):
    """Function to create a new secret."""

    # There are three version stages for a secret: AWSPREVIOUS, AWSCURRENT, AWSPENDING.
    # When a new secret is generated, it is in the AWSPENDING stage untill the version stage is updated.
    # If a secret with AWSPENDING stage exists, get that secret, else generate a new secret value.
    try:
        service_client.get_secret_value(
            SecretId=arn, VersionId=token, VersionStage="AWSPENDING"
        )
    except service_client.exceptions.ResourceNotFoundException:
        # Generate a new token
        new_token = service_client.get_random_password(
            ExcludePunctuation=True, PasswordLength=32
        )
        # Put the secret
        service_client.put_secret_value(
            SecretId=arn,
            ClientRequestToken=token,
            SecretString=new_token["RandomPassword"],
            VersionStages=["AWSPENDING"],
        )


def set_secret(service_client, arn, token):
    """Set the new token in cloudflare and application load balancer."""

    # Retrieve the old secret
    old_token = service_client.get_secret_value(SecretId=arn, VersionStage="AWSCURRENT")
    # Retrieve the new secret
    new_token = service_client.get_secret_value(SecretId=arn, VersionStage="AWSPENDING")

    # Modify the token in the listener rule
    print("Modifying ELB listener rule with two token values...")
    modify_listener = LoadbalancerHelper()
    response = modify_listener.modify_rule(
        [old_token['SecretString'], new_token['SecretString']]
    )
    # print(response)
    result = response['ResponseMetadata']
    print(result['HTTPStatusCode'])

    if result['HTTPStatusCode'] == 200:
        # Change token in cloudflare
        print("Rotating the token in cloudflare...")
        token_refresh = CloudflareHelper()
        response = token_refresh.roll_token(new_token["SecretString"])
        result = response.json()
        print(result["success"])

        if result["success"] == True:
            # Updating listener rule and removing the old token
            print("Updating the ELB listener rule with only the new token...")
            modify_listener = LoadbalancerHelper()
            response = modify_listener.modify_rule([new_token["SecretString"]])
            response = response["ResponseMetadata"]
            print(response["HTTPStatusCode"])

        else:
            print("Rotation failed at Cloudflare!")

    else:
        print("Rotation failed!")


def test_secret(service_client, arn, token):
    """Method to test the new token."""

    print("No need to test against any service.")


def finish_secret(service_client, arn, token):
    """Method to set the Version stage of the new token."""

    # First describe the secret to get the current version
    metadata = service_client.describe_secret(SecretId=arn)

    # Response sample of service_client.describe_secret(SecretId=arn): {
    #     'ARN': 'SECRET-ARN','Name': 'SECRET-NAME','Description': 'SECRET-DESCRIPTION','RotationEnabled': True|False,'RotationLambdaARN': 'LAMBDA-ARN',
    #     'RotationRules': { 'AutomaticallyAfterDays': 1,'ScheduleExpression': 'rate(4 hours)'},
    #     'VersionIdsToStages': { 'old-secret-versionid': ['AWSCURRENT','AWSPREVIOUS'],'new-secret-versionid': ['AWSPENDING'] },}
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The new secret version is already marked as AWSCURRENT, return
                return

            # Finalize by staging the new secret version to AWSCURRENT.
            service_client.update_secret_version_stage(
                SecretId=arn,
                VersionStage="AWSCURRENT",
                MoveToVersionId=token,
                RemoveFromVersionId=version,
            )

            break

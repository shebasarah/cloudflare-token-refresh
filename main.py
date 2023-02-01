from cloudflare_helper import CloudflareHelper
from get_curent_token import GetToken
from loadbalancer_helper import LoadbalancerHelper
from random_token_generator import RandomTokenGenerator
from store_token_SM import SaveToken

"""Rotate token in secret manager, modify token in Http Request Header in Cloudflare and load balancer listener rule"""

if __name__ == "__main__":
    """Get Current token and save it in a variable"""
    old_token = "oldtoken"
    new_token = "newtoken"
    current_token = "current_token"

    print("Retrieving the current token...")
    old_token = GetToken.get_token()
    # print(old_token)

    """Create new token"""
    print("Generating a new token...")
    random_token_generator = RandomTokenGenerator()
    new_token = random_token_generator.generate_random_token()
    # print(f"The new token is {new_token}")
    print(
        "-----------------------------------------------------------------------------------------------------------------------------------------------------------"
    )
    """"Rotate token in secret manager"""
    print("Rotating the new token in to the secret manager...")
    save_token = SaveToken()
    save_token_response = save_token.save_token(new_token)
    # print(save_token_response)
    print(
        "-----------------------------------------------------------------------------------------------------------------------------------------------------------"
    )
    """Change token in cloudflare"""
    print("Rotating the token in cloudflare...")
    token_refresh = CloudflareHelper()
    response = token_refresh.roll_token(new_token)
    result = response.json()
    print(result["success"])
    print(
        "-----------------------------------------------------------------------------------------------------------------------------------------------------------"
    )
    """Modify the token in the listener rule"""
    print("Modifying ELB listener rule with two token values...")
    modify_listener = LoadbalancerHelper()
    response = modify_listener.modify_rule([old_token, new_token])
    response = response['ResponseMetadata']
    print(response['HTTPStatusCode'])
    print(
        "-----------------------------------------------------------------------------------------------------------------------------------------------------------"
    )
    """Retrieve the new token from the secret manager"""
    print("Retrieving new token from secret manager...")
    current_token = GetToken.get_token()
    # print(current_token)
    print(
        "-----------------------------------------------------------------------------------------------------------------------------------------------------------"
    )

    """Updating listener rule and removing the old token"""
    print("Updating the ELB listener rule with only the new token...")
    response = modify_listener.modify_rule([current_token])
    # print(response)
    response = response["ResponseMetadata"]
    print(response["HTTPStatusCode"])
    print(
        "-----------------------------------------------------------------------------------------------------------------------------------------------------------"
    )

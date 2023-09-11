import json
import boto3
import os
import datetime
# import requests
table = boto3.resource('dynamodb').Table(os.getenv('TableName'))

def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    user_id = "0"+event['requestContext']['authorizer']['claims']['sub']
    print(f'User ID (sub claim): {user_id}')
    item = {
        "user_id": user_id,
        "various_id": user_id,
        "username": event['requestContext']['authorizer']['claims']['cognito:username'],
        "is_guest": False,
        "base_table": "0",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    }
    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"hello: {user_id}",
            # "location": ip.text.replace("\n", "")
        }),
    }

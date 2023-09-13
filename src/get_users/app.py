import json
import boto3
import os
# import requests
# dynamodb_client = boto3.client(os.getenv('TableName'))
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
    try:
        user_ids = event["multiValueQueryStringParameters"]["user_ids"]
    except KeyError:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "query parameters is invalid",
            }),
        }
    res = []
    for user_id in user_ids:
        res.append(table.get_item(Key={
            "user_id": user_id,
            "various_id": user_id,
            })["Item"])
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_infos": res,
        }),
    }

import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
import datetime
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
        user_id = "0"+event['requestContext']['authorizer']['claims']['sub']
    except KeyError:
        return {
            "statusCode": 401,
            "body": json.dumps({
                "message": "unoriginated user",
            }),
        }
    res = table.query(
        IndexName="base_table",  # LSIを使用する場合、この行を追加
        KeyConditionExpression=Key('user_id').eq(user_id) & Key('base_table').eq('1'),
        FilterExpression=Key('status').eq("pending"),
        ProjectionExpression="various_id",
    )["Items"]
    friend_ids = [x["various_id"] for x in res]
    return {
        "statusCode": 200,
        "body": json.dumps({
            "friend_ids": friend_ids,
        }),
    }

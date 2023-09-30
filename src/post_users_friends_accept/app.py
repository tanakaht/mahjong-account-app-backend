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
    try:
        user_id = "0"+event['requestContext']['authorizer']['claims']['sub']
    except (KeyError, TypeError):
        return {
            "statusCode": 401,
            "body": json.dumps({
                "message": "unoriginated user",
            }),
        }
    try:
        friend_id = json.loads(event["body"])["friend_id"]
        action = json.loads(event["body"])["action"]
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "request body is invalid",
            }),
        }
    try:
        friend_request = table.get_item(Key={
                "user_id": user_id,
                "various_id": friend_id,
                })["Item"]
        if friend_request["base_table"] != "1" or friend_request["status"] != "pending":
            raise ValueError
    except (KeyError, TypeError, ValueError):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "message": "no friend request",
            }),
        }
    if action == "accept":
        table.put_item(Item={
            "user_id": user_id,
            "various_id": friend_id,
            "base_table": "2",
            "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "status": "accepted",
            "expire_date": (datetime.datetime.now()+datetime.timedelta(days=1000*365)).strftime('%Y-%m-%dT%H:%M:%S'),
        })
        table.put_item(Item={
            "user_id": friend_id,
            "various_id": user_id,
            "base_table": "2",
            "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "status": "accepted",
            "expire_date": (datetime.datetime.now()+datetime.timedelta(days=1000*365)).strftime('%Y-%m-%dT%H:%M:%S'),
        })
    elif action == "temporarily_accept":
        table.put_item(Item={
            "user_id": user_id,
            "various_id": friend_id,
            "base_table": "2",
            "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "status": "temporarily_accepted",
            "expire_date": (datetime.datetime.now()+datetime.timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S'),
        })
        table.put_item(Item={
            "user_id": friend_id,
            "various_id": user_id,
            "base_table": "2",
            "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "status": "temporarily_accepted",
            "expire_date": (datetime.datetime.now()+datetime.timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S'),
        })
    elif action == "deny":
        table.put_item(Item={
            "user_id": user_id,
            "various_id": friend_id,
            "base_table": "1",
            "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "status": "denied",
        })
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": f"action: {action} is invalid",
            })
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"action: {action} is processed",
        }),
    }

import json
import boto3
import os
import datetime
import uuid
table = boto3.resource('dynamodb').Table(os.getenv('TableName'))


def lambda_handler(event, context):
    # confirm userする
    try:
        user_id = "0"+event['requestContext']['authorizer']['claims']['sub']
    except KeyError:
        return {
            "statusCode": 401,
            "body": json.dumps({
                "message": "unoriginated user",
            }),
        }
    guest_user_id = "0"+str(uuid.uuid4())
    try:
        data = json.loads(event["body"])
        guest_user_name = data["guest_user_name"]
    except (KeyError, json.JSONDecodeError):
        guest_user_name = "guest" + guest_user_id[:5]
    item = {
        "user_id": guest_user_id,
        "various_id": guest_user_id,
        "username": event['requestContext']['authorizer']['claims']['cognito:username'],
        "is_guest": True,
        "base_table": "0",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    }
    table.put_item(Item=item)

    # user_idとフレンドにする
    table.put_item(Item={
        "user_id": user_id,
        "various_id": guest_user_id,
        "base_table": "2",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "status": "accepted",
        "expire_date": (datetime.datetime.now()+datetime.timedelta(days=1000*365)).strftime('%Y-%m-%dT%H:%M:%S'),
    })
    table.put_item(Item={
        "user_id": guest_user_id,
        "various_id": user_id,
        "base_table": "2",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "status": "accepted",
        "expire_date": (datetime.datetime.now()+datetime.timedelta(days=1000*365)).strftime('%Y-%m-%dT%H:%M:%S'),
    })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "guest_user_id": guest_user_id,
            "guest_user_name": guest_user_name,
        }),
    }

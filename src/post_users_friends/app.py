import json
import boto3
import os
import datetime
# import requests
table = boto3.resource('dynamodb').Table(os.getenv('TableName'))

def get_item(table, user_id, various_id):
    return table.get_item(Key={
        "user_id": user_id,
        "various_id": various_id,
    })["Item"]



def lambda_handler(event, context):
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
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "request body is invalid",
            }),
        }
    # すでにリクエスト済み, フレンドであったらやめる
    try:
        friend_info = get_item(table, user_id, friend_id)
        if friend_info["status"]=="denied":
            pass
        elif friend_info["status"]=="temporarily_accepted" and friend_info["expire_date"]>datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'):
            pass
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "request is invalid",
                }),
            }
    except (KeyError, TypeError):
        pass

    # 相手がゲストユーザーだったら、勝手にフレンドになる
    try:
        friend_user_info = get_item(table, friend_id, friend_id)
        if friend_user_info["is_guest"]:
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
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": f"friend_request from {user_id} to {friend_id} is processed",
                }),
            }
    except (KeyError, TypeError):
        pass
    item = {
        "user_id": user_id,
        "various_id": friend_id,
        "base_table": "1",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "status": "pending"
    }
    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"friend_request from {user_id} to {friend_id} is processed",
            # "location": ip.text.replace("\n", "")
        }),
    }

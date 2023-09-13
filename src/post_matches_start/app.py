import json
import boto3
import os
import datetime
from boto3.dynamodb.conditions import Key, Attr
# import requests
table = boto3.resource('dynamodb').Table(os.getenv('TableName'))

def can_write(table, writer_user_id: str, related_user_ids: [str]) -> bool:
    res = table.query(
        IndexName="base_table",  # LSIを使用する場合、この行を追加
        KeyConditionExpression=Key('user_id').eq(writer_user_id) & Key('base_table').eq('2'),
        FilterExpression=Key('expire_date').gt(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')),
        ProjectionExpression="various_id",
    )["Items"]
    friend_ids = set([x["various_id"] for x in res])
    for related_user_id in related_user_ids:
        if related_user_id not in friend_ids:
            try:
                res = table.get_item(Key={
                    "user_id": related_user_id,
                    "various_id": related_user_id,
                })["Item"]
                if (not res["is_guest"]) and (res["user_id"] != writer_user_id):
                    return False
            except KeyError:
                return False
    return True

def get_item(table, user_id, various_id):
    return table.get_item(Key={
        "user_id": user_id,
        "various_id": various_id,
    })["Item"]

def is_exists(table, user_id, various_id):
    res = table.get_item(Key={
        "user_id": user_id,
        "various_id": various_id,
    })
    return "Item" in res

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
    try:
        data = json.loads(event["body"])
        match_id = data["match_id"]
        user_id1 = data["user_id1"]
        user_id2 = data["user_id2"]
        user_id3 = data["user_id3"]
        user_id4 = data.get("user_id4")
        rule_id = data["rule_id"]
    except KeyError:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "request body is invalid",
            }),
        }
    # 書き込んで良いか((userがユーザーがフレンド or guestユーザであるか), (match_id使ってないか), (rule_idあるか))確認
    if (not can_write(table, user_id, [i for i in [user_id1, user_id2, user_id3, user_id4] if i is not None])) or (is_exists(table, "01", match_id)) or (not is_exists(table, "03", rule_id)) or (not match_id.startswith("1")):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "message": "request is invalid",
            }),
        }

    item = {
        "user_id": "01",
        "various_id": match_id,
        "match_id": match_id,
        "base_table": "3",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "status": "playing",
        "user_id1": user_id1,
        "user_id2": user_id2,
        "user_id3": user_id3,
        "rule_id": rule_id,
        "writer_user_id": user_id,
    }
    if user_id4 is not None:
        item["user_id4"] = user_id4
    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"match: {match_id} start is processed",
        }),
    }

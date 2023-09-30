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
    except (KeyError, TypeError):
        return {
            "statusCode": 401,
            "body": json.dumps({
                "message": "unoriginated user",
            }),
        }
    try:
        data = json.loads(event["body"])
        match_id = data["match_id"]
        round_id = data["round_id"]
        round_number = data["round_number"]
        ba = data["ba"]
        end_type = data["end_type"]
        user_end_type = data["user_end_type"]
        is_reach = data["is_reach"]
        is_tenpai = data["is_tenpai"]
        start_point = data["start_point"]
        raw_point_diff = data["raw_point_diff"]
        other_point_diff = data["other_point_diff"]
        other_profit = data["other_profit"]
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "request body is invalid",
            }),
        }
    # round_idの確認
    try:
        last_round_number = table.query(
            IndexName="match_id",
            KeyConditionExpression=Key('match_id').eq(match_id) & Key('base_table').eq('5'),
            ScanIndexForward=False,
            Limit=1
        )["Items"][0]["round_number"]
    except (IndexError, KeyError, TypeError):
        last_round_number = -1
    if round_number != last_round_number+1:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "round_number is invalid",
            }),
        }
    # match_infoの取得
    try:
        match_info = get_item(table, "01", match_id)
        if match_info["status"]!="playing":
            raise KeyError
    except (KeyError, TypeError):
        return {
            "statusCode": 404,
            "body": json.dumps({
                "message": "match is not found",
            }),
        }
    rule_id = match_info["rule_id"]
    rule_info = get_item(table, "03", rule_id)
    user_ids = [match_info[f"user_id{i}"] for i in range(1, 5) if match_info[f"user_id{i}"] is not None]
    kaze = ["東", "南", "西", "北"][:len(user_ids)]
    kaze = kaze[int(ba[1])-1:]+kaze[:int(ba[1])-1]
    kaze2user_id = {kaze[i]: user_ids[i] for i in range(len(user_ids))}
    # 書き込んで良いか((userがユーザーがフレンド or guestユーザであるか), (match_id使ってないか), (rule_idあるか))確認
    if (not can_write(table, user_id, user_ids)) or (not round_id.startswith("2")):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "message": "request is invalid",
            }),
        }
    item = {
        "user_id": "02",
        "various_id": round_id,
        "match_id": match_id,
        "base_table": "5",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "round_number": round_number,
        "ba": ba,
        "end_type": end_type,
        "user_id1": kaze2user_id["東"],
        "user_id2": kaze2user_id["南"],
        "user_id3": kaze2user_id["西"],
        "rule_id": rule_id,
        "writer_user_id": user_id,
    }
    if len(user_ids)==4:
        item["user_id4"] = kaze2user_id["北"]
    table.put_item(Item=item)

    # round_participant
    end_point = [start_point[i]+raw_point_diff[i]+other_point_diff[i] for i in range(len(user_ids))]
    user_id2start_rank = {x[1]: i+1 for i, x in enumerate(sorted(enumerate(user_ids), key=lambda x: (-start_point[x[0]], x[0])))}
    user_id2end_rank = {x[1]: i+1 for i, x in enumerate(sorted(enumerate(user_ids), key=lambda x: (-end_point[x[0]], x[0])))}
    for i in range(len(user_ids)):
        item = {
            "user_id": user_ids[i],
            "various_id": round_id,
            "match_id": match_id,
            "base_table": "6",
            "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "end_type": end_type,
            "user_end_type": user_end_type[i],
            "is_reach": is_reach[i],
            "start_point": start_point[i],
            "end_point": end_point[i],
            "point_diff": raw_point_diff[i]+other_point_diff[i],
            "raw_point_diff": raw_point_diff[i],
            "other_point_diff": other_point_diff[i],
            "other_profit": other_profit[i],
            "start_rank": user_id2start_rank[user_ids[i]],
            "end_rank": user_id2end_rank[user_ids[i]],
            "pos": kaze[i],
            "rule_id": rule_id,
            "writer_user_id": user_id,
        }
        table.put_item(Item=item)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"match: {match_id} start is processed",
        }),
    }

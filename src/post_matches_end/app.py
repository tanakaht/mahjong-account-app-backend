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
    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "request body is invalid",
            }),
        }
    # match_infoの取得
    try:
        match_info = get_item(table, "01", match_id)
        if match_info["status"]!="playing":
            raise KeyError
    except KeyError:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "message": "match is not found",
            }),
        }
    rule_id = match_info["rule_id"]
    rule_info = get_item(table, "03", rule_id)
    user_ids = [match_info[f"user_id{i}"] for i in range(1, 5) if match_info.get(f"user_id{i}") is not None]
    # 書き込んで良いか((userがユーザーがフレンド or guestユーザであるか), (match_id使ってないか), (rule_idあるか))確認
    if (not can_write(table, user_id, user_ids)):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "message": "request is invalid",
            }),
        }

    # score集計
    rounds_infos = table.query(
        IndexName="match_id",
        KeyConditionExpression=Key('match_id').eq(match_id) & Key('base_table').eq('6'),
    )["Items"]
    user_id2last_round_info = {x: {} for x in user_ids}
    user_id2other_profits = {x: 0 for x in user_ids}
    for round_info in rounds_infos:
        user_id_ = round_info["user_id"]
        date = round_info["date"]
        user_id2other_profits[user_id_] += round_info["other_profit"]
        if user_id2last_round_info[user_id_].get("date", "0000-00-00")<date:
            user_id2last_round_info[user_id_] = round_info
    # matchをupdate
    item = {
        "user_id": "01",
        "various_id": match_id,
        "match_id": match_id,
        "base_table": "3",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "status": "finished",
        "user_id1": user_ids[0],
        "user_id2": user_ids[1],
        "user_id3": user_ids[2],
        "rule_id": rule_id,
        "writer_user_id": user_id,
    }
    if len(user_ids)==4:
        item["user_id4"] = user_ids[3]
    table.put_item(Item=item)

    # match_participant
    for i in range(len(user_ids)):
        raw_point = user_id2last_round_info[user_ids[i]]["end_point"]
        rank = user_id2last_round_info[user_ids[i]]["end_rank"]
        point = rule_info[f"rank_point_{rank}"]*1000+raw_point-rule_info["end_point"]
        if rule_info["start_point"]<rule_info["end_point"]:
            point += (rule_info["end_point"]-rule_info["start_point"])*(len(user_ids)-1)
        point_profit = point*rule_info["rate"]//100
        total_profit = point_profit+user_id2other_profits[user_ids[i]]
        item = {
            "user_id": user_ids[i],
            "various_id": match_id,
            "match_id": match_id,
            "base_table": "4",
            "date":  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "point": point,
            "raw_point": raw_point,
            "total_profit": total_profit,
            "point_profit": point_profit,
            "bonus_profit": user_id2other_profits[user_ids[i]],
            "rank": rank,
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

import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from collections import defaultdict
# import requests
# dynamodb_client = boto3.client(os.getenv('TableName'))
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('TableName'))

def lambda_handler(event, context):
    try:
        user_ids = event["multiValueQueryStringParameters"]["user_ids"]
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "query parameters is invalid",
            }),
        }
    match_id2user_profits = defaultdict(dict)
    match_id2date = {}
    for user_id in user_ids:
        res_match = table.query(
            IndexName="base_table",
            KeyConditionExpression=Key('user_id').eq(user_id) & Key('base_table').eq('4'),
        )["Items"]
        for match in res_match:
            match_id2user_profits[match["match_id"]][user_id] = int(match["total_profit"])
            match_id2date[match["match_id"]] = match["date"]
    res_matchinfo =  dynamodb.batch_get_item(
            RequestItems={
                os.getenv('TableName'): {
                    'Keys': [
                        {"user_id": "01",
                        "various_id": match_id}
                        for match_id in match_id2user_profits.keys()
                    ]
                }
            }
        )["Responses"][os.getenv('TableName')]
    for matchinfo in res_matchinfo:
        for i in "1234":
            if matchinfo.get(f"user_id{i}", user_ids[0]) not in user_ids:
                match_id2user_profits.pop(matchinfo["various_id"])
    scoreboard = []
    total_profits = defaultdict(int)
    for match_id in sorted(match_id2user_profits.keys(), key=lambda x: match_id2date[x]):
        match_info = []
        for user_id, profit in match_id2user_profits[match_id].items():
            match_info.append({
                "user_id": user_id,
                "profit": profit,
            })
            total_profits[user_id] += profit
        scoreboard.append(match_info)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "scoreboard": scoreboard,
            "total_profits": [{"user_id": user_id, "profit": profit} for user_id, profit in total_profits.items()],
        }),
    }

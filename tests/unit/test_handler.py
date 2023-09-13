import json

import pytest
import boto3
import os
import yaml
import copy
from moto import mock_dynamodb
import boto3
import datetime

def is_same_without_date(d1, d2) -> bool:
    d1 = copy.deepcopy(d1)
    d2 = copy.deepcopy(d2)
    try:
        d1.pop("date")
    except KeyError:
        pass
    try:
        d2.pop("date")
    except KeyError:
        pass
    return d1 == d2


@pytest.fixture(scope='function', autouse=True)
def set_env():
    """Set up AWS Credentials for moto."""
    import os
    os.environ['TableName']="test_table"

@pytest.fixture(scope='function')
def dynamodb():
    with mock_dynamodb():
        yield boto3.resource('dynamodb', region_name='ap-northeast-1')

@pytest.fixture(scope='function')
def create_table(dynamodb):
    table = dynamodb.create_table(
        TableName=os.environ['TableName'],  # テスト用のスタック名として「test-stack」を仮定しています。
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'various_id', 'AttributeType': 'S'},
            {'AttributeName': 'base_table', 'AttributeType': 'S'},
            {'AttributeName': 'match_id', 'AttributeType': 'S'},
        ],
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'various_id', 'KeyType': 'RANGE'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'match_id',
                'KeySchema': [
                    {'AttributeName': 'match_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'base_table', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                },
            },
        ],
        LocalSecondaryIndexes=[
            {
                'IndexName': 'base_table',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'base_table', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        },
    )
    table.meta.client.get_waiter('table_exists').wait(TableName=os.environ['TableName'])
    return table

@pytest.fixture(scope='function')
def base_table_0(create_table):
    # table0: users
    for i in [1, 2, 3, 4, 5]:
        create_table.put_item(Item={
            "user_id": f"0{i}{i}{i}{i}",
            "various_id": f"0{i}{i}{i}{i}",
            "username": f"user{i}",
            "is_guest": False,
            "base_table": "0",
            "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        })
    create_table.put_item(Item={
        "user_id": "03",
        "various_id": "31111",
        "base_table": "7",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "rule_name": "test",
        "n_persons": 4,
        "n_rounds": 8,
        "start_point": 25000,
        "end_point": 25000,
        "rank_point_1": 20,
        "rank_point_2": 10,
        "rank_point_3": -10,
        "rank_point_4": -20,
        "rate": 100,
        "tobishou": 0
    })
    return create_table

@pytest.fixture(scope='function')
def base_table_01(base_table_0):
    # table1: friendrequests
    base_table_0.put_item(Item={
        "user_id": "01111",
        "various_id": "02222",
        "status": "pending",
        "base_table": "1",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    })
    return base_table_0

@pytest.fixture(scope='function')
def base_table_02(base_table_0):
    for i in [1, 2, 3, 4]:
        for j in [1, 2, 3, 4]:
            if i==j:
                continue
            # table1: friendrequests
            base_table_0.put_item(Item={
                "user_id": f"0{i}{i}{i}{i}",
                "various_id": f"0{j}{j}{j}{j}",
                "base_table": "2",
                "status": "temporarily_accepted",
                "expire_date": (datetime.datetime.now()+datetime.timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S'),
                "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            })
    return base_table_0

@pytest.fixture(scope='function')
def base_table_023(base_table_02):
    # table1: friendrequests
    base_table_02.put_item(Item={
        "user_id": "01",
        "various_id": "11111",
        "match_id": "11111",
        "base_table": "3",
        "date": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "status": "playing",
        "user_id1": "01111",
        "user_id2": "02222",
        "user_id3": "03333",
        "user_id4": "04444",
        "rule_id": "31111",
        "writer_user_id": "01111",
    })
    return base_table_02

@pytest.fixture(scope='function')
def base_apigw_event():
    """ Generates API GW Event"""
    return {
        "body": '{ "test": "body"}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }

@pytest.fixture(scope='function')
def base_apigw_event_user1(base_apigw_event):
    base_apigw_event_user1 = copy.deepcopy(base_apigw_event)
    base_apigw_event_user1["requestContext"]["authorizer"] = {
        "claims": {
            "sub": "1111",
            "cognito:username": "user1",
        }
    }
    return base_apigw_event_user1

@pytest.fixture(scope='function')
def base_apigw_event_user2(base_apigw_event):
    base_apigw_event_user2 = copy.deepcopy(base_apigw_event)
    base_apigw_event_user2["requestContext"]["authorizer"] = {
        "claims": {
            "sub": "2222",
            "cognito:username": "user2",
        }
    }
    return base_apigw_event_user2


class TableWatcher:
    def __init__(self, table) -> None:
        self.table = table
        self.init_data = self.get_all_elements()

    def print_all_elements(self):
        print("------------------")
        print("all_elements")
        data = self.get_all_elements()
        for d in data:
            print(d)

    def get_all_elements(self):
        response = self.table.scan()
        data = response['Items']
        return data

    def get_data_diff(self):
        removed = []
        added = []
        changed = []
        data1_dict = {(d["user_id"], d["various_id"]):d for d in self.init_data}
        data2_dict = {(d["user_id"], d["various_id"]):d for d in self.get_all_elements()}
        for k in data1_dict.keys():
            if k not in data2_dict.keys():
                removed.append(data1_dict[k])
            elif data1_dict[k] != data2_dict[k]:
                changed.append((data1_dict[k], data2_dict[k]))
        for k in data2_dict.keys():
            if k not in data1_dict.keys():
                added.append(data2_dict[k])
        return {"removed":removed, "added":added, "changed": changed}

    def print_data_diff(self):
        res = self.get_data_diff()
        if len(res["removed"])!=0:
            print("------------------")
            print("removed")
            for d in res["removed"]:
                print(d)
        if len(res["added"])!=0:
            print("------------------")
            print("added")
            for d in res["added"]:
                print(d)
        if len(res["changed"])!=0:
            print("------------------")
            print("changed")
            for d in res["changed"]:
                print(f"before: {d[0]}")
                print(f"after: {d[1]}")
                print()


def test_post_users_confirmation(create_table, base_apigw_event, base_apigw_event_user1, base_apigw_event_user2):
    from src.post_users_confirmation.app import lambda_handler
    tablewatcher = TableWatcher(create_table)
    req1 = copy.deepcopy(base_apigw_event_user1)
    req1["httpMethod"] = "POST"
    req1["body"]= '{"device_token": "xxxxx"}'
    req2 = copy.deepcopy(base_apigw_event_user2)
    req2["httpMethod"] = "POST"
    result = lambda_handler(req1, {})
    result = lambda_handler(req2, {})
    data = json.loads(result["body"])
    # print debug
    print(result)
    tablewatcher.print_data_diff()
    # 検証
    assert result["statusCode"] == 200
    # assert "message" in result["body"]
    # assert data["message"] == "hello world"


def test_get_users(base_table_0, base_apigw_event, base_apigw_event_user1, base_apigw_event_user2):
    from src.get_users.app import lambda_handler
    tablewatcher = TableWatcher(base_table_0)
    tablewatcher.print_all_elements()
    table_data = tablewatcher.get_all_elements()
    req = copy.deepcopy(base_apigw_event)
    req["httpMethod"] = "GET"
    req["multiValueQueryStringParameters"]= {"user_ids": ["01111", "02222"]}
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    print(data)
    # 検証
    assert result["statusCode"] == 200
    assert is_same_without_date(data["user_infos"][0], table_data[0])
    assert is_same_without_date(data["user_infos"][1], table_data[1])
    # assert data["message"] == "hello world"

def test_post_users_friends(base_table_0, base_apigw_event, base_apigw_event_user1, base_apigw_event_user2):
    from src.post_users_friends.app import lambda_handler
    tablewatcher = TableWatcher(base_table_0)
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "POST"
    req["body"]= '{"friend_id": "02222"}'
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    print(result)
    tablewatcher.print_data_diff()
    # 検証
    assert result["statusCode"] == 200
    # assert "message" in result["body"]
    # assert data["message"] == "hello world"

def test_get_users_friend_request(base_table_01, base_apigw_event, base_apigw_event_user1, base_apigw_event_user2):
    from src.get_users_friend_request.app import lambda_handler
    tablewatcher = TableWatcher(base_table_01)
    tablewatcher.print_all_elements()
    table_data = tablewatcher.get_all_elements()
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "GET"
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    print(data)
    # 検証
    assert result["statusCode"] == 200
    # assert is_same_without_date(data["user_infos"][0], table_data[0])
    # assert is_same_without_date(data["user_infos"][1], table_data[1])

def test_post_users_friends_accept(base_table_01, base_apigw_event, base_apigw_event_user1, base_apigw_event_user2):
    from src.post_users_friends_accept.app import lambda_handler
    tablewatcher = TableWatcher(base_table_01)
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "POST"
    # req["body"]= {"friend_id": "02222", "action": "accept"}
    # req["body"]= {"friend_id": "02222", "action": "temporarily_accept"}
    req["body"]= '{"friend_id": "02222", "action": "deny"}'
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    print(result)
    tablewatcher.print_data_diff()
    # 検証
    assert result["statusCode"] == 200
    # assert "message" in result["body"]
    # assert data["message"] == "hello world"


def test_get_users_friends(base_table_02, base_apigw_event):
    from src.get_users_friends.app import lambda_handler
    tablewatcher = TableWatcher(base_table_02)
    # tablewatcher.print_all_elements()
    req = copy.deepcopy(base_apigw_event)
    req["httpMethod"] = "GET"
    req["queryStringParameters"] = {"user_id": "01111"}
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    # 検証
    assert result["statusCode"] == 200
    assert data["friend_ids"] == ["02222", "03333", "04444"]

    req["httpMethod"] = "GET"
    req["queryStringParameters"] = {"user_id": "02222"}
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    # 検証
    assert result["statusCode"] == 200
    assert data["friend_ids"] == ["01111", "03333", "04444"]


def test_post_matches_start(base_table_02, base_apigw_event_user1):
    from src.post_matches_start.app import lambda_handler
    tablewatcher = TableWatcher(base_table_02)
    # tablewatcher.print_all_elements()
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "POST"
    req["body"] = json.dumps({
        "match_id": "11111",
        "user_id1": "01111",
        "user_id2": "02222",
        "user_id3": "03333",
        "user_id4": "04444",
        "rule_id": "31111",
    })
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    tablewatcher.print_data_diff()
    # 検証
    assert result["statusCode"] == 200

def test_post_matches_start_invalid1(base_table_02, base_apigw_event_user1):
    from src.post_matches_start.app import lambda_handler
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "POST"
    req["body"] = json.dumps({
        "match_id": "11111",
        "user_id1": "01111",
        "user_id2": "02222",
        "user_id3": "03333",
        "user_id4": "04444",
        "rule_id": "31111",
    })
    result = lambda_handler(req, {})
    # 検証
    assert result["statusCode"] == 200
    tablewatcher = TableWatcher(base_table_02)
    # tablewatcher.print_all_elements()
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    tablewatcher.print_data_diff()
    assert result["statusCode"] == 403

def test_post_matches_start_invalid2(base_table_02, base_apigw_event_user1):
    from src.post_matches_start.app import lambda_handler
    tablewatcher = TableWatcher(base_table_02)
    # tablewatcher.print_all_elements()
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "POST"
    req["body"] = json.dumps({
        "match_id": "11111",
        "user_id1": "01111",
        "user_id2": "02222",
        "user_id3": "03333",
        "user_id4": "05555",
        "rule_id": "31111",
    })
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    tablewatcher.print_data_diff()
    # 検証
    assert result["statusCode"] == 403


def test_post_matches_round(base_table_023, base_apigw_event_user1):
    from src.post_matches_round.app import lambda_handler
    tablewatcher = TableWatcher(base_table_023)
    # tablewatcher.print_all_elements()
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "POST"
    req["body"] = json.dumps({
        "match_id": "11111",
        "round_id": "21111",
        "round_number": 0,
        "ba": "東1",
        "end_type": "和了",
        "user_end_type": ["ツモ", "他家ツモ", "他家ツモ", "他家ツモ"],
        "is_reach": [True, True, False, False],
        "is_tenpai": [True, False, False, False],
        "start_point": [25000, 25000, 25000, 25000],
        "raw_point_diff": [12000, -4000, -4000, -4000],
        "other_point_diff": [1000, -1000, 0, 0],
        "other_profit": [0, 0, 0, 0],
    })
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    tablewatcher.print_data_diff()
    # 検証
    assert result["statusCode"] == 200


def test_post_matches_end(base_table_023, base_apigw_event_user1):
    test_post_matches_round(base_table_023, base_apigw_event_user1)
    from src.post_matches_end.app import lambda_handler
    tablewatcher = TableWatcher(base_table_023)
    # tablewatcher.print_all_elements()
    req = copy.deepcopy(base_apigw_event_user1)
    req["httpMethod"] = "POST"
    req["body"] = json.dumps({
        "match_id": "11111",
    })
    result = lambda_handler(req, {})
    data = json.loads(result["body"])
    # print debug
    tablewatcher.print_data_diff()
    # 検証
    assert result["statusCode"] == 200

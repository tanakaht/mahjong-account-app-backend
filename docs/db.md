# DBについて

## 背景

元々RDSでやろうとしたが、金が面倒だなと思ってdynamoにした。元々RDBのテーブルだったがおそらく単一テーブルでいける気分になれたので、統合した。

全部書くのだるくなってるので、厄介そうなポイントだけ記載する。

## schema?

![](./imgs/db.png)
[参照](https://lucid.app/lucidchart/95de4622-68c6-4b17-9753-e70720ba22e6/edit?page=0_0&invitationId=inv_00ce94c5-9863-41e0-826f-0301c7c3873b#)

一番右が統合された最終的なテーブル。右から2行目が中間的に統合したもの。そのほかがRDBとして設計したもの

## attributes

ポイントだけ

### idについて
諸々の理由で、各種IDを区別するため、各種IDにsurfixをつける。以下の対応

- user_id: 0xxxxx
- match_id: 1xxxxx
- round_id: 2xxxxx
- rule_id: 3xxxxx

### user_id (PK)
基本は、cognitoのuser_idに先頭に0をつけたもの。必須

検索のため、以下のIDは予約

- 01: match_id の検索用特殊ID
- 02: round_id の検索用特殊ID
- 03: rule_id の検索用特殊ID

### various_id (SK)

user_id, match_id, round_id, rule_idが入る.

### base_table (LSI)

統合前のどのRDBのテーブルのものかを指定。

- 0: Users
- 1: FriendsRequests
- 2: Friends
- 3: Matches
- 4: MatchParticipants
- 5: Rounds
- 6: RoundParticipants
- 7: Rules

### match_id (GSI)

後述の検索用にGSI

### date

LSIになってないけどいいのか?


## apiでの叩き方

こんな感じだからいけるべと思ったらしい。

- 対局開始
    - matches, matchParticipantsに足すだけ
- 対局終了
    - matches, matchParticipantsにupdate by match_id
- 対局削除
    - match_idで削除
- round登録
    - OK
- round削除
    - match_idで検索→user_id1,2,3,4取得→round_numberで削除
- 対局再開
    - user_id, match_idで検索
- 戦績取得(個人)
    - user_idで検索→処理
- 収支計算
    - MatchParticipantsでuser_idで検索, timestampでfilter→(matchesでmatch_idで検索→filterつくる)→filter

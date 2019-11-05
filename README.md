技適DB検索ツール
================

- 諸事情により対象を 920MHz 帯に固定している。
- 変えるには REC=02-08-00-00 を適当に書き換える。
- 技術基準適合証明等を受けた機器の検索 Web-API のコード値一覧を参照。
- SSLの Warningを出さないようにするには[後述](#warning-を止める)の環境変数を設定する。

## 件数の取得

```
% get_records.py --date-from 20130101 --date-to 20130120
size=34
```

## 登録情報の取得

出力ファイルを指定しないと標準出力に表示する。

```
% get_records.py --date-from 20121226 --date-to 20121226 --retrieve 
[
  {
    "gitekiInfo": {
      "attachmentFileKey": "",
      "name": "アイ・ティー・シーネットワーク株式会社",
      "organName": "ＳＧＳジャパン(株)",
      "attachmentFileCntForCd2": "",
      "attachmentFileCntForCd1": "",
      "spuriousRules": "新スプリアス規定",
      "date": "2012-12-26",
      "attachmentFileName": "",
      "number": "006ＹＹＡ0000058〜006ＹＹＡ0000065",
      "radioEquipmentCode": "第２条第８号に規定する特定無線設備",
      "bodySar": "—",
      "elecWave": "Ｆ１Ｄ\\n922.5〜927.9ＭＨz(200kＨz間隔28波)　0.02Ｗ",
      "note": "",
      "typeName": "920ＭＨz　汎用モジュールＡＭ",
      "techCode": "登録証明機関による技術基準適合証明",
      "no": "1"
    }
  }
]
```

下記コマンドは、60秒ごとに500件づつ920MHzを全件持ってくる。
2019年10月11日時点で 22809件あった。

```
% get_records.py result-920-20191011.db --retrieve
```

## get_records.py で保存したファイルを読み込む。

- 全体の統計など

    reader.py result-920-20191011.db  -v

- 特定の組織の情報だけを読む。

    reader.py result-920-20191011.db --name '大崎電気'

## Usage

- get_records

```
usage: get_records.py [-h] [--date-from DATE_FROM] [--date-to DATE_TO]
                      [--interval INTERVAL] [--dc {4,5,6,7}] [--retrieve] [-v]
                      [db_file]

retriving the records in the giteki database.

positional arguments:
  db_file               database in JSON. (default: None)

optional arguments:
  -h, --help            show this help message and exit
  --date-from DATE_FROM
                        specify a datetime of the start date > 19260101
                        (default: None)
  --date-to DATE_TO     specify a datetime of the end date < 21001231
                        (default: None)
  --interval INTERVAL   specify an interval in seconds to wait for the next
                        retrieving. (default: 60)
  --dc {4,5,6,7}        specify an index number for the chunk size.
                        DC:chunk_size = {4: 50, 5: 100, 6: 500, 7: 1000}
                        (default: 6)
  --retrieve            specify to retrieve the records. (default: False)
  -v                    enable verbose mode. (default: False)
```

- reader.py

```
usage: reader.py [-h] [--name NAME] [--date-from DATE_FROM]
                 [--date-to DATE_TO] [--max-tx-power MAX_TX_POWER]
                 [--min-tx-power MIN_TX_POWER] [--ch-width CH_WIDTH]
                 [--specific-ch-width] [--show-others] [-v] [--show-stat]
                 db_file

a reader of the response from GITEKI db.

positional arguments:
  db_file               database in JSON.

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           specify a vendor name. (default: None)
  --date-from DATE_FROM
                        specify a datetime of the start date (default:
                        19700101)
  --date-to DATE_TO     specify a datetime of the end date (default: 29990101)
  --max-tx-power MAX_TX_POWER
                        specify the maximum Tx power, includes the number
                        (default: 20.0)
  --min-tx-power MIN_TX_POWER
                        specify the minimum Tx power, not includes the number
                        (default: 1.0)
  --ch-width CH_WIDTH   specify a channel width interested. (default: None)
  --specific-ch-width   specify that the channel width specified only be
                        taken. (default: False)
  --show-others         enable to show other recoreds. (default: False)
  -v                    enable verbose mode. (default: False)
  --show-stat           specify to show the statistics. (default: False)
```

## warning を止める

```
/Users/sakane/.pyenv/versions/3.7.2/lib/python3.7/site-packages/urllib3/connectionpool.py:847: InsecureRequestWarning: Unverified HTTPS request is being made. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings InsecureRequestWarning)
```

```
export PYTHONWARNINGS="ignore:Unverified HTTPS request"
```


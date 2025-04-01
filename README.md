# 研究用リポジトリ

## 作成者

野口朋弥

## 作成期間

2023 年 7 月 ～ 2024 年 3 月

## ディレクトリ構成

```sh
├─ output #各分析結果
│  ├─ pattern_sample.json #パターン候補の生成結果
│  └─ rq2_sample.png #rq2の結果
└─ src #全体プログラム
   ├─ abstractor #抽象化処理
   ├─ cleaner #データ整形
   ├─ constants #パス関連
   ├─ developer #プロジェクト内に参加する開発者分析用
   ├─ diff #ファイル単位でdiff取得
   ├─ fetch #github,opendevからのfetch処理
   ├─ gumtree #構文解析を行うgumtreeを使った処理
   ├─ models #dataclassの型定義
   ├─ pattern #パターン候補の生成
   ├─ rq1 #rq1分析用
   └─ rq2 #rq2分析用
```
## 再現手順

研究結果のsampleは`outputs`下に用意しています．
実際にはローカルマシン上の`data`配下に出力されます．この時，非公開や削除されることによってデータセットが変わり，出力結果が変わる可能性があります．その場合，サーバ上にあるデータを使用することで同様の結果を得ることが可能です．

### 環境構築

pythonとpoetryとDockerに依存した方法と，Dockerのみに依存した方法があります．
前者は，プログラムの実行にpoetry，Gumtreeの実行にDockerを使用し，後者はserver上で動かせれるように，Dockerのみで起動できるようになっています．

```sh
$ docker -v
Docker version 27.4.0, build bde2b89
$ python --version
Python 3.12.1
$ poetry --version
Poetry (version 1.7.1)
```

### Poetry + Docker
```sh
# 依存ライブラリをインストール
$ poetry install

# 仮想環境の構築
$ poetry shell

# GumTreeをビルド
$ make build_gumtree
```

### Docker Only
```sh
# Dockerコンテナの立ち上げ
make up

# Dockerコンテナ内に入る
make exec
```

### コードの実行方法
```sh
# envファイルの書き換えを行い，opendevからトークンを取得してください
$ mv .env.sample .env

# データのフェッチ
$ python src/fetch/open_stack.py

# パターン候補の作成・フィルタリング
$ python src/pattern/parallel_diff.py

# パターンの出現回数の分析
$ python src/rq2/parallel_search.py
..
```

## 研究結果の出力
研究結果は以下のように出力されます
```sh
/
└─ data
   ├─ out
   │  └─ results #結果の保存
   │     └─ openstack_s10_t15
   │        ├─ 2013to2014
   │        └─ all
   │           ├─ merged_all_nova.json
   │           ├─ pre_filtered_nova.json
   │           └─ merged_all_nova.json
   └─ resources #fetchしたデータの保管
      └─ openstack
         └─ 2013to2014
            └─ nova.json
```

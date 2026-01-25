# PGroonga CNPG

このプロジェクトは、[PGroonga](https://pgroonga.github.io/) を [CloudNativePG (CNPG)](https://cloudnative-pg.io/) と統合するための Docker イメージを提供します。

## 概要

PGroonga は PostgreSQL の高速全文検索拡張です。このプロジェクトでは、CNPG の要件に合わせてカスタマイズされた Docker イメージを作成し、Kubernetes 上で PGroonga を利用できるようにします。

### 背景

groonga/pgroonga のベースイメージでは postgres ユーザーの UID が 70 ですが、CNPG は UID 26 を期待しています。そのため、Dockerfile では postgres ユーザーの UID/GID を 26 に変更しています。

## イメージ

ビルドされたイメージは [GitHub Container Registry](https://ghcr.io/soli0222/pgroonga-cnpg) で公開されています。

- `ghcr.io/soli0222/pgroonga-cnpg:4.0.5-alpine-18`

## 使用方法

### CNPG クラスタの作成

`cluster.yaml` を使用して CNPG クラスタを作成します。

```bash
kubectl apply -f cluster.yaml
```

### イメージのビルド

ローカルでイメージをビルドするには：

```bash
docker build -t pgroonga-cnpg .
```

## ファイル構成

- `Dockerfile`: CNPG 互換の PGroonga イメージをビルドするためのファイル
- `cluster.yaml`: CNPG クラスタのサンプル設定
- `renovate.json5`: 依存関係更新の自動化設定

## 貢献

プルリクエストやイシューを歓迎します。変更を提案する前に、既存のイシューを確認してください。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
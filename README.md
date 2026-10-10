# PGroonga CNPG

このプロジェクトは、[PGroonga](https://pgroonga.github.io/) を [CloudNativePG (CNPG)](https://cloudnative-pg.io/) と統合するための Docker イメージを提供します。

## 概要

PGroonga は PostgreSQL の高速全文検索拡張です。このプロジェクトでは、CNPG の要件に合わせてカスタマイズされた Docker イメージを作成し、Kubernetes 上で PGroonga を利用できるようにします。

### 背景

groonga/pgroonga のベースイメージでは postgres ユーザーの UID が 70 ですが、CNPG は UID 26 を期待しています。そのため、Dockerfile では postgres ユーザーの UID/GID を 26 に変更しています。

## イメージ

ビルドされたイメージは [GitHub Container Registry](https://ghcr.io/soli0222/pgroonga-cnpg) で公開されています。

<!-- release-image:start -->
- `ghcr.io/soli0222/pgroonga-cnpg/4.1.0-alpine:18`
<!-- release-image:end -->

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

## リリースとテスト

Dockerfileのベースイメージのタグをバージョンの正本にしています。
RenovateのPGroonga更新PRは、amd64・arm64のCNPG E2Eが成功すると自動マージされます。
mainでは、未公開のバージョンについて次を実行します。

1. 各アーキテクチャでイメージをビルドし、kind上のCNPGで検証する。
2. 検証したイメージをGHCRに公開し、マルチアーキテクチャのタグを作成する。
3. READMEのイメージ名、`cluster.yaml`、`CHANGELOG.md`を更新する。
4. `X.Y.Z-alpine-PG_MAJOR`タグとGitHub Releaseを作成する。

既存Releaseがある場合はテストのみ実行し、イメージを上書きしません。
失敗したリリースはActionsの「Test and release」をmainに対して手動実行すると再試行できます。
テスト中にmainが進んだ場合も、新しいmainに対して再実行します。
バージョンを記載するファイルを増やす場合は、`scripts/release.py`の更新対象に追加してください。

E2Eでは1インスタンスのCNPGクラスタのReady、UID/GID 26、PostgreSQLとPGroongaのバージョン、
PGroongaインデックスを使った日本語全文検索を確認します。
kind・CNPG・Kubernetesノードイメージのバージョンは`tests/e2e.env`で管理しています。
Renovateが安定版の更新をまとめてPRにし、両アーキテクチャのE2E成功後に自動マージします。
ノードイメージのdigestも更新対象です。E2E依存関係のみの更新では新しいリリースを作りません。
ローカルではDocker・kubectlと、`tests/e2e.env`と同じバージョンのkindが必要です。
テスト専用クラスタは終了時に削除されます。

```bash
tag=$(python3 scripts/release.py metadata | sed -n 's/^tag=//p')
version=${tag%%-alpine-*}
pg_major=${tag##*-}
docker build -t "pgroonga-cnpg-test:$pg_major" .
bash tests/cnpg-e2e.sh "pgroonga-cnpg-test:$pg_major" "$version" "$pg_major"
```

## ファイル構成

- `Dockerfile`: CNPG 互換の PGroonga イメージをビルドするためのファイル
- `cluster.yaml`: CNPG クラスタのサンプル設定
- `renovate.json5`: 依存関係更新の自動化設定

## 貢献

プルリクエストやイシューを歓迎します。変更を提案する前に、既存のイシューを確認してください。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

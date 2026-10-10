#!/usr/bin/env python3
"""Derive release metadata and synchronize examples from Dockerfile."""
import argparse
import os
from pathlib import Path
import re


def metadata():
    match = re.search(
        r"^FROM groonga/pgroonga:(\d+\.\d+\.\d+)-alpine-(\d+)(?:@sha256:[a-f0-9]+)?$",
        Path("Dockerfile").read_text(), re.MULTILINE,
    )
    if not match:
        raise SystemExit("Expected groonga/pgroonga:X.Y.Z-alpine-PG_MAJOR in Dockerfile")
    version, pg_major = match.groups()
    repository = os.environ.get("GITHUB_REPOSITORY", "Soli0222/pgroonga-cnpg").lower()
    return {
        "version": version,
        "pg_major": pg_major,
        "tag": f"{version}-alpine-{pg_major}",
        "image": f"ghcr.io/{repository}/{version}-alpine:{pg_major}",
    }


def notes(data):
    return (
        f"PGroonga {data['version']} / Alpine / PostgreSQL {data['pg_major']}\n\n"
        f"- イメージ: `{data['image']}`\n"
        "- 対応アーキテクチャ: `linux/amd64`, `linux/arm64`\n"
        "- postgres UID/GID: `26:26`\n"
        "- 各アーキテクチャでCNPGの起動・PGroonga拡張・日本語全文検索を検証。\n"
    )


def sync(data):
    readme = Path("README.md")
    text, count = re.subn(
        r"<!-- release-image:start -->.*?<!-- release-image:end -->",
        f"<!-- release-image:start -->\n- `{data['image']}`\n<!-- release-image:end -->",
        readme.read_text(), flags=re.DOTALL,
    )
    if count != 1:
        raise SystemExit("README must contain one release-image marker pair")
    readme.write_text(text)
    cluster = Path("cluster.yaml")
    text, count = re.subn(r"(?m)^  imageName: .+$", f"  imageName: {data['image']}", cluster.read_text())
    if count != 1:
        raise SystemExit("cluster.yaml must contain one imageName")
    cluster.write_text(text)
    changelog = Path("CHANGELOG.md")
    text = changelog.read_text() if changelog.exists() else "# Changelog\n\n"
    heading = f"## {data['tag']}"
    if heading not in text.splitlines():
        prefix = "# Changelog\n\n"
        if not text.startswith(prefix):
            raise SystemExit("Unexpected CHANGELOG heading")
        changelog.write_text(prefix + heading + "\n\n" + notes(data) + "\n" + text[len(prefix):])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["metadata", "sync", "notes"])
    args = parser.parse_args()
    data = metadata()
    if args.command == "sync":
        sync(data)
    elif args.command == "notes":
        print(notes(data), end="")
    else:
        for key, value in data.items():
            print(f"{key}={value}")

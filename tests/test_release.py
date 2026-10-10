import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release", ROOT / "scripts/release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        for name in ["README.md", "cluster.yaml", "CHANGELOG.md"]:
            Path(name).write_text((ROOT / name).read_text())
        Path("Dockerfile").write_text("FROM groonga/pgroonga:4.1.1-alpine-18\n")
        self.environment = patch.dict(os.environ, {"GITHUB_REPOSITORY": "Soli0222/pgroonga-cnpg"})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        os.chdir(self.previous)
        self.temp.cleanup()

    def test_sync_new_release_is_idempotent(self):
        data = release.metadata()
        release.sync(data)
        names = ["README.md", "cluster.yaml", "CHANGELOG.md"]
        first = {name: Path(name).read_text() for name in names}
        release.sync(data)
        self.assertEqual(first, {name: Path(name).read_text() for name in names})
        for name in names:
            self.assertIn(data["image"], first[name])
        self.assertEqual(first["CHANGELOG.md"].count("## 4.1.1-alpine-18"), 1)
        self.assertIn("## 4.1.0-alpine-18", first["CHANGELOG.md"])

    def test_postgres_major_and_digest(self):
        Path("Dockerfile").write_text("FROM groonga/pgroonga:4.2.0-alpine-19@sha256:" + "a" * 64 + "\n")
        data = release.metadata()
        self.assertEqual(data["tag"], "4.2.0-alpine-19")
        self.assertTrue(data["image"].endswith("/4.2.0-alpine:19"))

    def test_invalid_base_image_fails(self):
        Path("Dockerfile").write_text("FROM groonga/pgroonga:latest\n")
        with self.assertRaises(SystemExit):
            release.metadata()

    def test_missing_readme_marker_fails(self):
        Path("README.md").write_text("missing marker\n")
        with self.assertRaises(SystemExit):
            release.sync(release.metadata())


if __name__ == "__main__":
    unittest.main()

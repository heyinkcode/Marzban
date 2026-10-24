import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def test_image_startup_stops_when_migration_fails(self):
        cmd = next(line[4:] for line in (ROOT / "Dockerfile").read_text().splitlines()
                   if line.startswith("CMD "))
        self.assertEqual(json.loads(cmd), ["bash", "-c", "alembic upgrade head && exec python main.py"])

    def test_real_alembic_cli_preserves_existing_data_and_guards_downgrade(self):
        spec = importlib.util.spec_from_file_location("release_verify", ROOT / "tools/verify_usage_continuity_release.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.verify(os.environ.get("MR_SHAW_RELAY_TEST_XRAY"))["migration"], "passed")

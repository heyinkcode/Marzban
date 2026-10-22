"""Distribution namespace guards; upstream credit and historical evidence stay intact."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RepositoryNamespaceTests(unittest.TestCase):
    def test_active_distribution_uses_current_owner(self):
        for relative in ("Dockerfile", "docker-compose.yml", ".github/workflows/build.yml", "README.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("heyinkcode", text, relative)
            self.assertNotIn("github.com/kissow", text, relative)
            self.assertNotIn("githubusercontent.com/kissow", text, relative)
            self.assertNotIn("ghcr.io/kissow/", text, relative)

    def test_core_and_upstream_attribution_are_preserved(self):
        self.assertIn("ARG XRAY_CORE_VERSION=v26.3.27", (ROOT / "Dockerfile").read_text())
        self.assertIn("Gozargah", (ROOT / "README.md").read_text(encoding="utf-8"))

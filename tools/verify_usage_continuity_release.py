"""Exercise the real Alembic CLI on synthetic SQLite data, never a live DB."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OLD_HEAD = "b234cd56ef78"
NEW_HEAD = "c345de67fa89"


def verify(xray=None):
    with tempfile.TemporaryDirectory(prefix="continuity-migration-") as temp:
        work = Path(temp)
        env = os.environ.copy()
        env.update(SQLALCHEMY_DATABASE_URL="sqlite:///" + str(work / "ledger.db"),
                   PYTHONPATH=str(ROOT), XRAY_JSON=str(ROOT / "xray_config.json"),
                   TELEGRAM_API_TOKEN="", TELEGRAM_PROXY_URL="")
        if xray:
            env["XRAY_EXECUTABLE_PATH"] = str(Path(xray).resolve())
            version = subprocess.run([env["XRAY_EXECUTABLE_PATH"], "version"],
                                     check=True, capture_output=True, text=True, timeout=15)
            if "Xray 26.3.27" not in version.stdout:
                raise RuntimeError("Expected pinned Xray 26.3.27")
        else:
            # Only unit-test imports need a version executable. CI container
            # smoke always supplies the actual pinned binary with --xray.
            (work / "version").write_text("print('Xray 26.3.27')\n", encoding="utf-8")
            env["XRAY_EXECUTABLE_PATH"] = sys.executable
        ini = work / "alembic.ini"
        ini.write_text((ROOT / "alembic.ini").read_text(encoding="utf-8").replace(
            "script_location = app/db/migrations",
            "script_location = " + Path(os.path.relpath(ROOT / "app/db/migrations", work)).as_posix()),
            encoding="utf-8")

        def migrate(*args, success=True):
            result = subprocess.run([sys.executable, "-B", "-m", "alembic", "-c", str(ini), *args],
                                    cwd=work, env=env, capture_output=True, text=True, timeout=90)
            if (result.returncode == 0) != success:
                raise RuntimeError("Synthetic migration failed: " + result.stdout + result.stderr)
            return result

        def snapshot(db):
            tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                      if row[0] not in ("alembic_version", "user_usage_recoveries", "sqlite_sequence")]
            return {name: sorted(db.execute('SELECT * FROM "' + name + '"').fetchall(), key=repr)
                    for name in tables}

        if os.name == "nt":
            # Upstream's historical TLS migration uses a 100-year OpenSSL
            # interval, which overflows Windows C long. Do not alter historical
            # certificate behavior for a release test: build the unchanged old
            # schema locally; Linux/container smoke runs the complete chain.
            seed = subprocess.run([sys.executable, "-B", "-c",
                "from app.db.base import Base,engine; "
                "Base.metadata.create_all(engine,tables=[t for t in Base.metadata.sorted_tables "
                "if t.name != 'user_usage_recoveries']); engine.dispose()"],
                cwd=work, env=env, capture_output=True, text=True, timeout=45)
            if seed.returncode:
                raise RuntimeError("Synthetic old schema setup failed: " + seed.stderr)
            migrate("stamp", OLD_HEAD)
        else:
            migrate("upgrade", OLD_HEAD)
        db = sqlite3.connect(work / "ledger.db")
        try:
            db.execute("INSERT INTO users (id, username, status, used_traffic, data_limit, expire, created_at, "
                       "data_limit_reset_strategy) VALUES (1, 'synthetic_user', 'active', 123, 10000, "
                       "2000000000, '2026-01-01 00:00:00', 'month')")
            db.execute("INSERT INTO user_usage_logs (user_id, used_traffic_at_reset, reset_at) "
                       "VALUES (1, 6000, '2026-02-01 00:00:00')")
            db.commit()
            before = snapshot(db)
            migrate("upgrade", "head")
            assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == NEW_HEAD
            assert before == snapshot(db), "Migration changed existing data"
            assert db.execute("SELECT count(*) FROM user_usage_recoveries").fetchone()[0] == 0
            migrate("upgrade", "head")
            assert before == snapshot(db), "Repeated upgrade changed data"
            migrate("downgrade", OLD_HEAD)
            assert before == snapshot(db), "Empty-audit downgrade changed data"
            migrate("upgrade", "head")
            db.execute("INSERT INTO user_usage_recoveries VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("11111111-1111-4111-8111-111111111111", 1, "synthetic_user",
                        "2026-01-01 00:00:00", 1, 6000, "a" * 64, json.dumps({"synthetic": True})))
            db.commit()
            result = migrate("downgrade", OLD_HEAD, success=False)
            assert "Applied usage recoveries exist" in result.stderr
            assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == NEW_HEAD
            assert db.execute("SELECT count(*) FROM user_usage_recoveries").fetchone()[0] == 1
            assert before == snapshot(db), "Refused downgrade changed data"
        finally:
            db.close()
    return {"migration": "passed", "data": "synthetic-only", "head": NEW_HEAD,
            "real_xray": bool(xray), "complete_historical_chain": os.name != "nt",
            "production_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xray", help="Real pinned executable, required for container smoke")
    print(json.dumps(verify(parser.parse_args().xray)))

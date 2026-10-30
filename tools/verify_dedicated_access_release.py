"""Real Alembic CLI on synthetic old SQLite data; never open a production DB."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
OLD_HEAD, NEW_HEAD = "c345de67fa89", "d456ef78ab90"


def verify(xray=None):
    with tempfile.TemporaryDirectory(prefix="dedicated-migration-") as temp:
        work = Path(temp)
        env = os.environ.copy()
        env.update(SQLALCHEMY_DATABASE_URL="sqlite:///" + str(work / "ledger.db"), PYTHONPATH=str(ROOT),
                   XRAY_JSON=str(ROOT / "xray_config.json"), TELEGRAM_API_TOKEN="", TELEGRAM_PROXY_URL="")
        if xray:
            env["XRAY_EXECUTABLE_PATH"] = str(Path(xray).resolve())
        else:
            (work / "version").write_text("print('Xray 26.3.27')\n", encoding="utf-8")
            env["XRAY_EXECUTABLE_PATH"] = sys.executable
        ini = work / "alembic.ini"
        ini.write_text((ROOT / "alembic.ini").read_text(encoding="utf-8").replace(
            "script_location = app/db/migrations", "script_location = " +
            Path(os.path.relpath(ROOT / "app/db/migrations", work)).as_posix()), encoding="utf-8")
        def migrate(*args, success=True):
            result = subprocess.run([sys.executable, "-B", "-m", "alembic", "-c", str(ini), *args],
                cwd=work, env=env, text=True, capture_output=True, timeout=90)
            if (result.returncode == 0) != success:
                raise RuntimeError("Synthetic dedicated migration failed: " + result.stdout + result.stderr)
            return result
        if os.name == "nt":
            # Historical 100-year OpenSSL TLS migration overflows Windows C
            # long. Linux CI runs the full history. Locally construct the old
            # column set, explicitly excluding all new ACL tables/columns.
            seed = '''
import sqlalchemy as sa
from app.db.base import Base, engine
import app.db.models
old = sa.MetaData()
excluded = {'nodes': {'access_mode', 'access_revision'}, 'hosts': {'node_id'}}
for table in Base.metadata.sorted_tables:
    if table.name.startswith('dedicated_node_'):
        continue
    columns = [column._copy() for column in table.columns if column.name not in excluded.get(table.name, set())]
    sa.Table(table.name, old, *columns)
old.create_all(engine)
engine.dispose()
'''
            result = subprocess.run([sys.executable, "-B", "-c", seed], cwd=work, env=env,
                                    text=True, capture_output=True, timeout=45)
            if result.returncode:
                raise RuntimeError("Synthetic old column setup failed: " + result.stderr)
            migrate("stamp", OLD_HEAD)
        else:
            migrate("upgrade", OLD_HEAD)
        with closing(sqlite3.connect(work / "ledger.db")) as db:
            db.execute("INSERT INTO nodes (id,name,address,port,api_port,status,usage_coefficient) VALUES (1,'Keep-node','node.example.invalid',62050,62051,'connected',5)")
            db.execute("INSERT INTO inbounds (id,tag) VALUES (1,'SYNTHETIC')")
            db.execute("INSERT INTO hosts (id,remark,address,inbound_tag,security) VALUES (1,'Keep-host','node.example.invalid','SYNTHETIC','inbound_default')")
            db.execute("INSERT INTO users (id,username,status,used_traffic,data_limit,expire,created_at,data_limit_reset_strategy) VALUES (1,'synthetic_user','active',123,10000,2000000000,'2026-01-01 00:00:00','no_reset')")
            db.commit()
            tables = {row[0]: [column[1] for column in db.execute('PRAGMA table_info("' + row[0] + '")')]
                      for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                      if row[0] not in {"alembic_version", "sqlite_sequence"}}
            def snapshot():
                return {table: sorted(db.execute('SELECT ' + ','.join('"' + column + '"' for column in columns)
                    + ' FROM "' + table + '"').fetchall(), key=repr) for table, columns in tables.items()}
            before = snapshot()
            migrate("upgrade", "head")
            assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == NEW_HEAD
            assert snapshot() == before, "Existing user/config/counters changed"
            assert db.execute("SELECT access_mode,access_revision FROM nodes").fetchone() == ("public", 0)
            assert db.execute("SELECT node_id FROM hosts").fetchone() == (1,)
            migrate("upgrade", "head")
            assert snapshot() == before
            migrate("downgrade", OLD_HEAD)
            assert snapshot() == before
            migrate("upgrade", "head")
            db.execute("INSERT INTO dedicated_node_operations (operation_id,payload_sha256,node_id,user_id,username,user_created_at,granted,actor,revision,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("8c75b813-9304-490c-a09a-1298a7fe1e0b", "a" * 64, 1, 1, "synthetic_user", "2026-01-01 00:00:00", 1,
                 "synthetic_admin", 1, "2026-10-30 00:00:00"))
            db.commit()
            result = migrate("downgrade", OLD_HEAD, success=False)
            assert "downgrade would expose Nodes" in result.stderr
            assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == NEW_HEAD
            assert db.execute("SELECT COUNT(*) FROM dedicated_node_operations").fetchone()[0] == 1
            assert snapshot() == before
    return {"migration": "passed", "head": NEW_HEAD, "data": "synthetic-only",
            "complete_historical_chain": os.name != "nt", "production_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xray")
    print(json.dumps(verify(parser.parse_args().xray)))

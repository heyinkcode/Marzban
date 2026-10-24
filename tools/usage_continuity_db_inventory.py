"""Run inside /code with python -B; read-only schema inventory, no app imports."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from sqlalchemy.engine import make_url


def inventory(database_url):
    url = make_url(database_url)
    result = {'database_engine': url.get_backend_name()}
    if url.get_backend_name() != 'sqlite':
        return {**result, 'check': 'unsupported_database'}
    if not url.database or url.database == ':memory:' or url.query:
        return {**result, 'check': 'unsupported_sqlite_url'}
    path = Path(url.database).resolve()
    result['sqlite_path'] = str(path)
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
            db.execute('PRAGMA query_only=ON')
            result['alembic_heads'] = [row[0] for row in db.execute('SELECT version_num FROM alembic_version')]
        result['check'] = 'ok'
    except sqlite3.Error as exc:
        # Do not echo connection strings or SQL errors containing secrets.
        result['check'] = type(exc).__name__
    return result


if __name__ == '__main__':
    from config import SQLALCHEMY_DATABASE_URL
    print(json.dumps(inventory(SQLALCHEMY_DATABASE_URL), ensure_ascii=True))

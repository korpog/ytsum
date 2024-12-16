import sqlite3
from datetime import datetime
from typing import Optional

import click
from flask import current_app, g
from flask.app import Flask


def get_db() -> sqlite3.Connection:
    """Get or create a database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e: Optional[Exception] = None) -> None:
    """Close the database connection."""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db() -> None:
    """Initialize the database with schema from schema.sql."""
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command() -> None:
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


sqlite3.register_converter(
    "timestamp",
    # type: Callable[[bytes], datetime]
    lambda v: datetime.fromisoformat(v.decode())
)


def init_app(app: Flask) -> None:
    """Initialize application with database teardown and CLI command."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

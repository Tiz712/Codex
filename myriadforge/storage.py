"""SQLite development storage; session mutations are transactional."""
from contextlib import contextmanager
from dataclasses import asdict
import json
import sqlite3
from uuid import uuid4

from myriadforge.core import DomainError, Session


def serialize(session):
    data = asdict(session)
    data['unlocked'] = sorted(session.unlocked)
    return data


class Store:
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, payload TEXT NOT NULL, version INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS concepts (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def create_session(self):
        # Fixture inventory only, not AI-generated or earned through a real game.
        session = Session(inventory={'guardian_rune': 3, 'shield_fragment': 6,
                                     'arcane_fiber': 4, 'starlight_core': 1})
        identifier = str(uuid4())
        data = serialize(session)
        with self.transaction() as db:
            db.execute('INSERT INTO sessions VALUES (?, ?, 0)', (identifier, json.dumps(data)))
        return {'id': identifier, 'version': 0, 'inventory_source': 'demo_fixture', **data}

    def _load(self, db, identifier):
        row = db.execute('SELECT payload, version FROM sessions WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise DomainError('SESSION_NOT_FOUND')
        data = json.loads(row[0])
        data['unlocked'] = set(data['unlocked'])
        return Session(**data), row[1]

    def get_session(self, identifier):
        with self.transaction() as db:
            session, version = self._load(db, identifier)
        return {'id': identifier, 'version': version, 'inventory_source': 'demo_fixture', **serialize(session)}

    def mutate(self, identifier, expected_version, *, target=None, recipe=None, request_id=None):
        with self.transaction() as db:
            session, version = self._load(db, identifier)
            retry = recipe is not None and request_id in session.requests
            if retry:
                if session.requests[request_id] != recipe:
                    raise DomainError('IDEMPOTENCY_CONFLICT')
            elif version != expected_version:
                raise DomainError('VERSION_CONFLICT')
            if recipe is not None:
                session.craft(recipe, request_id)
            else:
                session.transition(target)
            if not retry:
                version += 1
                db.execute('UPDATE sessions SET payload=?, version=? WHERE id=?',
                           (json.dumps(serialize(session)), version, identifier))
        return {'id': identifier, 'version': version, 'inventory_source': 'demo_fixture', **serialize(session)}

    def save_concept(self, data):
        identifier = str(uuid4())
        with self.transaction() as db:
            db.execute('INSERT INTO concepts VALUES (?, ?)', (identifier, json.dumps(data, ensure_ascii=False)))
        return {'id': identifier, **data}

    def get_concept(self, identifier):
        with self.transaction() as db:
            row = db.execute('SELECT payload FROM concepts WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise DomainError('CONCEPT_NOT_FOUND')
        return {'id': identifier, **json.loads(row[0])}

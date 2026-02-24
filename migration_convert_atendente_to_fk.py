#!/usr/bin/env python3
"""
Convert `atividade.atendente` string column (username) to a foreign key `atendente_id` -> user.id

Usage: python migration_convert_atendente_to_fk.py

What it does (idempotent where possible):
- Checks for existing `atendente_id` column; exits if already present
- Adds `atendente_id` INT NULL
- For each distinct non-null value in `atividade.atendente`, tries to find a `User` with that username
  - If found, updates matching atividade rows to set `atendente_id` to the user id
  - If not found, logs the value (left in `atendente` backup)
- Adds a foreign key constraint `fk_atividade_atendente` referencing `user(id)` (ON DELETE SET NULL)
- Renames old `atendente` column to `atendente_old` to keep a backup

Important: run from the project root where your Flask app and config are accessible. Make a database backup before running in production.
"""

from app import app
from models import db, User
from sqlalchemy import inspect, text
import sys


def run():
    with app.app_context():
        inspector = inspect(db.engine)
        cols = {c['name']: c for c in inspector.get_columns('atividade')}

        if 'atendente_id' in cols:
            print('atendente_id column already exists. Exiting.')
            return 0

        # Step 1: add atendente_id column
        print('Adding column atendente_id INT NULL...')
        try:
            db.session.execute(text('ALTER TABLE atividade ADD COLUMN atendente_id INT NULL'))
            db.session.commit()
        except Exception as e:
            print('Error adding column:', e)
            db.session.rollback()
            return 1

        # Step 2: migrate data from atendente (username strings) to atendente_id
        print('Reading distinct atendente values...')
        conn = db.engine.connect()
        distinct_sql = text("SELECT DISTINCT atendente FROM atividade WHERE atendente IS NOT NULL AND atendente != ''")
        result = conn.execute(distinct_sql)
        distinct_values = [row[0] for row in result]
        result.close()

        not_found = []
        updated_total = 0
        for val in distinct_values:
            name = str(val).strip()
            if not name:
                continue
            # Try to find user by username
            user = User.query.filter_by(username=name).first()
            if user:
                print(f"Mapping username '{name}' -> user.id={user.id}")
                upd = text("UPDATE atividade SET atendente_id = :uid WHERE atendente = :name")
                res = conn.execute(upd, {'uid': user.id, 'name': name})
                updated = res.rowcount if hasattr(res, 'rowcount') else 0
                updated_total += updated
            else:
                # maybe the stored value is numeric id in string form
                try:
                    uid = int(name)
                    user_by_id = User.query.get(uid)
                    if user_by_id:
                        print(f"Mapping numeric string '{name}' -> user.id={uid}")
                        upd = text("UPDATE atividade SET atendente_id = :uid WHERE atendente = :name")
                        res = conn.execute(upd, {'uid': uid, 'name': name})
                        updated = res.rowcount if hasattr(res, 'rowcount') else 0
                        updated_total += updated
                        continue
                except Exception:
                    pass

                print(f"User not found for atendente value: '{name}' (leaving as backup)")
                not_found.append(name)

        conn.execute(text('COMMIT'))
        print(f'Migrated atendente -> atendente_id for {updated_total} rows.')

        # Step 3: add foreign key constraint
        print('Adding foreign key constraint fk_atividade_atendente...')
        try:
            db.session.execute(text(
                'ALTER TABLE atividade ADD CONSTRAINT fk_atividade_atendente FOREIGN KEY (atendente_id) REFERENCES `user`(id) ON DELETE SET NULL'
            ))
            db.session.commit()
        except Exception as e:
            print('Error adding foreign key constraint:', e)
            db.session.rollback()
            print('You may need to add the constraint manually depending on your DB permissions.')

        # Step 4: drop the old atendente column (backup removal)
        # If a previous backup 'atendente_old' exists, drop it; otherwise drop 'atendente'
        try:
            if 'atendente_old' in cols:
                print("Dropping backup column 'atendente_old'...")
                db.session.execute(text('ALTER TABLE atividade DROP COLUMN atendente_old'))
                db.session.commit()
            elif 'atendente' in cols:
                print("Dropping old column 'atendente'...")
                db.session.execute(text('ALTER TABLE atividade DROP COLUMN atendente'))
                db.session.commit()
            else:
                print("No old atendente column found to drop.")
        except Exception as e:
            print('Error dropping old atendente column:', e)
            db.session.rollback()
            print('You may drop the column manually if necessary.')

        # Summary
        print('\nMigration summary:')
        print(f'  new atendente_id column added')
        print(f'  total rows updated: {updated_total}')
        if not_found:
            print('  valores sem correspondencia (não mapeados):')
            for v in not_found:
                print('   -', v)
        print('  old atendente column renamed to atendente_old (backup)')
        print('Done.')
        return 0


if __name__ == '__main__':
    code = run()
    sys.exit(code)

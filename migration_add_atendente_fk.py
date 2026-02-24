#!/usr/bin/env python3
"""
Database migration: Convert atendente column to foreign key
This migration:
1. Adds atendente_id column as foreign key to user table
2. Migrates data from old atendente column if it contains user IDs
3. Drops the old atendente column
4. Adds relationship constraint between atividade and user tables

Usage: python migration_add_atendente_fk.py
"""

from models import db
from app import app
import sys

def run_migration():
    """Run the migration"""
    with app.app_context():
        try:
            # Get connection for raw SQL if needed
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            # Check if atendente_id already exists
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'atividade' AND COLUMN_NAME = 'atendente_id'
            """)
            
            if cursor.fetchone():
                print("atendente_id column already exists. Migration may have already been run.")
                cursor.close()
                connection.close()
                return True
            
            print("Starting migration: Converting atendente to foreign key...")
            
            # Step 1: Add the new atendente_id column
            print("  1. Adding atendente_id column...")
            cursor.execute("""
                ALTER TABLE atividade 
                ADD COLUMN atendente_id INT NULL
            """)
            
            # Step 2: Migrate data - try to convert old atendente values to IDs
            # This assumes old atendente values might be numeric IDs or usernames
            print("  2. Migrating data from old atendente column...")
            cursor.execute("""
                UPDATE atividade a
                SET atendente_id = (
                    SELECT u.id FROM user u 
                    WHERE u.username = a.atendente 
                    OR CAST(a.atendente AS UNSIGNED) = u.id
                )
                WHERE atendente IS NOT NULL
            """)
            
            # Step 3: Add foreign key constraint
            print("  3. Adding foreign key constraint...")
            cursor.execute("""
                ALTER TABLE atividade 
                ADD CONSTRAINT fk_atividade_atendente 
                FOREIGN KEY (atendente_id) REFERENCES user(id) ON DELETE SET NULL
            """)
            
            # Step 4: Drop old atendente column
            print("  4. Dropping old atendente column...")
            cursor.execute("""
                ALTER TABLE atividade 
                DROP COLUMN atendente
            """)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error during migration: {str(e)}", file=sys.stderr)
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

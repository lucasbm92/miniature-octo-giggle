"""
Database migration script for Gestor de Tarefas
Usage: python migrate_db.py
"""
from models import db
from app import app

# Create all tables defined in models.py
with app.app_context():
    db.create_all()
    print("Database tables created successfully.")

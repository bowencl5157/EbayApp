#!/usr/bin/env python
"""
Database initialization script
Run this script to create all database tables
"""

from models.database import init_db
from models import Base

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database tables created successfully!")

#!/usr/bin/env python3
"""
Reset database with updated sample data
"""

from app import create_app
from app.models import db
from app.services.database_service import DatabaseService

def reset_database():
    """Reset the database with new sample data"""
    app = create_app()
    
    with app.app_context():
        print("Resetting database...")
        
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create sample data
        db_service = DatabaseService()
        db_service.create_sample_data()
        
        print("✓ Database reset completed!")
        print("Phone number 84966164 is now registered in the system")

if __name__ == "__main__":
    reset_database()

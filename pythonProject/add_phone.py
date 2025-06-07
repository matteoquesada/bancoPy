#!/usr/bin/env python3
"""
Add phone number to existing database
"""

from app import create_app
from app.models import db, SinpeSubscription

def add_phone_number():
    """Add the phone number 84966164 to the database"""
    app = create_app()
    
    with app.app_context():
        # Check if phone number already exists
        existing = SinpeSubscription.query.filter_by(sinpe_number='84966164').first()
        if existing:
            print("Phone number 84966164 already exists in database")
            return
        
        # Add the new phone number
        subscription = SinpeSubscription(
            sinpe_number='84966164',
            sinpe_bank_code='0152',
            sinpe_client_name='Test User External'
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        print("✓ Phone number 84966164 added to database")
        print("  Bank Code: 0152")
        print("  Name: Test User External")

if __name__ == "__main__":
    add_phone_number()

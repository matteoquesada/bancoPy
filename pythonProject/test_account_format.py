#!/usr/bin/env python3
"""
Test script to verify account format and SINPE functionality
"""

import requests
import json
from app.utils.iban_generator import generate_iban, validate_iban, extract_bank_code

def test_account_format():
    """Test IBAN account format generation"""
    print("=== Testing Account Format ===")
    
    # Generate 5 test accounts
    for i in range(5):
        iban = generate_iban()
        print(f"Generated IBAN {i+1}: {iban}")
        
        # Validate format
        is_valid = validate_iban(iban)
        print(f"  Valid: {is_valid}")
        
        # Extract bank code
        bank_code = extract_bank_code(iban)
        print(f"  Bank Code: {bank_code}")
        
        # Check format: CR21 + 0666 + 0001 + 12 digits
        expected_format = iban.startswith("CR21") and iban[4:8] == "0666" and iban[8:12] == "0001" and len(iban) == 22
        print(f"  Correct Format: {expected_format}")
        print()

def test_api_endpoints():
    """Test API endpoints"""
    print("=== Testing API Endpoints ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health Check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return
    
    # Test login
    try:
        login_data = {
            "username": "juan_perez",
            "password": "password123"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"Login: {response.status_code} - {response.json()}")
        
        if response.status_code == 200:
            # Get session cookie
            session_cookie = response.cookies.get('session')
            cookies = {'session': session_cookie} if session_cookie else {}
            
            # Test get user accounts
            response = requests.get(f"{base_url}/api/accounts", cookies=cookies)
            print(f"Get Accounts: {response.status_code}")
            if response.status_code == 200:
                accounts = response.json()
                print(f"User Accounts:")
                for account in accounts:
                    print(f"  - {account['number']} (Balance: {account['balance']} {account['currency']})")
                    if 'phone_link' in account and account['phone_link']:
                        print(f"    Phone: {account['phone_link']['phone']}")
            
            # Test SINPE transfer
            sinpe_data = {
                "sender_phone": "88887777",
                "receiver_phone": "88886666", 
                "amount": 1000.0,
                "description": "Test transfer"
            }
            response = requests.post(f"{base_url}/api/sinpe-movil", json=sinpe_data, cookies=cookies)
            print(f"SINPE Transfer: {response.status_code} - {response.json()}")
            
    except Exception as e:
        print(f"API Test Failed: {e}")

def test_bank_code_logic():
    """Test bank code handling logic"""
    print("=== Testing Bank Code Logic ===")
    
    # Test bank codes
    test_codes = ["0666", "666", "0152", "152"]
    
    for code in test_codes:
        # Test with leading zero removal
        clean_code = code.lstrip('0')
        # Test with leading zero addition
        full_code = f"0{clean_code}" if not code.startswith('0') else code
        
        print(f"Original: {code}")
        print(f"  Clean (BCCR): {clean_code}")
        print(f"  Full (Routing): {full_code}")
        print(f"  Is Our Bank: {clean_code == '666'}")
        print()

if __name__ == "__main__":
    print("🏦 SINPE Banking System - Account Format & Functionality Test")
    print("=" * 60)
    
    test_account_format()
    test_bank_code_logic()
    test_api_endpoints()
    
    print("=" * 60)
    print("✓ Test completed!")

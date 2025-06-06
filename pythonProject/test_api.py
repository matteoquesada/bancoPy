#!/usr/bin/env python3
"""
API Test Script for SINPE Banking System
Tests all major API endpoints
"""

import requests
import json
import time
from datetime import datetime
import uuid

BASE_URL = "http://127.0.0.1:5000/api"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get("http://127.0.0.1:5000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_users_api():
    """Test users API endpoints"""
    print("\n👥 Testing Users API...")
    
    # Get all users
    response = requests.get(f"{BASE_URL}/users")
    if response.status_code == 200:
        users = response.json()['data']
        print(f"✅ Found {len(users)} users")
        return users
    else:
        print(f"❌ Failed to get users: {response.status_code}")
        return []

def test_accounts_api():
    """Test accounts API endpoints"""
    print("\n💰 Testing Accounts API...")
    
    # Get all accounts
    response = requests.get(f"{BASE_URL}/accounts")
    if response.status_code == 200:
        accounts = response.json()['data']
        print(f"✅ Found {len(accounts)} accounts")
        return accounts
    else:
        print(f"❌ Failed to get accounts: {response.status_code}")
        return []

def test_phone_links_api():
    """Test phone links API endpoints"""
    print("\n🔗 Testing Phone Links API...")
    
    # Get all phone links
    response = requests.get(f"{BASE_URL}/phone-links")
    if response.status_code == 200:
        links = response.json()['data']
        print(f"✅ Found {len(links)} phone links")
        return links
    else:
        print(f"❌ Failed to get phone links: {response.status_code}")
        return []

def test_sinpe_validation():
    """Test SINPE phone validation"""
    print("\n📱 Testing SINPE Validation...")
    
    test_phones = ["88887777", "88886666", "99999999"]
    
    for phone in test_phones:
        response = requests.get(f"{BASE_URL}/validate/{phone}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {phone}: {data['name']} (Bank: {data['bank_code']})")
        else:
            print(f"❌ {phone}: Not registered")

def test_sinpe_user_link():
    """Test SINPE user link check"""
    print("\n🔗 Testing SINPE User Links...")
    
    test_users = ["juan_perez", "maria_rodriguez", "nonexistent_user"]
    
    for username in test_users:
        response = requests.get(f"{BASE_URL}/sinpe/user-link/{username}")
        if response.status_code == 200:
            data = response.json()
            if data['linked']:
                print(f"✅ {username}: Linked to {data['phone']} -> {data['account']}")
            else:
                print(f"⚠️  {username}: Not linked")
        else:
            print(f"❌ {username}: Error checking link")

def test_transactions_api():
    """Test transactions API endpoints"""
    print("\n📊 Testing Transactions API...")
    
    # Get all transactions
    response = requests.get(f"{BASE_URL}/transactions")
    if response.status_code == 200:
        transactions = response.json()['data']
        print(f"✅ Found {len(transactions)} transactions")
        
        if transactions:
            # Show latest transaction
            latest = transactions[0]
            print(f"   Latest: {latest['amount']} {latest['currency']} - {latest['status']}")
        
        return transactions
    else:
        print(f"❌ Failed to get transactions: {response.status_code}")
        return []

def test_sinpe_transfer():
    """Test SINPE transfer (simplified - without proper HMAC)"""
    print("\n💸 Testing SINPE Transfer...")
    
    # This is a simplified test - in production you'd need proper HMAC
    print("⚠️  Note: This test uses simplified transfer without full HMAC verification")
    
    # Test data
    transfer_data = {
        "version": "1.0",
        "timestamp": datetime.now().isoformat() + "Z",
        "transaction_id": str(uuid.uuid4()),
        "sender": {
            "phone": "88887777",
            "bank_code": "152",
            "name": "Juan Pérez"
        },
        "receiver": {
            "phone": "88886666",
            "bank_code": "152", 
            "name": "María Rodríguez"
        },
        "amount": {
            "value": 1000.00,
            "currency": "CRC"
        },
        "description": "Test transfer via API",
        "hmac_md5": "dummy_hmac_for_testing"  # This would fail HMAC verification
    }
    
    response = requests.post(f"{BASE_URL}/sinpe-movil", json=transfer_data)
    if response.status_code == 201:
        print("✅ Transfer successful")
        result = response.json()
        print(f"   Transaction ID: {result['data']['transaction_id']}")
    elif response.status_code == 403:
        print("⚠️  Transfer rejected (HMAC verification failed - expected)")
    else:
        print(f"❌ Transfer failed: {response.status_code} - {response.text}")

def test_authentication():
    """Test authentication endpoints"""
    print("\n🔐 Testing Authentication...")
    
    # Test login
    login_data = {
        "username": "juan_perez",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        
        # Test auth check
        response = requests.get(f"{BASE_URL}/auth/check")
        if response.status_code == 200:
            auth_data = response.json()
            print(f"   Authenticated: {auth_data['authenticated']}")
            print(f"   User: {auth_data.get('username', 'N/A')}")
        
        # Test logout
        response = requests.post(f"{BASE_URL}/auth/logout")
        if response.status_code == 200:
            print("✅ Logout successful")
    else:
        print(f"❌ Login failed: {response.status_code}")

def main():
    """Run all API tests"""
    print("🚀 SINPE Banking System API Test Suite")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test health check first
    if not test_health_check():
        print("❌ Server is not responding. Make sure to run 'python main.py' first.")
        return
    
    # Run all tests
    test_users_api()
    test_accounts_api()
    test_phone_links_api()
    test_sinpe_validation()
    test_sinpe_user_link()
    test_transactions_api()
    test_authentication()
    test_sinpe_transfer()
    
    print("\n" + "=" * 50)
    print("🎉 API test suite completed!")
    print("\nTo run the full system:")
    print("  python main.py")
    print("\nTo access the API directly:")
    print("  curl http://127.0.0.1:5000/health")

if __name__ == "__main__":
    main()
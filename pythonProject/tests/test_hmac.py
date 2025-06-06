"""
Test HMAC generation and verification
"""

import unittest
from app.utils.hmac_generator import (
    generate_hmac_for_account_transfer,
    generate_hmac_for_phone_transfer,
    verify_hmac
)

class TestHMACGeneration(unittest.TestCase):
    
    def test_account_transfer_hmac(self):
        """Test HMAC generation for account transfers"""
        account_number = "152001234567890"
        timestamp = "2024-01-15T10:30:00Z"
        transaction_id = "12345678-1234-1234-1234-123456789012"
        amount = 5000.00
        
        hmac_result = generate_hmac_for_account_transfer(
            account_number, timestamp, transaction_id, amount
        )
        
        self.assertIsInstance(hmac_result, str)
        self.assertEqual(len(hmac_result), 32)  # MD5 hex length
    
    def test_phone_transfer_hmac(self):
        """Test HMAC generation for phone transfers"""
        phone_number = "88887777"
        timestamp = "2024-01-15T10:30:00Z"
        transaction_id = "12345678-1234-1234-1234-123456789012"
        amount = 5000.00
        
        hmac_result = generate_hmac_for_phone_transfer(
            phone_number, timestamp, transaction_id, amount
        )
        
        self.assertIsInstance(hmac_result, str)
        self.assertEqual(len(hmac_result), 32)  # MD5 hex length
    
    def test_hmac_verification_phone(self):
        """Test HMAC verification for phone transfers"""
        payload = {
            "version": "1.0",
            "timestamp": "2024-01-15T10:30:00Z",
            "transaction_id": "12345678-1234-1234-1234-123456789012",
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
                "value": 5000.00,
                "currency": "CRC"
            },
            "description": "Test transfer"
        }
        
        # Generate correct HMAC
        correct_hmac = generate_hmac_for_phone_transfer(
            payload["sender"]["phone"],
            payload["timestamp"],
            payload["transaction_id"],
            payload["amount"]["value"]
        )
        
        # Test verification
        self.assertTrue(verify_hmac(payload, correct_hmac))
        self.assertFalse(verify_hmac(payload, "invalid_hmac"))
    
    def test_hmac_verification_account(self):
        """Test HMAC verification for account transfers"""
        payload = {
            "version": "1.0",
            "timestamp": "2024-01-15T10:30:00Z",
            "transaction_id": "12345678-1234-1234-1234-123456789012",
            "sender": {
                "account_number": "152001234567890",
                "bank_code": "152",
                "name": "Juan Pérez"
            },
            "receiver": {
                "account_number": "152001234567891",
                "bank_code": "152",
                "name": "María Rodríguez"
            },
            "amount": {
                "value": 5000.00,
                "currency": "CRC"
            },
            "description": "Test transfer"
        }
        
        # Generate correct HMAC
        correct_hmac = generate_hmac_for_account_transfer(
            payload["sender"]["account_number"],
            payload["timestamp"],
            payload["transaction_id"],
            payload["amount"]["value"]
        )
        
        # Test verification
        self.assertTrue(verify_hmac(payload, correct_hmac))
        self.assertFalse(verify_hmac(payload, "invalid_hmac"))

if __name__ == '__main__':
    unittest.main()
"""
HMAC Generator - Generate and verify HMAC signatures for SINPE transfers
"""

import hmac
import hashlib
from datetime import datetime

def generate_hmac(account_number: str, timestamp: str, transaction_id: str, amount: float, key: str = "supersecreta123") -> str:
    """
    Generate HMAC signature for SINPE transfer
    
    Args:
        account_number: Account number
        timestamp: Transaction timestamp
        transaction_id: Unique transaction ID
        amount: Transfer amount
        key: Secret key for HMAC generation
        
    Returns:
        str: Generated HMAC signature
    """
    amount_str = "{:.2f}".format(float(amount))
    message = account_number + timestamp + transaction_id + amount_str
    return hmac.new(key.encode(), message.encode(), hashlib.md5).hexdigest()

def verify_hmac(data: dict, signature: str, key: str = "supersecreta123") -> bool:
    """
    Verify HMAC signature for SINPE transfer
    
    Args:
        data: Transfer data
        signature: HMAC signature to verify
        key: Secret key for HMAC verification
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    try:
        # Extract required fields
        account_number = data['sender']['account_number']
        timestamp = data['timestamp']
        transaction_id = data['transaction_id']
        amount = data['amount']['value']
        
        # Generate HMAC
        expected_signature = generate_hmac(account_number, timestamp, transaction_id, amount, key)
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
        
    except (KeyError, TypeError, ValueError):
        return False

def generate_nack_response(error_message: str) -> dict:
    """
    Generate NACK (Negative Acknowledgement) response
    
    Args:
        error_message: Error message
        
    Returns:
        dict: NACK response
    """
    return {
        'status': 'NACK',
        'timestamp': datetime.utcnow().isoformat(),
        'error': error_message
    }

def generate_ack_response(data: dict = None) -> dict:
    """
    Generate ACK (Acknowledgement) response
    
    Args:
        data: Optional data to include in response
        
    Returns:
        dict: ACK response
    """
    response = {
        'status': 'ACK',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data:
        response['data'] = data
        
    return response

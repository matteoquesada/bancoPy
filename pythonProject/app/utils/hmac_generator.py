"""
HMAC Generation Utilities for SINPE Banking System
"""

import hashlib
import hmac

SECRET_KEY = "supersecreta123"

def generate_hmac_for_account_transfer(account_number: str, timestamp: str, transaction_id: str, amount: float) -> str:
    """
    Generate HMAC MD5 for account-to-account transfers
    
    Args:
        account_number: Account number of sender
        timestamp: ISO 8601 timestamp
        transaction_id: UUID of transaction
        amount: Transfer amount
        
    Returns:
        HMAC in hexadecimal format
    """
    message = f"{SECRET_KEY},{account_number},{timestamp},{transaction_id},{amount}"
    return hashlib.md5(message.encode()).hexdigest()

def generate_hmac_for_phone_transfer(phone_number: str, timestamp: str, transaction_id: str, amount: float) -> str:
    """
    Generate HMAC MD5 for SINPE mobile transfers (phone-based)
    
    Args:
        phone_number: Phone number of recipient
        timestamp: ISO 8601 timestamp
        transaction_id: UUID of transaction
        amount: Transfer amount
        
    Returns:
        HMAC in hexadecimal format
    """
    message = f"{SECRET_KEY},{phone_number},{timestamp},{transaction_id},{amount}"
    return hashlib.md5(message.encode()).hexdigest()

def verify_hmac(payload: dict, provided_hmac: str) -> bool:
    """
    Verify HMAC signature for incoming transfer requests
    
    Args:
        payload: Transfer payload containing all fields
        provided_hmac: HMAC provided in request
        
    Returns:
        True if HMAC is valid, False otherwise
    """
    try:
        # Determine if this is a phone or account transfer
        sender = payload.get('sender', {})
        
        if sender.get('phone'):
            # Phone-based transfer
            calculated_hmac = generate_hmac_for_phone_transfer(
                sender['phone'],
                payload['timestamp'],
                payload['transaction_id'],
                payload['amount']['value']
            )
        elif sender.get('account_number'):
            # Account-based transfer
            calculated_hmac = generate_hmac_for_account_transfer(
                sender['account_number'],
                payload['timestamp'],
                payload['transaction_id'],
                payload['amount']['value']
            )
        else:
            return False
            
        return calculated_hmac == provided_hmac
        
    except Exception:
        return False

def extract_bank_code_from_iban(iban: str) -> str:
    """
    Extract bank code from IBAN (positions 6-8, substring 5:8)
    
    Args:
        iban: IBAN string
        
    Returns:
        Bank code (3 digits)
    """
    if len(iban) < 8:
        return ""
    return iban[5:8]

def is_external_transfer(bank_code: str) -> bool:
    """
    Determine if transfer is to external bank (not our bank code "152")
    
    Args:
        bank_code: Bank code to check
        
    Returns:
        True if external bank, False if internal
    """
    LOCAL_BANK_CODE = "152"
    return bank_code != LOCAL_BANK_CODE
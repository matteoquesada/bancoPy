"""
IBAN Generation Utilities for SINPE Banking System
"""

import random
import string

def generate_iban(bank_code: str = "152", country_code: str = "CR") -> str:
    """
    Generate a Costa Rican IBAN for the banking system
    
    Args:
        bank_code: Bank code (default "152" for local bank)
        country_code: Country code (default "CR" for Costa Rica)
        
    Returns:
        Generated IBAN string
    """
    # Generate random account number (12 digits)
    account_number = ''.join(random.choices(string.digits, k=12))
    
    # Calculate check digits (simplified - in real IBAN this is more complex)
    check_digits = str(random.randint(10, 99))
    
    # Format: CR + check_digits + bank_code + account_number
    iban = f"{country_code}{check_digits}{bank_code}{account_number}"
    
    return iban

def generate_account_number() -> str:
    """
    Generate a unique account number
    
    Returns:
        Account number string
    """
    # Generate 15-digit account number
    return ''.join(random.choices(string.digits, k=15))

def validate_iban_format(iban: str) -> bool:
    """
    Basic IBAN format validation
    
    Args:
        iban: IBAN to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    if not iban or len(iban) < 15:
        return False
        
    # Check if starts with country code
    if not iban[:2].isalpha():
        return False
        
    # Check if rest contains only digits
    if not iban[2:].isdigit():
        return False
        
    return True
"""
IBAN Generator - Generate Costa Rican IBAN numbers
"""

import random

def generate_account_number():
    """
    Generate a Costa Rican account number (12 random digits)
    
    Returns:
        str: Generated account number
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])

def generate_iban():
    """
    Generate a Costa Rican IBAN number
    Format: CR21+0666+0001+12 random digits
    
    Returns:
        str: Generated IBAN number
    """
    # Fixed parts
    country_code = "CR21"
    bank_code = "0666"  # Our bank code with leading 0
    branch_code = "0001"  # Fixed branch code
    
    # Generate account number
    account_number = generate_account_number()
    
    # Combine all parts
    iban = f"{country_code}{bank_code}{branch_code}{account_number}"
    
    return iban

def validate_iban(iban: str) -> bool:
    """
    Validate a Costa Rican IBAN number
    
    Args:
        iban: IBAN number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not iban or len(iban) != 22:  # CR21 + 0666 + 0001 + 12 digits = 22 chars
        return False
        
    # Check fixed parts
    if not (iban.startswith("CR21") and 
            iban[4:8] == "0666" and  # Our bank
            iban[8:12] == "0001"):
        return False
    
    # Check if last 12 characters are digits
    return iban[12:].isdigit()

def extract_bank_code(iban: str) -> str:
    """
    Extract bank code from IBAN
    
    Args:
        iban: IBAN number
        
    Returns:
        str: Bank code or None if invalid
    """
    if not validate_iban(iban):
        return None
    
    return iban[4:8]  # Get the bank code part (0666)

def extract_account_number(iban: str) -> str:
    """
    Extract account number from IBAN
    
    Args:
        iban: IBAN number
        
    Returns:
        str: Account number or None if invalid
    """
    if not validate_iban(iban):
        return None
    
    return iban[12:]  # Get the account number part (12 digits)

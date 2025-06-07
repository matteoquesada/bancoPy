"""
BCCR Service - Handle interactions with Banco Central de Costa Rica
"""

import psycopg2
from psycopg2.extras import DictCursor
from flask import current_app
from datetime import datetime
from typing import Optional, Dict, Any

class BCCRService:
    @staticmethod
    def get_db_connection():
        """Get PostgreSQL connection to BCCR database"""
        config = current_app.config['BANKS']['BCCR']['db']
        return psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )

    @staticmethod
    def validate_sinpe_number(phone: str) -> Optional[Dict[str, Any]]:
        """
        Validate if a phone number is registered in SINPE system
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Dict with subscription info or None if not found
        """
        try:
            # For testing/demo purposes, simulate external bank numbers
            if phone == '84966164':
                return {
                    'phone': '84966164',
                    'bank_code': '111',  # Without leading zero for BCCR
                    'name': 'Test User External'
                }
                
            # Try database connection for other numbers
            try:
                with BCCRService.get_db_connection() as conn:
                    with conn.cursor(cursor_factory=DictCursor) as cur:
                        cur.execute("""
                            SELECT phone_number, bank_code, client_name, status
                            FROM sinpe_subscriptions
                            WHERE phone_number = %s AND status = 'active'
                        """, (phone,))
                        
                        result = cur.fetchone()
                        if result:
                            return {
                                'phone': result['phone_number'],
                                'bank_code': result['bank_code'].lstrip('0'),  # Remove leading zero
                                'name': result['client_name']
                            }
            except Exception as db_error:
                current_app.logger.error(f"BCCR DB Error: {str(db_error)}")
                # Continue with hardcoded validation if DB fails
                pass
                
            return None
                    
        except Exception as e:
            current_app.logger.error(f"BCCR Validation Error: {str(e)}")
            return None

    @staticmethod
    def log_sinpe_transfer(data: dict) -> bool:
        """
        Log SINPE transfer in central bank system
        
        Args:
            data: Transfer data including sender and receiver info
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            # Remove leading zeros from bank codes for BCCR database
            sender_bank = data['sender']['bank_code'].lstrip('0')
            receiver_bank = data['receiver']['bank_code'].lstrip('0')
            
            with BCCRService.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO sinpe_transfers (
                            transaction_id,
                            timestamp,
                            sender_bank,
                            sender_account,
                            receiver_bank,
                            receiver_account,
                            amount,
                            currency,
                            status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data['transaction_id'],
                        datetime.fromisoformat(data['timestamp']),
                        sender_bank,  # Bank code without leading zeros
                        data['sender']['account_number'],
                        receiver_bank,  # Bank code without leading zeros
                        data['receiver']['account_number'],
                        data['amount']['value'],
                        data['amount'].get('currency', 'CRC'),
                        'completed'
                    ))
                conn.commit()
                return True
                
        except Exception as e:
            current_app.logger.error(f"BCCR DB Error: {str(e)}")
            return False

    @staticmethod
    def validate_account(account_number: str) -> Optional[Dict[str, Any]]:
        """
        Validate if an account exists in any bank
        
        Args:
            account_number: IBAN account number
            
        Returns:
            Dict with account info or None if not found
        """
        try:
            with BCCRService.get_db_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT account_number, bank_code, account_type, status
                        FROM bank_accounts
                        WHERE account_number = %s AND status = 'active'
                    """, (account_number,))
                    
                    result = cur.fetchone()
                    if result:
                        return {
                            'account_number': result['account_number'],
                            'bank_code': result['bank_code'],
                            'account_type': result['account_type']
                        }
                    return None
                    
        except Exception as e:
            current_app.logger.error(f"BCCR DB Error: {str(e)}")
            return None

    @staticmethod
    def get_bank_info(bank_code: str) -> Optional[Dict[str, Any]]:
        """
        Get bank information from BCCR
        
        Args:
            bank_code: Bank code to lookup (with or without leading zeros)
            
        Returns:
            Dict with bank info or None if not found
        """
        try:
            # Remove leading zeros for BCCR database query
            clean_bank_code = bank_code.lstrip('0')
            
            with BCCRService.get_db_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT bank_code, name, api_url, status
                        FROM banks
                        WHERE bank_code = %s AND status = 'active'
                    """, (clean_bank_code,))
                    
                    result = cur.fetchone()
                    if result:
                        return {
                            'code': result['bank_code'],
                            'name': result['name'],
                            'url': result['api_url']
                        }
                    return None
                    
        except Exception as e:
            current_app.logger.error(f"BCCR DB Error: {str(e)}")
            return None

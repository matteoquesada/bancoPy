"""
SINPE Service - Core business logic for SINPE transfers
"""

from app.models import db, User, Account, UserAccount, PhoneLink, SinpeSubscription, Transaction
from app.utils.hmac_generator import generate_nack_response, generate_ack_response
from app.services.bccr_service import BCCRService
from decimal import Decimal
import uuid
import requests
import json
from datetime import datetime
from flask import current_app, g

class SinpeService:
    
    @staticmethod
    def find_phone_link_for_user(username: str):
        """
        Find phone link for a specific user
        
        Args:
            username: Username to search for
            
        Returns:
            Dict with phone and account info, or None if not found
        """
        user = User.query.filter_by(name=username).first()
        if not user:
            return None
            
        # Check all user accounts for phone links
        for user_account in user.user_accounts:
            account = user_account.account
            phone_link = PhoneLink.query.filter_by(account_number=account.number).first()
            
            if phone_link:
                return {
                    'phone': phone_link.phone,
                    'account': account.number
                }
                
        return None
    
    @staticmethod
    def find_phone_subscription(phone: str):
        """
        Find phone subscription in BCCR system
        
        Args:
            phone: Phone number to search for
            
        Returns:
            SinpeSubscription object or None
        """
        return SinpeSubscription.query.filter_by(sinpe_number=phone).first()
    
    @staticmethod
    def process_sinpe_transfer(data: dict, current_user=None) -> dict:
        """
        Process SINPE transfer between accounts
        
        Args:
            data: Transfer data including sender and receiver info
            current_user: Current authenticated user
            
        Returns:
            dict: Response with ACK/NACK status
        """
        try:
            # Validate sender account ownership
            if not current_user:
                return generate_nack_response("Authentication required")
            
            sender_account = Account.query.filter_by(number=data['sender']['account_number']).first()
            if not sender_account:
                return generate_nack_response("Sender account not found")
            
            # Verify account ownership
            user_account = UserAccount.query.filter_by(
                user_id=current_user.id,
                account_id=sender_account.id
            ).first()
            if not user_account:
                return generate_nack_response("No permission to use this account")
            
            # Check if this is an external transfer
            receiver_bank = data['receiver']['bank_code']
            if receiver_bank.lstrip('0') != "666":  # Compare without leading zeros
                # External transfer - forward to other bank
                # Ensure bank codes are properly formatted
                data['sender']['bank_code'] = "666"  # BCCR format without leading 0
                data['receiver']['bank_code'] = receiver_bank.lstrip('0')  # Remove leading 0 for BCCR
                return SinpeService._handle_external_transfer(data)
            
            # Local transfer
            receiver_account = Account.query.filter_by(number=data['receiver']['account_number']).first()
            if not receiver_account:
                return generate_nack_response("Receiver account not found")
            
            # Check balance
            amount = Decimal(str(data['amount']['value']))
            if sender_account.balance < amount:
                return generate_nack_response("Insufficient funds")
            
            # Process transfer
            sender_account.balance -= amount
            receiver_account.balance += amount
            
            # Create transaction record
            transaction = Transaction(
                transaction_id=data['transaction_id'],
                from_account_id=sender_account.id,
                to_account_id=receiver_account.id,
                amount=amount,
                currency=data['amount'].get('currency', 'CRC'),
                description=data.get('description', ''),
                status="completed"
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return generate_ack_response({
                'transaction': transaction.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            return generate_nack_response(str(e))
    
    @staticmethod
    def send_sinpe_movil(sender_phone: str, receiver_phone: str, amount: float, currency: str = "CRC", description: str = "", current_user=None):
        """
        Process SINPE mobile transfer
        
        Args:
            sender_phone: Sender's phone number
            receiver_phone: Receiver's phone number
            amount: Transfer amount
            currency: Currency code
            description: Transfer description
            current_user: Current authenticated user
            
        Returns:
            Transaction object
            
        Raises:
            Exception: If transfer cannot be processed
        """
        # Validate amount
        if amount <= 0:
            raise Exception("El monto debe ser mayor a cero.")
            
        # 1. Validate receiver is registered in BCCR
        subscription = SinpeSubscription.query.filter_by(sinpe_number=receiver_phone).first()
        if not subscription:
            # Try to validate with external BCCR system
            bccr_result = BCCRService.validate_sinpe_number(receiver_phone)
            if not bccr_result:
                raise Exception("El número de destino no está registrado en SINPE Móvil.")
            # Create temporary subscription for external number
            subscription = SinpeSubscription(
                sinpe_number=bccr_result['phone'],
                sinpe_bank_code=f"0{bccr_result['bank_code']}",  # Add leading zero for routing
                sinpe_client_name=bccr_result['name']
            )
        
        # 2. Get receiver account info
        receiver_link = PhoneLink.query.filter_by(phone=receiver_phone).first()
        to_account = None
        is_external_transfer = False
        
        if receiver_link:
            # Local receiver
            to_account = Account.query.filter_by(number=receiver_link.account_number).first()
            if not to_account:
                raise Exception("La cuenta destino no existe.")
        else:
            # External receiver - need to handle inter-bank transfer
            is_external_transfer = True
            if not subscription:
                raise Exception("No se puede procesar transferencia externa sin información del banco destino.")
        
        # 3. Check sender account
        sender_link = PhoneLink.query.filter_by(phone=sender_phone).first()
        from_account_id = None
        from_account = None
        
        if sender_link:
            from_account = Account.query.filter_by(number=sender_link.account_number).first()
            if not from_account:
                raise Exception("La cuenta origen vinculada al número remitente no existe.")
                
            # Validate user ownership if current_user is provided
            if current_user:
                user_account = UserAccount.query.filter_by(
                    user_id=current_user.id, 
                    account_id=from_account.id
                ).first()
                if not user_account:
                    raise Exception("No tiene permisos para usar esta cuenta.")
                
            if from_account.balance < Decimal(str(amount)):
                raise Exception("Fondos insuficientes en la cuenta origen.")
                
            from_account_id = from_account.id
        else:
            # External sender - this is an incoming transfer
            if not current_user:
                raise Exception("Se requiere autenticación para transferencias externas.")
        
        # 4. Process transfer based on type
        transaction_id = str(uuid.uuid4())
        
        if is_external_transfer:
            # Handle external transfer
            result = SinpeService._process_external_transfer(
                sender_phone, receiver_phone, amount, currency, description, transaction_id
            )
            if not result['success']:
                raise Exception(result['error'])
        else:
            # Local transfer
            if from_account:
                # Deduct funds from sender
                from_account.balance -= Decimal(str(amount))
            
            # Credit funds to receiver
            to_account.balance += Decimal(str(amount))
        
        # 5. Create transaction record
        transaction = Transaction(
            transaction_id=transaction_id,
            from_account_id=from_account_id,
            to_account_id=to_account.id if to_account else None,
            amount=Decimal(str(amount)),
            currency=currency,
            description=description,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            status="completed"
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Basic phone number validation
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid format, False otherwise
        """
        # Remove any non-digit characters
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Costa Rican phone numbers are typically 8 digits
        return len(clean_phone) == 8
    
    @staticmethod
    def get_user_accounts_with_phone_links(username: str):
        """
        Get all accounts for a user with their phone links
        
        Args:
            username: Username to search for
            
        Returns:
            List of account info with phone links
        """
        user = User.query.filter_by(name=username).first()
        if not user:
            return []
            
        accounts_info = []
        for user_account in user.user_accounts:
            account = user_account.account
            phone_link = PhoneLink.query.filter_by(account_number=account.number).first()
            
            account_info = account.to_dict()
            account_info['phone_link'] = phone_link.to_dict() if phone_link else None
            accounts_info.append(account_info)
            
        return accounts_info
    
    @staticmethod
    def _handle_external_transfer(data: dict) -> dict:
        """
        Handle transfer to external bank
        
        Args:
            data: Transfer data
            
        Returns:
            dict: Response with ACK/NACK status
        """
        try:
            # Get bank configuration - use bank code with leading 0 for routing
            banks_config = current_app.config.get('BANKS', {})
            target_bank_code = f"0{data['receiver']['bank_code']}"  # Add leading 0 for routing
            target_bank = banks_config.get(target_bank_code)
            
            if not target_bank:
                return generate_nack_response(f"Invalid bank code: {target_bank_code}")
            
            # Send request to target bank
            headers = {
                'Content-Type': 'application/json',
                'X-Bank-Code': '0666'
            }
            
            response = requests.post(
                f"{target_bank['url']}/api/sinpe-transfer",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                return generate_nack_response(response.json().get('error', 'External transfer failed'))
                
        except requests.RequestException as e:
            return generate_nack_response(f"Connection error: {str(e)}")
        except Exception as e:
            return generate_nack_response(f"Internal error: {str(e)}")
    
    @staticmethod
    def _validate_bccr_phone(phone: str) -> bool:
        """
        Validate phone number with external BCCR system
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Get BCCR configuration
            banks_config = current_app.config.get('BANKS', {})
            bccr_url = banks_config.get('CB', {}).get('url')
            
            if not bccr_url:
                return False
                
            # Make request to BCCR validation endpoint
            response = requests.get(f"{bccr_url}/api/validate/{phone}", timeout=5)
            return response.status_code == 200
            
        except Exception:
            return False
    
    @staticmethod
    def _process_external_sinpe_movil(data: dict) -> dict:
        """
        Process external inter-bank transfer
        
        Args:
            sender_phone: Sender's phone number
            receiver_phone: Receiver's phone number
            amount: Transfer amount
            currency: Currency code
            description: Transfer description
            transaction_id: Unique transaction ID
            
        Returns:
            Dict with success status and message
        """
        try:
            # Get receiver bank info
            subscription = SinpeSubscription.query.filter_by(sinpe_number=receiver_phone).first()
            if not subscription:
                return {'success': False, 'error': 'Información del banco destino no disponible'}
            
            # Get bank configuration
            banks_config = current_app.config.get('BANKS', {})
            target_bank = banks_config.get(subscription.sinpe_bank_code)
            
            if not target_bank:
                return {'success': False, 'error': 'Banco destino no configurado'}
            
            # Prepare transfer payload
            from app.utils.hmac_generator import generate_hmac
            
            payload = {
                "version": "1.0",
                "timestamp": datetime.utcnow().isoformat(),
                "transaction_id": transaction_id,
                "sender": {
                    "phone": sender_phone,
                    "bank_code": "666",  # Local bank code (without leading 0 for BCCR)
                    "name": "My Bank"
                },
                "receiver": {
                    "phone": receiver_phone,
                    "bank_code": subscription.sinpe_bank_code.lstrip('0'),  # Remove leading 0 for BCCR
                    "name": subscription.sinpe_client_name
                },
                "amount": {
                    "value": amount,
                    "currency": currency
                },
                "description": description
            }
            
            # Generate HMAC
            hmac_signature = generate_hmac(payload)
            payload["hmac_md5"] = hmac_signature
            
            # Send request to target bank
            headers = {
                'Content-Type': 'application/json',
                'X-Bank-Code': '0666',  # Use full bank code with leading 0 for routing
                'X-SINPE-Token': 'sinpe-transfer-token'
            }
            
            response = requests.post(
                f"{target_bank['url']}/api/sinpe-movil",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                return {'success': True, 'message': 'Transferencia externa exitosa'}
            else:
                error_msg = response.json().get('error', 'Error en transferencia externa')
                return {'success': False, 'error': error_msg}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Error de conexión: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Error interno: {str(e)}'}
    
    @staticmethod
    def get_current_user_context():
        """
        Get current user context from Flask g object
        
        Returns:
            Current user or None
        """
        return getattr(g, 'current_user', None)

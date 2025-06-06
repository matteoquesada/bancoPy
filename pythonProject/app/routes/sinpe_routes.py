"""
SINPE Routes - API endpoints for SINPE functionality
"""

from flask import Blueprint, request, jsonify
from app.services.sinpe_service import SinpeService
from app.utils.hmac_generator import verify_hmac

sinpe_bp = Blueprint('sinpe', __name__)

@sinpe_bp.route('/sinpe/user-link/<username>', methods=['GET'])
def check_user_sinpe_link(username):
    """
    Check if user has SINPE phone link
    
    Args:
        username: Username to check
        
    Returns:
        JSON response with link status
    """
    try:
        result = SinpeService.find_phone_link_for_user(username)
        
        if not result:
            return jsonify({'linked': False})
            
        return jsonify({
            'linked': True,
            'phone': result['phone'],
            'account': result['account']
        })
        
    except Exception as e:
        return jsonify({'error': 'Error del servidor'}), 500

@sinpe_bp.route('/sinpe-movil', methods=['POST'])
def handle_sinpe_transfer():
    """
    Handle SINPE mobile transfer requests
    
    Expected payload:
    {
        "version": "string",
        "timestamp": "string",
        "transaction_id": "string",
        "sender": {
            "phone": "string",
            "bank_code": "string",
            "name": "string"
        },
        "receiver": {
            "account_number": "string",
            "phone": "string",
            "bank_code": "string",
            "name": "string"
        },
        "amount": {
            "value": float,
            "currency": "string"
        },
        "description": "string",
        "hmac_md5": "string"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sender', 'receiver', 'amount', 'hmac_md5']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Falta el campo: {field}'}), 400
        
        sender = data['sender']
        receiver = data['receiver']
        amount = data['amount']
        hmac_md5 = data['hmac_md5']
        
        # Validate sender phone or receiver phone
        if not sender.get('phone') and not receiver.get('phone'):
            return jsonify({'error': 'Se requiere teléfono del remitente o receptor'}), 400
            
        if not amount.get('value'):
            return jsonify({'error': 'Se requiere el monto de la transferencia'}), 400
        
        # Verify HMAC
        if not verify_hmac(data, hmac_md5):
            return jsonify({'error': 'HMAC inválido'}), 403
        
        # Determine phone numbers for transfer
        sender_phone = sender.get('phone', '')
        receiver_phone = receiver.get('phone', '')
        
        # If receiver doesn't have phone, this might be account-to-account
        if not receiver_phone and receiver.get('account_number'):
            # For account-to-account, we need to find the phone linked to the account
            from app.models import PhoneLink
            phone_link = PhoneLink.query.filter_by(account_number=receiver['account_number']).first()
            if phone_link:
                receiver_phone = phone_link.phone
            else:
                return jsonify({'error': 'Cuenta destino no tiene teléfono vinculado'}), 400
        
        # Process transfer
        transfer = SinpeService.send_sinpe_transfer(
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            amount=amount['value'],
            currency=amount.get('currency', 'CRC'),
            description=data.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'message': 'Transferencia realizada exitosamente',
            'data': transfer.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sinpe_bp.route('/validate/<phone>', methods=['GET'])
def validate_phone(phone):
    """
    Validate phone number in BCCR system
    
    Args:
        phone: Phone number to validate
        
    Returns:
        JSON response with validation result
    """
    try:
        subscription = SinpeService.find_phone_subscription(phone)
        
        if not subscription:
            return jsonify({'error': 'No registrado'}), 404
            
        return jsonify({
            'name': subscription.sinpe_client_name,
            'bank_code': subscription.sinpe_bank_code,
            'phone': subscription.sinpe_number
        })
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@sinpe_bp.route('/sinpe/accounts/<username>', methods=['GET'])
def get_user_sinpe_accounts(username):
    """
    Get all accounts for a user with their SINPE phone links
    
    Args:
        username: Username to get accounts for
        
    Returns:
        JSON response with user accounts and phone links
    """
    try:
        accounts = SinpeService.get_user_accounts_with_phone_links(username)
        
        return jsonify({
            'success': True,
            'data': accounts
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
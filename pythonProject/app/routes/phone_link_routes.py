"""
Phone Link Routes - API endpoints for phone link management
"""

from flask import Blueprint, request, jsonify
from app.models import db, PhoneLink, Account
from app.services.sinpe_service import SinpeService

phone_link_bp = Blueprint('phone_links', __name__)

@phone_link_bp.route('/phone-links', methods=['GET'])
def get_phone_links():
    """Get all phone links"""
    try:
        phone_links = PhoneLink.query.all()
        return jsonify({
            'success': True,
            'data': [link.to_dict() for link in phone_links]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@phone_link_bp.route('/phone-links', methods=['POST'])
def create_phone_link():
    """Create new phone link"""
    try:
        data = request.get_json()
        
        required_fields = ['account_number', 'phone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Validate phone number format
        if not SinpeService.validate_phone_number(data['phone']):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Check if account exists
        account = Account.query.filter_by(number=data['account_number']).first()
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Check if phone is already linked
        existing_phone_link = PhoneLink.query.filter_by(phone=data['phone']).first()
        if existing_phone_link:
            return jsonify({'error': 'Phone number already linked to another account'}), 400
        
        # Check if account already has a phone link
        existing_account_link = PhoneLink.query.filter_by(account_number=data['account_number']).first()
        if existing_account_link:
            return jsonify({'error': 'Account already has a phone link'}), 400
        
        phone_link = PhoneLink(
            account_number=data['account_number'],
            phone=data['phone']
        )
        
        db.session.add(phone_link)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': phone_link.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@phone_link_bp.route('/phone-links/<int:link_id>', methods=['GET'])
def get_phone_link(link_id):
    """Get specific phone link"""
    try:
        phone_link = PhoneLink.query.get_or_404(link_id)
        return jsonify({
            'success': True,
            'data': phone_link.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@phone_link_bp.route('/phone-links/phone/<phone>', methods=['GET'])
def get_phone_link_by_phone(phone):
    """Get phone link by phone number"""
    try:
        phone_link = PhoneLink.query.filter_by(phone=phone).first()
        
        if not phone_link:
            return jsonify({'error': 'Phone link not found'}), 404
            
        return jsonify({
            'success': True,
            'data': phone_link.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@phone_link_bp.route('/phone-links/account/<account_number>', methods=['GET'])
def get_phone_link_by_account(account_number):
    """Get phone link by account number"""
    try:
        phone_link = PhoneLink.query.filter_by(account_number=account_number).first()
        
        if not phone_link:
            return jsonify({'error': 'Phone link not found'}), 404
            
        return jsonify({
            'success': True,
            'data': phone_link.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@phone_link_bp.route('/phone-links/<int:link_id>', methods=['PUT'])
def update_phone_link(link_id):
    """Update phone link"""
    try:
        phone_link = PhoneLink.query.get_or_404(link_id)
        data = request.get_json()
        
        if 'phone' in data:
            # Validate new phone number
            if not SinpeService.validate_phone_number(data['phone']):
                return jsonify({'error': 'Invalid phone number format'}), 400
                
            # Check if new phone is already linked
            existing_link = PhoneLink.query.filter_by(phone=data['phone']).first()
            if existing_link and existing_link.id != link_id:
                return jsonify({'error': 'Phone number already linked to another account'}), 400
                
            phone_link.phone = data['phone']
        
        if 'account_number' in data:
            # Check if account exists
            account = Account.query.filter_by(number=data['account_number']).first()
            if not account:
                return jsonify({'error': 'Account not found'}), 404
                
            # Check if new account already has a phone link
            existing_link = PhoneLink.query.filter_by(account_number=data['account_number']).first()
            if existing_link and existing_link.id != link_id:
                return jsonify({'error': 'Account already has a phone link'}), 400
                
            phone_link.account_number = data['account_number']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': phone_link.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@phone_link_bp.route('/phone-links/<int:link_id>', methods=['DELETE'])
def delete_phone_link(link_id):
    """Delete phone link"""
    try:
        phone_link = PhoneLink.query.get_or_404(link_id)
        db.session.delete(phone_link)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Phone link deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
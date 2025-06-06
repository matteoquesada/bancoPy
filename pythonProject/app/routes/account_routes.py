"""
Account Routes - API endpoints for account management
"""

from flask import Blueprint, request, jsonify
from app.models import db, Account, User, UserAccount
from app.utils.iban_generator import generate_account_number
from decimal import Decimal

account_bp = Blueprint('accounts', __name__)

@account_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Get all accounts"""
    try:
        accounts = Account.query.all()
        return jsonify({
            'success': True,
            'data': [account.to_dict() for account in accounts]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@account_bp.route('/accounts', methods=['POST'])
def create_account():
    """Create new account"""
    try:
        data = request.get_json()
        
        # Generate account number if not provided
        account_number = data.get('number', generate_account_number())
        
        # Check if account number already exists
        if Account.query.filter_by(number=account_number).first():
            return jsonify({'error': 'Account number already exists'}), 400
        
        account = Account(
            number=account_number,
            currency=data.get('currency', 'CRC'),
            balance=Decimal(str(data.get('balance', 0)))
        )
        
        db.session.add(account)
        db.session.commit()
        
        # Link to user if user_id provided
        if 'user_id' in data:
            user = User.query.get(data['user_id'])
            if user:
                user_account = UserAccount(user_id=user.id, account_id=account.id)
                db.session.add(user_account)
                db.session.commit()
        
        return jsonify({
            'success': True,
            'data': account.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@account_bp.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    """Get specific account"""
    try:
        account = Account.query.get_or_404(account_id)
        return jsonify({
            'success': True,
            'data': account.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@account_bp.route('/accounts/<account_number>', methods=['GET'])
def get_account_by_number(account_number):
    """Get account by account number"""
    try:
        account = Account.query.filter_by(number=account_number).first_or_404()
        return jsonify({
            'success': True,
            'data': account.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@account_bp.route('/accounts/<int:account_id>/balance', methods=['PUT'])
def update_balance(account_id):
    """Update account balance"""
    try:
        account = Account.query.get_or_404(account_id)
        data = request.get_json()
        
        if 'balance' not in data:
            return jsonify({'error': 'Balance is required'}), 400
            
        account.balance = Decimal(str(data['balance']))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': account.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@account_bp.route('/users/<int:user_id>/accounts', methods=['GET'])
def get_user_accounts(user_id):
    """Get all accounts for a specific user"""
    try:
        user = User.query.get_or_404(user_id)
        accounts = []
        
        for user_account in user.user_accounts:
            accounts.append(user_account.account.to_dict())
            
        return jsonify({
            'success': True,
            'data': accounts
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@account_bp.route('/users/<int:user_id>/accounts', methods=['POST'])
def link_account_to_user(user_id):
    """Link existing account to user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'account_id' not in data:
            return jsonify({'error': 'Account ID is required'}), 400
            
        account = Account.query.get_or_404(data['account_id'])
        
        # Check if link already exists
        existing_link = UserAccount.query.filter_by(
            user_id=user_id, 
            account_id=account.id
        ).first()
        
        if existing_link:
            return jsonify({'error': 'Account already linked to user'}), 400
        
        user_account = UserAccount(user_id=user_id, account_id=account.id)
        db.session.add(user_account)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account linked to user successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
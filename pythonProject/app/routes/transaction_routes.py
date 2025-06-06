"""
Transaction Routes - API endpoints for transaction management
"""

from flask import Blueprint, request, jsonify
from app.models import db, Transaction, Account
from app.utils.hmac_generator import verify_hmac
from decimal import Decimal
import uuid

transaction_bp = Blueprint('transactions', __name__)

@transaction_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        transactions = Transaction.query.order_by(
            Transaction.created_at.desc()
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [transaction.to_dict() for transaction in transactions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': transactions.total,
                'pages': transactions.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get specific transaction"""
    try:
        transaction = Transaction.query.filter_by(
            transaction_id=transaction_id
        ).first_or_404()
        
        return jsonify({
            'success': True,
            'data': transaction.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/accounts/<account_number>/transactions', methods=['GET'])
def get_account_transactions(account_number):
    """Get transactions for specific account"""
    try:
        account = Account.query.filter_by(number=account_number).first_or_404()
        
        # Get both sent and received transactions
        sent_transactions = Transaction.query.filter_by(
            from_account_id=account.id
        ).all()
        
        received_transactions = Transaction.query.filter_by(
            to_account_id=account.id
        ).all()
        
        all_transactions = sent_transactions + received_transactions
        all_transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        return jsonify({
            'success': True,
            'data': [transaction.to_dict() for transaction in all_transactions]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions', methods=['POST'])
def create_transaction():
    """Create new transaction (for testing purposes)"""
    try:
        data = request.get_json()
        
        required_fields = ['from_account_id', 'to_account_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Validate accounts exist
        from_account = Account.query.get(data['from_account_id'])
        to_account = Account.query.get(data['to_account_id'])
        
        if not from_account or not to_account:
            return jsonify({'error': 'Invalid account ID'}), 400
        
        # Check sufficient balance
        amount = Decimal(str(data['amount']))
        if from_account.balance < amount:
            return jsonify({'error': 'Insufficient funds'}), 400
        
        # Create transaction
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            from_account_id=data['from_account_id'],
            to_account_id=data['to_account_id'],
            amount=amount,
            currency=data.get('currency', 'CRC'),
            description=data.get('description', ''),
            status='pending'
        )
        
        db.session.add(transaction)
        
        # Update balances
        from_account.balance -= amount
        to_account.balance += amount
        
        # Mark transaction as completed
        transaction.status = 'completed'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': transaction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions/<transaction_id>/status', methods=['PUT'])
def update_transaction_status(transaction_id):
    """Update transaction status"""
    try:
        transaction = Transaction.query.filter_by(
            transaction_id=transaction_id
        ).first_or_404()
        
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['pending', 'completed', 'failed', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        transaction.status = data['status']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': transaction.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions/verify-hmac', methods=['POST'])
def verify_transaction_hmac():
    """Verify HMAC for transaction payload"""
    try:
        data = request.get_json()
        
        if 'payload' not in data or 'hmac' not in data:
            return jsonify({'error': 'Payload and HMAC are required'}), 400
        
        is_valid = verify_hmac(data['payload'], data['hmac'])
        
        return jsonify({
            'success': True,
            'valid': is_valid
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
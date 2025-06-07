"""
Database Service - Initialize and manage database operations
"""

from app.models import db, User, Account, UserAccount, PhoneLink, SinpeSubscription, Currency, Transaction
from werkzeug.security import generate_password_hash
from decimal import Decimal
import uuid

class DatabaseService:
    
    def create_sample_data(self):
        """Create sample data for testing"""
        
        # Check if data already exists
        if User.query.first():
            return
        
        # Create currencies
        currencies = [
            Currency(code='CRC', name='Costa Rican Colón'),
            Currency(code='USD', name='US Dollar'),
            Currency(code='EUR', name='Euro')
        ]
        
        for currency in currencies:
            db.session.add(currency)
        
        # Create sample users
        users_data = [
            {
                'name': 'juan_perez',
                'email': 'juan@example.com',
                'phone': '88887777',
                'password': 'password123'
            },
            {
                'name': 'maria_rodriguez',
                'email': 'maria@example.com',
                'phone': '88886666',
                'password': 'password123'
            },
            {
                'name': 'carlos_gonzalez',
                'email': 'carlos@example.com',
                'phone': '88885555',
                'password': 'password123'
            },
            {
                'name': 'ana_lopez',
                'email': 'ana@example.com',
                'phone': '88884444',
                'password': 'password123'
            }
        ]
        
        users = []
        for user_data in users_data:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                phone=user_data['phone'],
                password_hash=generate_password_hash(user_data['password'])
            )
            users.append(user)
            db.session.add(user)
        
        db.session.flush()  # Get user IDs
        
        # Create sample accounts with proper IBAN format (CR21 + 0666 + 0001 + 12 digits)
        accounts_data = [
            {'number': 'CR2106660001123456789012', 'balance': 50000.00},
            {'number': 'CR2106660001123456789013', 'balance': 75000.00},
            {'number': 'CR2106660001123456789014', 'balance': 100000.00},
            {'number': 'CR2106660001123456789015', 'balance': 25000.00},
            {'number': 'CR2106660001123456789016', 'balance': 150000.00},
            {'number': 'CR2106660001123456789017', 'balance': 80000.00}
        ]
        
        accounts = []
        for account_data in accounts_data:
            account = Account(
                number=account_data['number'],
                currency='CRC',
                balance=Decimal(str(account_data['balance']))
            )
            accounts.append(account)
            db.session.add(account)
        
        db.session.flush()  # Get account IDs
        
        # Link users to accounts
        user_account_links = [
            (0, 0),  # juan_perez -> account 0
            (0, 1),  # juan_perez -> account 1
            (1, 2),  # maria_rodriguez -> account 2
            (2, 3),  # carlos_gonzalez -> account 3
            (2, 4),  # carlos_gonzalez -> account 4
            (3, 5),  # ana_lopez -> account 5
        ]
        
        for user_idx, account_idx in user_account_links:
            user_account = UserAccount(
                user_id=users[user_idx].id,
                account_id=accounts[account_idx].id
            )
            db.session.add(user_account)
        
        # Create phone links
        phone_links_data = [
            ('CR2106660001123456789012', '88887777'),  # juan's first account
            ('CR2106660001123456789014', '88886666'),  # maria's account
            ('CR2106660001123456789015', '88885555'),  # carlos's first account
            ('CR2106660001123456789017', '88884444'),  # ana's account
        ]
        
        for account_number, phone in phone_links_data:
            phone_link = PhoneLink(
                account_number=account_number,
                phone=phone
            )
            db.session.add(phone_link)
        
        # Create SINPE subscriptions (BCCR data)
        sinpe_subscriptions = [
            {
                'sinpe_number': '88887777',
                'sinpe_bank_code': '0666',
                'sinpe_client_name': 'Juan Pérez Mora'
            },
            {
                'sinpe_number': '88886666',
                'sinpe_bank_code': '0666',
                'sinpe_client_name': 'María Rodríguez Soto'
            },
            {
                'sinpe_number': '88885555',
                'sinpe_bank_code': '0666',
                'sinpe_client_name': 'Carlos González Vargas'
            },
            {
                'sinpe_number': '88884444',
                'sinpe_bank_code': '0666',
                'sinpe_client_name': 'Ana López Jiménez'
            },
            {
                'sinpe_number': '84966164',
                'sinpe_bank_code': '0152',
                'sinpe_client_name': 'Test User External'
            },
            {
                'sinpe_number': '88883333',
                'sinpe_bank_code': '0151',
                'sinpe_client_name': 'Pedro Ramírez Castro'
            },
            {
                'sinpe_number': '88882222',
                'sinpe_bank_code': '0153',
                'sinpe_client_name': 'Laura Fernández Rojas'
            }
        ]
        
        for sub_data in sinpe_subscriptions:
            subscription = SinpeSubscription(
                sinpe_number=sub_data['sinpe_number'],
                sinpe_bank_code=sub_data['sinpe_bank_code'],
                sinpe_client_name=sub_data['sinpe_client_name']
            )
            db.session.add(subscription)
        
        # Create sample transactions
        sample_transactions = [
            {
                'from_account_id': accounts[0].id,
                'to_account_id': accounts[2].id,
                'amount': 5000.00,
                'description': 'Transferencia de prueba',
                'sender_phone': '88887777',
                'receiver_phone': '88886666'
            },
            {
                'from_account_id': accounts[2].id,
                'to_account_id': accounts[3].id,
                'amount': 2500.00,
                'description': 'Pago de servicios',
                'sender_phone': '88886666',
                'receiver_phone': '88885555'
            }
        ]
        
        for trans_data in sample_transactions:
            transaction = Transaction(
                transaction_id=str(uuid.uuid4()),
                from_account_id=trans_data['from_account_id'],
                to_account_id=trans_data['to_account_id'],
                amount=Decimal(str(trans_data['amount'])),
                currency='CRC',
                description=trans_data['description'],
                sender_phone=trans_data['sender_phone'],
                receiver_phone=trans_data['receiver_phone'],
                status='completed'
            )
            db.session.add(transaction)
        
        # Commit all changes
        db.session.commit()
        
        print("✓ Sample data created successfully")
        print("Sample users:")
        for user in users:
            print(f"  - {user.name} (password: password123)")
        print("Sample phone numbers with SINPE links:")
        for phone_link in phone_links_data:
            print(f"  - {phone_link[1]} -> Account {phone_link[0]}")
    
    def reset_database(self):
        """Reset database (drop all tables and recreate)"""
        db.drop_all()
        db.create_all()
        self.create_sample_data()
        print("✓ Database reset successfully")
    
    def get_database_stats(self):
        """Get database statistics"""
        stats = {
            'users': User.query.count(),
            'accounts': Account.query.count(),
            'phone_links': PhoneLink.query.count(),
            'sinpe_subscriptions': SinpeSubscription.query.count(),
            'transactions': Transaction.query.count()
        }
        return stats
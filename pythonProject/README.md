# SINPE Banking System - Python Implementation

A comprehensive Python-based banking system that replicates the functionality of a TypeScript/Node.js SINPE (Costa Rican payment system) project. The system features a terminal-based interface with Flask API backend.

## Features

- **Terminal UI**: Rich terminal interface with colorful menus and interactive forms
- **REST API**: Complete Flask-based API with all SINPE endpoints
- **Database**: SQLite database with SQLAlchemy ORM
- **SINPE Transfers**: Phone-based and account-based transfers with HMAC verification
- **User Management**: Complete user authentication and account management
- **Phone Links**: Link phone numbers to bank accounts for SINPE transfers
- **Transaction History**: Complete transaction tracking and history
- **Admin Panel**: Database management and statistics

## Quick Start

1. **Install Dependencies**:
   ```bash
   cd pythonProject
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

3. **Access the System**:
   - Terminal UI: Automatically launches
   - API Server: http://127.0.0.1:5000
   - Health Check: http://127.0.0.1:5000/health

## Project Structure

```
pythonProject/
├── main.py                 # Entry point with terminal UI
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── models/            # SQLAlchemy models
│   ├── routes/            # API route handlers
│   ├── services/          # Business logic
│   └── utils/             # Helper functions
├── config/
│   ├── banks.json         # Bank configuration
│   └── settings.py        # Application settings
├── database/
│   └── banking.db         # SQLite database (auto-created)
├── tests/
└── requirements.txt
```

## API Endpoints

### SINPE Routes
- `POST /api/sinpe-movil` - Handle SINPE transfers
- `GET /api/validate/{phone}` - Validate phone number in BCCR system
- `GET /api/sinpe/user-link/{username}` - Check if user has SINPE phone link
- `GET /api/sinpe/accounts/{username}` - Get user accounts with phone links

### User Management
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `GET /api/users/{id}` - Get specific user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Account Management
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Create new account
- `GET /api/accounts/{id}` - Get specific account
- `GET /api/accounts/{number}` - Get account by number
- `PUT /api/accounts/{id}/balance` - Update account balance
- `GET /api/users/{id}/accounts` - Get user accounts

### Transaction Management
- `GET /api/transactions` - List transactions (paginated)
- `POST /api/transactions` - Create new transaction
- `GET /api/transactions/{id}` - Get specific transaction
- `PUT /api/transactions/{id}/status` - Update transaction status
- `GET /api/accounts/{number}/transactions` - Get account transactions

### Phone Link Management
- `GET /api/phone-links` - List all phone links
- `POST /api/phone-links` - Create new phone link
- `GET /api/phone-links/{id}` - Get specific phone link
- `GET /api/phone-links/phone/{phone}` - Get phone link by phone
- `GET /api/phone-links/account/{account}` - Get phone link by account
- `PUT /api/phone-links/{id}` - Update phone link
- `DELETE /api/phone-links/{id}` - Delete phone link

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `GET /api/auth/check` - Check authentication status

## Sample Data

The system automatically creates sample data on first run:

### Sample Users (password: password123)
- `juan_perez` - Phone: 88887777
- `maria_rodriguez` - Phone: 88886666
- `carlos_gonzalez` - Phone: 88885555
- `ana_lopez` - Phone: 88884444

### Sample Accounts
- Multiple accounts with different balances
- Phone links for SINPE transfers
- BCCR subscription data

## SINPE Transfer Process

1. **Validation**: Receiver phone number is validated against BCCR system
2. **HMAC Verification**: All transfers require valid HMAC-MD5 signature
3. **Balance Check**: Sender account balance is verified
4. **Transfer Execution**: Funds are transferred between accounts
5. **Transaction Recording**: Complete transaction history is maintained

### HMAC Generation

The system uses HMAC-MD5 for transfer security:

```python
# For phone transfers
message = f"{secret},{phone},{timestamp},{transaction_id},{amount}"

# For account transfers  
message = f"{secret},{account_number},{timestamp},{transaction_id},{amount}"
```

## Configuration

### Bank Codes
- `152` - Local Bank (default)
- `151` - Banco Nacional
- `153` - Banco Popular

### Security
- HMAC Secret: `supersecreta123`
- Session timeout: 1 hour
- CORS enabled for development

## Terminal Interface

The rich terminal interface provides:

1. **Main Dashboard** - Account balances and recent transactions
2. **User Management** - Login, create users, manage accounts
3. **SINPE Transfers** - Interactive transfer interface
4. **Transaction History** - View and search transactions
5. **Phone Link Management** - Link phones to accounts
6. **Admin Panel** - Database management and statistics

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or run specific tests:

```bash
python tests/test_hmac.py
```

## Development

### Adding New Features

1. **Models**: Add new database models in `app/models/`
2. **Routes**: Create new API endpoints in `app/routes/`
3. **Services**: Add business logic in `app/services/`
4. **Terminal UI**: Extend terminal interface in `app/services/terminal_service.py`

### Database Management

The system provides several database management options:

- **Auto-initialization**: Database is created automatically on first run
- **Sample data**: Test data is created for development
- **Reset function**: Complete database reset via admin panel
- **Statistics**: View database statistics and health

## Security Features

- **HMAC Verification**: All transfers require valid signatures
- **Input Validation**: Comprehensive input validation and sanitization
- **SQL Injection Prevention**: SQLAlchemy ORM prevents SQL injection
- **Session Management**: Secure session handling
- **CORS Configuration**: Properly configured CORS for web clients

## Error Handling

The system provides comprehensive error handling:

- **API Errors**: Standardized JSON error responses
- **Database Errors**: Proper transaction rollback
- **Validation Errors**: Clear validation messages
- **Network Errors**: Graceful handling of external API failures

## Logging

All operations are logged with appropriate levels:

- **INFO**: Normal operations
- **WARNING**: Potential issues
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information

## Production Considerations

For production deployment:

1. **Database**: Switch to PostgreSQL or MySQL
2. **Security**: Use environment variables for secrets
3. **Logging**: Configure proper log rotation
4. **Monitoring**: Add health checks and metrics
5. **Scaling**: Consider using Gunicorn or uWSGI

## License

This project is for educational purposes and demonstrates SINPE banking system implementation in Python.
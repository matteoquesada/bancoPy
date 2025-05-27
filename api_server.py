from flask import Flask, request, jsonify
import logging
import uuid
from datetime import datetime
import hmac
import hashlib
import socket
import json
import ssl # For secure client connections to other banks

from db_handler import (
    init_db, add_account, delete_account, get_account, 
    update_balance, list_accounts, log_transaction, get_account_by_phone
)
from logging_config import setup_logging

app = Flask(__name__)

# Configure API_KEY for this bank (Banco A).
# IMPORTANT: Store securely (env variable, config file) in production.
THIS_BANK_API_KEY = b'secret_key_banco_A' # Used for signing outgoing messages
THIS_BANK_CODE = "BCA" # Example bank code for this server/bank
THIS_BANK_NAME = "Banco Central Alfa"

# Configuration for connecting to other banks (example, should be in a config file)
# In a real scenario, this would be a registry or discovery service.
OTHER_BANKS_CONFIG = {
    "BCB": {"host": "localhost", "port": 5002, "cert": "bank_b_cert.pem"}, # Example for Banco B
    "BCC": {"host": "otherbank.example.com", "port": 5001, "cert": "bank_c_cert.pem"}
}
# For client-side SSL, we need to trust the server's certificate.
# For self-signed certs, the server's cert (cert.pem) can be used as CA.
# In production, use proper CA-signed certificates.
# This CA_BUNDLE should contain all trusted CAs for inter-bank communication.
# For simplicity, we might use individual certs from OTHER_BANKS_CONFIG.

def generate_interbank_hmac(data_dict):
    """Generates HMAC for outgoing inter-bank messages."""
    try:
        raw_parts = [
            data_dict['sender']['account_number'],
            data_dict['timestamp'],
            data_dict['transaction_id'],
            str(data_dict['amount']['value'])
        ]
        raw = "|".join(raw_parts)
        return hmac.new(THIS_BANK_API_KEY, raw.encode(), hashlib.md5).hexdigest()
    except KeyError as e:
        logging.error(f"HMAC generation failed for outgoing message: Missing key {e}.")
        raise ValueError(f"Missing data for HMAC generation: {e}")


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
        
    acc_number = data.get("account_number")
    nombre = data.get("nombre")
    saldo_str = data.get("saldo", "0.0")
    phone_number = data.get("phone_number") # Optional for SINPE

    if not acc_number or not nombre:
        return jsonify({"error": "Faltan datos requeridos (account_number, nombre)"}), 400
    
    try:
        saldo = float(saldo_str)
    except ValueError:
        return jsonify({"error": "Saldo inválido, debe ser un número."}), 400

    if add_account(acc_number, nombre, saldo, phone_number):
        log_transaction(
            transaction_type='account_created_api',
            amount=saldo,
            currency='local_currency', # Assuming local currency
            status='completed',
            to_account_number=acc_number,
            description=f"Cuenta registrada via API. Tel: {phone_number if phone_number else 'N/A'}"
        )
        return jsonify({"message": "Cuenta registrada", "account_number": acc_number}), 201
    else:
        return jsonify({"error": "La cuenta o número de teléfono ya existe o datos inválidos"}), 400

@app.route('/account/<account_number>', methods=['GET'])
def get_account_details(account_number):
    account = get_account(account_number)
    if account:
        return jsonify(account), 200
    else:
        return jsonify({"error": "Cuenta no encontrada"}), 404

@app.route('/delete/<account_number>', methods=['DELETE'])
def delete(account_number):
    # Add more checks here, e.g., ensure balance is zero, or special auth
    account = get_account(account_number)
    if not account:
         return jsonify({"error": "Cuenta no encontrada"}), 404
    
    if account['saldo'] != 0: # Example business rule
        return jsonify({"error": "La cuenta debe tener saldo cero para ser eliminada"}), 400

    if delete_account(account_number):
        log_transaction(
            transaction_type='account_deleted_api',
            amount=0, currency='local_currency', status='completed',
            from_account_number=account_number, description="Cuenta eliminada via API"
        )
        return jsonify({"message": "Cuenta eliminada"})
    else:
        # This case should ideally not be reached if get_account found it
        return jsonify({"error": "Error al eliminar cuenta o no encontrada"}), 500


@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400
    acc = data.get("account_number")
    monto_str = data.get("monto")

    if not acc or monto_str is None:
        return jsonify({"error": "Faltan datos (account_number, monto)"}), 400
    try:
        monto = float(monto_str)
        if monto <= 0:
            return jsonify({"error": "Monto debe ser positivo"}), 400
    except ValueError:
        return jsonify({"error": "Monto inválido"}), 400

    cuenta = get_account(acc)
    if not cuenta:
        return jsonify({"error": "Cuenta no encontrada"}), 404
    
    nuevo_saldo = cuenta['saldo'] + monto
    update_balance(acc, nuevo_saldo)
    log_transaction(
        transaction_type='deposit_api',
        amount=monto, currency=data.get("currency", "CRC"), status='completed',
        to_account_number=acc, description="Depósito via API"
    )
    return jsonify({"message": "Deposito realizado", "nuevo_saldo": nuevo_saldo})


@app.route('/cashout', methods=['POST']) # Renamed from 'withdraw' for clarity if 'withdraw' is used elsewhere
def cashout():
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400
    acc = data.get("account_number")
    monto_str = data.get("monto")

    if not acc or monto_str is None:
        return jsonify({"error": "Faltan datos (account_number, monto)"}), 400
    try:
        monto = float(monto_str)
        if monto <= 0:
            return jsonify({"error": "Monto debe ser positivo"}), 400
    except ValueError:
        return jsonify({"error": "Monto inválido"}), 400

    cuenta = get_account(acc)
    if not cuenta:
        return jsonify({"error": "Cuenta no encontrada"}), 404
    
    if cuenta['saldo'] < monto:
        log_transaction(
            transaction_type='cashout_api_failed_funds',
            amount=monto, currency=data.get("currency", "CRC"), status='failed',
            from_account_number=acc, description="Retiro via API - Fondos insuficientes"
        )
        return jsonify({"error": "Fondos insuficientes"}), 400
    
    nuevo_saldo = cuenta['saldo'] - monto
    update_balance(acc, nuevo_saldo)
    log_transaction(
        transaction_type='cashout_api_completed',
        amount=monto, currency=data.get("currency", "CRC"), status='completed',
        from_account_number=acc, description="Retiro via API"
    )
    return jsonify({"message": "Retiro realizado", "nuevo_saldo": nuevo_saldo})


@app.route('/list_accounts', methods=['GET']) # Changed route from /list to be more descriptive
def list_all_accounts():
    return jsonify(list_accounts())

# ---- Inter-bank and SINPE Móvil Functionality ----

@app.route('/transfer_interbank', methods=['POST'])
def transfer_interbank_api():
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400

    sender_account_number = data.get("sender_account_number") # From this bank
    receiver_account_number = data.get("receiver_account_number")
    receiver_bank_code = data.get("receiver_bank_code")
    receiver_name = data.get("receiver_name")
    amount_str = data.get("amount")
    currency = data.get("currency", "CRC")
    description = data.get("description", "Transferencia interbancaria via API")

    if not all([sender_account_number, receiver_account_number, receiver_bank_code, receiver_name, amount_str]):
        return jsonify({"error": "Faltan datos requeridos para transferencia interbancaria"}), 400

    try:
        amount = float(amount_str)
        if amount <= 0: return jsonify({"error": "Monto debe ser positivo"}), 400
    except ValueError:
        return jsonify({"error": "Monto inválido"}), 400

    # 1. Check sender's balance in this bank
    sender_account = get_account(sender_account_number)
    if not sender_account:
        return jsonify({"error": f"Cuenta remitente {sender_account_number} no encontrada en este banco"}), 404
    
    if sender_account['saldo'] < amount:
        log_transaction(
            transaction_type='transfer_outgoing_api_failed_funds',
            amount=amount, currency=currency, status='failed',
            from_account_number=sender_account_number, to_account_number=receiver_account_number,
            description="Fondos insuficientes para transferencia interbancaria"
        )
        return jsonify({"error": "Fondos insuficientes en la cuenta remitente"}), 400

    # 2. Prepare inter-bank transaction message
    transaction_id = str(uuid.uuid4())
    interbank_payload = {
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "transaction_id": transaction_id,
        "sender": {
            "account_number": sender_account_number,
            "bank_code": THIS_BANK_CODE,
            "name": sender_account.get('nombre', THIS_BANK_NAME) # Use account name or bank name
        },
        "receiver": {
            "account_number": receiver_account_number,
            "bank_code": receiver_bank_code,
            "name": receiver_name
        },
        "amount": {"value": amount, "currency": currency},
        "description": description
    }
    try:
        interbank_payload['hmac_md5'] = generate_interbank_hmac(interbank_payload)
    except ValueError as e: # From generate_interbank_hmac if data is missing
         logging.error(f"Error generating HMAC for outgoing transfer: {e}")
         return jsonify({"error": f"Error interno al preparar la transferencia: {e}"}), 500


    # 3. Debit sender's account LOCALLY FIRST
    # IMPORTANT: This makes the local part of the transaction. If interbank send fails,
    # a rollback or compensation mechanism is needed in a real system.
    # For this example, we log the failure and the debit remains.
    new_sender_balance = sender_account['saldo'] - amount
    update_balance(sender_account_number, new_sender_balance)
    local_tx_id = log_transaction(
        transaction_type='transfer_outgoing_api_debited',
        amount=amount, currency=currency, status='pending_send', # Marked as pending send
        from_account_number=sender_account_number, to_account_number=receiver_account_number,
        description=f"Débito local para transferencia interbancaria a {receiver_bank_code}",
        external_transaction_id=transaction_id, hmac_signature_sent=interbank_payload['hmac_md5']
    )
    logging.info(f"Debited {amount} from {sender_account_number} for interbank transfer {transaction_id}. New balance: {new_sender_balance}")

    # 4. Send to other bank
    target_bank_config = OTHER_BANKS_CONFIG.get(receiver_bank_code)
    if not target_bank_config:
        # Log failure, and potentially revert the debit or mark for manual review
        log_transaction(
            transaction_type='transfer_outgoing_api_failed_config', amount=amount, currency=currency, status='failed',
            from_account_number=sender_account_number, to_account_number=receiver_account_number,
            notes=f"Configuración para banco receptor {receiver_bank_code} no encontrada. Débito realizado.",
            external_transaction_id=transaction_id
        )
        # For now, we don't auto-revert. This is a critical point for real systems.
        return jsonify({"error": f"Banco receptor {receiver_bank_code} no configurado. Transacción debitada localmente pero no enviada."}), 500
    
    # SSL Context for client
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = True # Enforce hostname check for security
    context.verify_mode = ssl.CERT_REQUIRED
    try:
        # Each bank might have its own cert, or use a common CA bundle
        # For simplicity, using the specific bank's cert as its CA cert (for self-signed)
        context.load_verify_locations(cafile=target_bank_config['cert'])
    except FileNotFoundError:
        logging.error(f"Cert file for {receiver_bank_code} ({target_bank_config['cert']}) not found.")
        # Log and potentially revert
        # ... (update transaction status to failed)
        return jsonify({"error": "Error de configuración SSL para banco receptor."}), 500
    except ssl.SSLError as e:
        logging.error(f"SSL config error for {receiver_bank_code}: {e}")
        return jsonify({"error": "Error de configuración SSL para banco receptor."}), 500

    response_from_other_bank = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
            with context.wrap_socket(raw_sock, server_hostname=target_bank_config['host']) as client_ssl:
                client_ssl.connect((target_bank_config['host'], target_bank_config['port']))
                client_ssl.sendall(json.dumps(interbank_payload).encode())
                response_from_other_bank = client_ssl.recv(4096).decode()
    except Exception as e:
        logging.exception(f"Error enviando transferencia interbancaria a {receiver_bank_code}:")
        # Update local transaction log to reflect send failure
        # c.execute("UPDATE transactions SET status=?, notes=? WHERE transaction_id=?", ('send_failed', str(e), local_tx_id))
        # (Simplified: not directly updating DB here, but should be done)
        return jsonify({"message": "Transferencia debitada localmente, pero falló el envío al otro banco.", "error": str(e)}), 502 # Bad Gateway

    if response_from_other_bank and response_from_other_bank.startswith("ACK"):
        # Update local transaction log to completed
        # c.execute("UPDATE transactions SET status=? WHERE transaction_id=?", ('completed', local_tx_id))
        logging.info(f"Transferencia interbancaria {transaction_id} completada. Respuesta: {response_from_other_bank}")
        return jsonify({"message": "Transferencia interbancaria enviada y confirmada.", "bank_response": response_from_other_bank, "transaction_id": transaction_id}), 200
    else:
        # Update local transaction log to reflect NACK or failure
        # c.execute("UPDATE transactions SET status=?, notes=? WHERE transaction_id=?", ('failed_at_receiver', response_from_other_bank, local_tx_id))
        logging.warning(f"Transferencia interbancaria {transaction_id} rechazada o fallida en banco receptor. Respuesta: {response_from_other_bank}")
        return jsonify({"message": "Transferencia debitada localmente, pero rechazada o fallida en banco receptor.", "bank_response": response_from_other_bank, "transaction_id": transaction_id}), 400 # Or 202 if processing


@app.route('/transfer_sinpe_movil', methods=['POST'])
def transfer_sinpe_movil_api():
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400

    sender_account_number = data.get("sender_account_number") # From this bank
    receiver_phone_number = data.get("receiver_phone_number")
    # For SINPE, bank code might be implicit or determined by phone prefix in a real system
    # Here, we might need it if the phone is not in our bank.
    receiver_bank_code = data.get("receiver_bank_code") # Optional, for external SINPE
    receiver_name = data.get("receiver_name", "Destinatario SINPE") # Often not known by sender
    amount_str = data.get("amount")
    currency = data.get("currency", "CRC")
    description = data.get("description", "Transferencia SINPE Móvil via API")

    if not all([sender_account_number, receiver_phone_number, amount_str]):
        return jsonify({"error": "Faltan datos (sender_account_number, receiver_phone_number, amount)"}), 400
    
    try:
        amount = float(amount_str)
        if amount <= 0: return jsonify({"error": "Monto debe ser positivo"}), 400
    except ValueError:
        return jsonify({"error": "Monto inválido"}), 400

    # 1. Check sender's balance
    sender_account = get_account(sender_account_number)
    if not sender_account:
        return jsonify({"error": f"Cuenta remitente {sender_account_number} no encontrada"}), 404
    if sender_account['saldo'] < amount:
        # Log this attempt
        return jsonify({"error": "Fondos insuficientes"}), 400

    # 2. Try to find receiver by phone in THIS bank
    local_receiver_account = get_account_by_phone(receiver_phone_number)

    if local_receiver_account:
        # Perform local transfer
        if sender_account_number == local_receiver_account['account_number']:
            return jsonify({"error": "No se puede transferir a la misma cuenta."}), 400

        # Debit sender
        update_balance(sender_account_number, sender_account['saldo'] - amount)
        # Credit receiver
        update_balance(local_receiver_account['account_number'], local_receiver_account['saldo'] + amount)
        
        log_transaction(
            transaction_type='transfer_sinpe_local_api',
            amount=amount, currency=currency, status='completed',
            from_account_number=sender_account_number, to_account_number=local_receiver_account['account_number'],
            to_phone_number=receiver_phone_number, description=description
        )
        return jsonify({
            "message": "Transferencia SINPE Móvil local completada.",
            "from_account": sender_account_number,
            "to_account": local_receiver_account['account_number'],
            "amount": amount
        }), 200
    else:
        # Simulate sending to another bank via SINPE Móvil (using interbank mechanism)
        if not receiver_bank_code:
            # In a real SINPE, the phone number itself might map to a bank.
            # Here, we require bank_code if phone is not local.
            return jsonify({"error": "Teléfono no encontrado localmente y código de banco receptor no provisto para SINPE externo."}), 400

        # Use the interbank transfer logic, but with phone number as primary receiver ID
        transaction_id = str(uuid.uuid4())
        interbank_payload = {
            "version": "1.0", "timestamp": datetime.utcnow().isoformat(), "transaction_id": transaction_id,
            "sender": {
                "account_number": sender_account_number, "bank_code": THIS_BANK_CODE,
                "name": sender_account.get('nombre', THIS_BANK_NAME)
            },
            "receiver": { # Key part for SINPE: send phone number
                "phone_number": receiver_phone_number,
                "account_number": None, # Explicitly null or omit if server handles it
                "bank_code": receiver_bank_code,
                "name": receiver_name
            },
            "amount": {"value": amount, "currency": currency}, "description": description
        }
        try:
            interbank_payload['hmac_md5'] = generate_interbank_hmac(interbank_payload)
        except ValueError as e:
             logging.error(f"Error generating HMAC for outgoing SINPE transfer: {e}")
             return jsonify({"error": f"Error interno al preparar la transferencia SINPE: {e}"}), 500
        
        # Debit sender's account (same critical point as regular interbank)
        update_balance(sender_account_number, sender_account['saldo'] - amount)
        log_transaction(
            transaction_type='transfer_sinpe_outgoing_api_debited',
            amount=amount, currency=currency, status='pending_send',
            from_account_number=sender_account_number, to_phone_number=receiver_phone_number,
            description=f"Débito local para SINPE Móvil a {receiver_bank_code} / {receiver_phone_number}",
            external_transaction_id=transaction_id, hmac_signature_sent=interbank_payload['hmac_md5']
        )

        # Send to other bank (re-uses logic structure from /transfer_interbank)
        target_bank_config = OTHER_BANKS_CONFIG.get(receiver_bank_code)
        if not target_bank_config:
            # Log, etc.
            return jsonify({"error": f"Banco receptor {receiver_bank_code} no configurado para SINPE. Transacción debitada localmente."}), 500
        
        # SSL Context setup (same as interbank)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        try:
            context.load_verify_locations(cafile=target_bank_config['cert'])
        except Exception as e:
            logging.error(f"SSL config error for SINPE to {receiver_bank_code}: {e}")
            return jsonify({"error": "Error de configuración SSL para banco receptor SINPE."}), 500

        response_from_other_bank = None
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
                with context.wrap_socket(raw_sock, server_hostname=target_bank_config['host']) as client_ssl:
                    client_ssl.connect((target_bank_config['host'], target_bank_config['port']))
                    client_ssl.sendall(json.dumps(interbank_payload).encode())
                    response_from_other_bank = client_ssl.recv(4096).decode()
        except Exception as e:
            logging.exception(f"Error enviando SINPE Móvil a {receiver_bank_code}:")
            # Update local transaction log to reflect send failure
            return jsonify({"message": "SINPE Móvil debitado localmente, pero falló el envío.", "error": str(e)}), 502

        if response_from_other_bank and response_from_other_bank.startswith("ACK"):
            # Update local transaction log
            logging.info(f"SINPE Móvil {transaction_id} completado. Respuesta: {response_from_other_bank}")
            return jsonify({"message": "SINPE Móvil enviado y confirmado.", "bank_response": response_from_other_bank, "transaction_id": transaction_id}), 200
        else:
            # Update local transaction log
            logging.warning(f"SINPE Móvil {transaction_id} rechazado/fallido. Respuesta: {response_from_other_bank}")
            return jsonify({"message": "SINPE Móvil debitado, pero rechazado/fallido en destino.", "bank_response": response_from_other_bank, "transaction_id": transaction_id}), 400


if __name__ == "__main__":
    setup_logging(log_file_name='banco_api_server.log')
    init_db() # Initialize database schema
    logging.info("Flask API server starting...")
    # For production, use a WSGI server like Gunicorn or uWSGI.
    # Example: gunicorn --bind 0.0.0.0:8000 api_server:app
    # SSL should be handled by a reverse proxy (Nginx, Apache) in front of the WSGI server.
    # Flask's built-in server is not suitable for production.
    app.run(host='0.0.0.0', port=8000, debug=True) # debug=False for production
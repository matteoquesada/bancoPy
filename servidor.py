import socket
import json
import hmac
import hashlib
import threading
import ssl
import logging
from db_handler import (
    init_db, add_account, delete_account, get_account, 
    update_balance, list_accounts, log_transaction, get_account_by_phone
)
from logging_config import setup_logging

# It's crucial to manage API_KEY securely, e.g., via environment variables or a config file.
# For this example, it remains hardcoded as per the original snippet.
API_KEY = b'secret_key_banco_A'  # Clave compartida (symmetric key)

# SSL Certificate files (generate these: openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem)
CERT_FILE = 'cert.pem'
KEY_FILE = 'key.pem'

def verificar_hmac(data, hash_recibido):
    # Ensure all required fields for HMAC are present
    try:
        raw_parts = [
            data['sender']['account_number'],
            data['timestamp'],
            data['transaction_id'],
            str(data['amount']['value']) # Ensure amount is string for consistent hashing
        ]
        raw = "|".join(raw_parts)
        h = hmac.new(API_KEY, raw.encode(), hashlib.md5).hexdigest()
        return h == hash_recibido
    except KeyError as e:
        logging.error(f"HMAC verification failed: Missing key {e} in data.")
        return False

def manejar_cliente(conn_ssl):
    datos_recibidos = b""
    try:
        while True: # Loop to receive all data, assuming messages are not excessively large
            chunk = conn_ssl.recv(4096)
            if not chunk:
                break
            datos_recibidos += chunk
            # Basic check if we might have a full JSON object (ends with '}')
            if datos_recibidos.strip().endswith(b'}'):
                break
        
        if not datos_recibidos:
            logging.warning("No data received from client.")
            return

        mensaje = json.loads(datos_recibidos.decode())
        logging.info(f"Received message: {mensaje}")

        hmac_valido = verificar_hmac(mensaje, mensaje.get('hmac_md5'))

        if not hmac_valido:
            log_transaction(
                transaction_type='transfer_incoming_failed_hmac',
                amount=mensaje.get('amount', {}).get('value', 0),
                currency=mensaje.get('amount', {}).get('currency', 'N/A'),
                status='failed',
                description='HMAC inválido',
                external_transaction_id=mensaje.get('transaction_id'),
                hmac_signature_received=mensaje.get('hmac_md5'),
                notes=f"Sender: {mensaje.get('sender')}"
            )
            conn_ssl.sendall(b'NACK: HMAC invalido')
            logging.warning("HMAC validation failed.")
            return

        receptor_identifier = mensaje['receiver'].get('account_number')
        if not receptor_identifier and mensaje['receiver'].get('phone_number'):
             # SINPE Movil: Resolve phone to account
            receptor_phone = mensaje['receiver']['phone_number']
            cuenta_receptor_obj = get_account_by_phone(receptor_phone)
            if cuenta_receptor_obj:
                receptor_identifier = cuenta_receptor_obj['account_number']
            else:
                log_transaction(
                    transaction_type='transfer_incoming_failed_account',
                    amount=mensaje['amount']['value'],
                    currency=mensaje['amount']['currency'],
                    status='failed',
                    to_phone_number=receptor_phone,
                    description='Cuenta (via telefono) inexistente',
                    external_transaction_id=mensaje['transaction_id'],
                    hmac_signature_received=mensaje['hmac_md5']
                )
                conn_ssl.sendall(b'NACK: Cuenta (via telefono) inexistente')
                logging.info(f"Receiver account for phone {receptor_phone} not found.")
                return
        
        if not receptor_identifier:
            log_transaction(
                transaction_type='transfer_incoming_failed_account',
                amount=mensaje['amount']['value'],
                currency=mensaje['amount']['currency'],
                status='failed',
                description='Identificador de receptor (cuenta/telefono) no provisto',
                external_transaction_id=mensaje['transaction_id'],
                hmac_signature_received=mensaje['hmac_md5']
            )
            conn_ssl.sendall(b'NACK: Identificador de receptor no provisto')
            logging.warning("Receiver identifier missing.")
            return

        monto = float(mensaje['amount']['value'])
        cuenta_receptor_obj = get_account(receptor_identifier)

        if not cuenta_receptor_obj:
            log_transaction(
                transaction_type='transfer_incoming_failed_account',
                amount=monto,
                currency=mensaje['amount']['currency'],
                status='failed',
                to_account_number=receptor_identifier,
                description='Cuenta receptora inexistente',
                external_transaction_id=mensaje['transaction_id'],
                hmac_signature_received=mensaje['hmac_md5']
            )
            conn_ssl.sendall(b'NACK: Cuenta inexistente')
            logging.info(f"Receiver account {receptor_identifier} not found.")
        # For incoming transfers (deposits), we generally don't check if the receiver's balance will be negative.
        # The "no negative balance" rule usually applies to withdrawals or outgoing payments from an account.
        # If a specific business rule requires rejecting deposits that don't bring an account to positive,
        # that logic would go here. For now, we accept all valid deposits.
        else:
            nuevo_saldo = cuenta_receptor_obj['saldo'] + monto
            update_balance(receptor_identifier, nuevo_saldo)
            log_transaction(
                transaction_type='transfer_incoming_completed',
                from_account_number=mensaje['sender']['account_number'],
                to_account_number=receptor_identifier,
                amount=monto,
                currency=mensaje['amount']['currency'],
                status='completed',
                description=mensaje.get('description', 'Transferencia interbancaria recibida'),
                external_transaction_id=mensaje['transaction_id'],
                hmac_signature_received=mensaje['hmac_md5']
            )
            conn_ssl.sendall(b'ACK: Transaccion completada')
            logging.info(f"[+] Nueva transacción: +{monto} a {receptor_identifier}. Saldo: {nuevo_saldo}")

    except json.JSONDecodeError:
        conn_ssl.sendall(b'NACK: Mensaje JSON malformado')
        logging.error("Failed to decode JSON message.")
    except ssl.SSLError as e:
        logging.error(f"SSL Error during client handling: {e}")
    except Exception as e:
        try:
            conn_ssl.sendall(f'NACK: Error interno del servidor {str(e)}'.encode())
        except Exception as send_e:
            logging.error(f"Failed to send error to client after initial error: {send_e}")
        logging.exception("Exception in manejar_cliente:")
    finally:
        conn_ssl.close()

def menu():
    while True:
        print("\n--- MENU CUENTAS (Servidor) ---")
        print("1. Registrar cuenta")
        print("2. Eliminar cuenta")
        print("3. Hacer depósito (local)")
        print("4. Hacer retiro (local)")
        print("5. Listar cuentas")
        print("6. Salir del menú")
        op = input("Seleccione opción: ")
        try:
            if op == "1":
                acc = input("Número de cuenta: ")
                nombre = input("Nombre: ")
                saldo = float(input("Saldo inicial: "))
                phone = input("Número de teléfono (opcional, presione Enter para omitir): ")
                phone_number = phone if phone else None
                if add_account(acc, nombre, saldo, phone_number):
                    logging.info(f"Cuenta registrada: {acc}, Nombre: {nombre}, Saldo: {saldo}, Tel: {phone_number}")
                    log_transaction('account_created', saldo, 'local_currency', 'completed', to_account_number=acc, description="Creación de cuenta")
                    print("Cuenta registrada.")
                else:
                    print("Error: cuenta o teléfono ya existe.")
            elif op == "2":
                acc = input("Número de cuenta a eliminar: ")
                # Consider logging this action too, perhaps with more details or a specific type
                if delete_account(acc):
                    logging.info(f"Cuenta eliminada: {acc}")
                    print("Cuenta eliminada.")
                else:
                    print("Cuenta no encontrada.")
            elif op == "3": # Depósito local
                acc = input("Número de cuenta: ")
                monto = float(input("Monto a depositar: "))
                if monto <= 0:
                    print("Monto debe ser positivo.")
                    continue
                cuenta = get_account(acc)
                if cuenta:
                    nuevo_saldo = cuenta['saldo'] + monto
                    update_balance(acc, nuevo_saldo)
                    log_transaction('deposit_local', monto, 'local_currency', 'completed', to_account_number=acc, description="Depósito local en ventanilla")
                    logging.info(f"Depósito local: {monto} a {acc}. Nuevo saldo: {nuevo_saldo}")
                    print("Depósito realizado.")
                else:
                    print("Cuenta no encontrada.")
            elif op == "4": # Retiro local
                acc = input("Número de cuenta: ")
                monto = float(input("Monto a retirar: "))
                if monto <= 0:
                    print("Monto debe ser positivo.")
                    continue
                cuenta = get_account(acc)
                if cuenta:
                    if cuenta['saldo'] >= monto:
                        nuevo_saldo = cuenta['saldo'] - monto
                        update_balance(acc, nuevo_saldo)
                        log_transaction('withdrawal_local', monto, 'local_currency', 'completed', from_account_number=acc, description="Retiro local en ventanilla")
                        logging.info(f"Retiro local: {monto} de {acc}. Nuevo saldo: {nuevo_saldo}")
                        print("Retiro realizado.")
                    else:
                        log_transaction('withdrawal_local', monto, 'local_currency', 'failed', from_account_number=acc, description="Retiro local fallido - fondos insuficientes")
                        print("Fondos insuficientes.")
                else:
                    print("Cuenta no encontrada.")
            elif op == "5":
                cuentas = list_accounts()
                if not cuentas:
                    print("No hay cuentas registradas.")
                for c in cuentas:
                    print(f"Nro: {c['account_number']}, Nombre: {c['nombre']}, Saldo: {c['saldo']}, Tel: {c.get('phone_number', 'N/A')}")
            elif op == "6":
                logging.info("Saliendo del menú de administración.")
                break
            else:
                print("Opción inválida.")
        except ValueError:
            print("Entrada inválida. Por favor ingrese un número para montos.")
        except Exception as e:
            logging.exception("Error en el menú:")
            print(f"Ocurrió un error: {e}")


def socket_server():
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain(CERT_FILE, KEY_FILE)
    except FileNotFoundError:
        logging.error(f"Error: Certificado SSL ({CERT_FILE} o {KEY_FILE}) no encontrado. Genere los certificados.")
        print(f"Error: Certificado SSL ({CERT_FILE} o {KEY_FILE}) no encontrado. Genere los certificados.")
        print("Ejemplo: openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor_sock:
        servidor_sock.bind(('0.0.0.0', 5001)) # Puerto para transferencias interbancarias
        servidor_sock.listen(5)
        logging.info("[*] Servidor socket (TLS) esperando conexiones para transferencias en el puerto 5001...")

        while True:
            try:
                conn, addr = servidor_sock.accept()
                logging.info(f"[+] Conexión de {addr}")
                # Wrap socket with SSL
                conn_ssl = context.wrap_socket(conn, server_side=True)
                # Handle client in a new thread
                client_thread = threading.Thread(target=manejar_cliente, args=(conn_ssl,))
                client_thread.daemon = True # Allows main program to exit even if threads are running
                client_thread.start()
            except ssl.SSLError as e:
                logging.error(f"SSL handshake error: {e} from {addr if 'addr' in locals() else 'unknown'}")
            except Exception as e:
                logging.exception(f"Error aceptando conexión:")


def main():
    setup_logging(log_file_name='banco_servidor.log')
    init_db()
    
    server_thread = threading.Thread(target=socket_server, daemon=True)
    server_thread.start()
    
    logging.info("[*] Servidor iniciado. Accediendo al menú de administración...")
    print("[*] Servidor iniciado. Accediendo al menú de administración...")
    menu()
    
    logging.info("[*] Cerrando aplicación servidor...")
    print("[*] Cerrando aplicación servidor...")

if __name__ == "__main__":
    main()
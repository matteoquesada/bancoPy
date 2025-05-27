import socket
import json
import uuid
from datetime import datetime
import hmac
import hashlib
import argparse
import ssl
import logging # Added logging
# import requests # This import seems unused in the provided snippet for 'transfer'

# It's crucial to manage API_KEY securely, e.g., via environment variables or a config file.
API_KEY = b'secret_key_banco_A' # Key for Banco A, assuming this client interacts with Banco A's server

# For client-side SSL, we need to trust the server's certificate.
# For self-signed certs, the server's cert (cert.pem) can be used as CA, or turn off hostname check for testing.
# In production, use proper CA-signed certificates.
CA_CERT_FILE = 'cert.pem' # Assuming server's cert is used as CA for self-signed setup

def generar_hmac(data):
    # Ensure all required fields for HMAC are present and in correct order
    try:
        raw_parts = [
            data['sender']['account_number'],
            data['timestamp'],
            data['transaction_id'],
            str(data['amount']['value']) # Ensure amount is string for consistent hashing
        ]
        raw = "|".join(raw_parts)
        return hmac.new(API_KEY, raw.encode(), hashlib.md5).hexdigest()
    except KeyError as e:
        logging.error(f"HMAC generation failed: Missing key {e} in data.")
        raise # Re-raise to indicate failure in preparing the message

def transfer(args):
    transaccion = {
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "transaction_id": str(uuid.uuid4()),
        "sender": {
            "account_number": args.sender,
            "bank_code": args.sender_bank,
            "name": args.sender_name
        },
        "receiver": { # Receiver can be account_number or phone_number for SINPE
            "account_number": args.receiver if not args.receiver_phone else None,
            "phone_number": args.receiver_phone if args.receiver_phone else None,
            "bank_code": args.receiver_bank,
            "name": args.receiver_name
        },
        "amount": {
            "value": args.amount,
            "currency": args.currency
        },
        "description": args.description
    }
    
    # Remove null receiver fields for cleaner JSON
    if transaccion["receiver"]["account_number"] is None:
        del transaccion["receiver"]["account_number"]
    if transaccion["receiver"]["phone_number"] is None:
        del transaccion["receiver"]["phone_number"]

    try:
        transaccion['hmac_md5'] = generar_hmac(transaccion)
    except Exception as e:
        print(f"Error preparing transaction: {e}")
        return

    # SSL Context for client
    # PROTOCOL_TLS_CLIENT requires server hostname verification and CA certs
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = True # Enforce hostname check
    context.verify_mode = ssl.CERT_REQUIRED
    
    # Load CA certificate to verify the server. For self-signed, this is server's cert.
    # In production, this would be the CA that signed the server's certificate.
    try:
        context.load_verify_locations(cafile=CA_CERT_FILE) 
    except FileNotFoundError:
        logging.error(f"CA certificate file '{CA_CERT_FILE}' not found. Cannot verify server.")
        print(f"Error: CA certificate file '{CA_CERT_FILE}' not found.")
        # Fallback for testing if CA cert is missing (INSECURE for production)
        # context.check_hostname = False
        # context.verify_mode = ssl.CERT_NONE
        # print("Warning: Server certificate will not be verified (CA_CERT_FILE not found).")
        return
    except ssl.SSLError as e:
        logging.error(f"SSL error loading CA cert: {e}")
        print(f"SSL error: {e}. Ensure '{CA_CERT_FILE}' is a valid certificate.")
        return


    # Use a raw socket first, then wrap it with SSL
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # server_hostname should match the CN or SAN in the server's certificate
    server_hostname = args.host # Assuming args.host is the FQDN used in server cert

    try:
        with context.wrap_socket(raw_socket, server_hostname=server_hostname) as cliente_ssl:
            cliente_ssl.connect((args.host, args.port))
            logging.info(f"Connected securely to {args.host}:{args.port}")
            
            cliente_ssl.sendall(json.dumps(transaccion).encode())
            logging.info(f"Sent transaction: {transaccion}")
            
            respuesta = cliente_ssl.recv(4096)
            print("Respuesta del servidor:", respuesta.decode())
            logging.info(f"Server response: {respuesta.decode()}")

    except socket.gaierror as e: # Address-related error
        print(f"Error de dirección: {e}. Verifique el host '{args.host}'.")
        logging.error(f"Address error for {args.host}: {e}")
    except ConnectionRefusedError:
        print(f"Conexión rechazada por el servidor en {args.host}:{args.port}.")
        logging.error(f"Connection refused by server at {args.host}:{args.port}.")
    except ssl.SSLCertVerificationError as e:
        print(f"Error de verificación de certificado SSL: {e}")
        print(f"Asegúrese que el servidor '{server_hostname}' usa un certificado válido y que '{CA_CERT_FILE}' es el CA correcto.")
        logging.error(f"SSL Certificate Verification Error for {server_hostname}: {e}")
    except ssl.SSLError as e: # Other SSL errors
        print(f"Error de SSL: {e}")
        logging.error(f"SSL Error: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        logging.exception("Unexpected error in transfer:")


def main():
    # Setup basic logging for the client
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Cliente para transferencias interbancarias seguras.")
    parser.add_argument('--host', default='localhost', help="Host del servidor bancario.")
    parser.add_argument('--port', type=int, default=5001, help="Puerto del servidor bancario.")
    
    parser.add_argument('--sender', required=True, help="Número de cuenta del remitente.")
    parser.add_argument('--sender_bank', required=True, help="Código del banco del remitente.")
    parser.add_argument('--sender_name', required=True, help="Nombre del remitente.")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--receiver', help="Número de cuenta del destinatario.")
    group.add_argument('--receiver_phone', help="Número de teléfono del destinatario (SINPE Móvil).")

    parser.add_argument('--receiver_bank', required=True, help="Código del banco del destinatario.")
    parser.add_argument('--receiver_name', required=True, help="Nombre del destinatario.")
    
    parser.add_argument('--amount', type=float, required=True, help="Monto de la transacción.")
    parser.add_argument('--currency', default="CRC", help="Moneda de la transacción.")
    parser.add_argument('--description', default="Transferencia interbancaria", help="Descripción de la transacción.")
    
    args = parser.parse_args()
    transfer(args)

if __name__ == "__main__":
    main()
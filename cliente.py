import socket
import json
import uuid
from datetime import datetime
import hmac
import hashlib
import argparse
import requests

API_KEY = b'secret_key_banco_A'

def generar_hmac(data):
    raw = f"{data['sender']['account_number']}|{data['timestamp']}|{data['transaction_id']}|{data['amount']['value']}"
    return hmac.new(API_KEY, raw.encode(), hashlib.md5).hexdigest()

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
        "receiver": {
            "account_number": args.receiver,
            "bank_code": args.receiver_bank,
            "name": args.receiver_name
        },
        "amount": {
            "value": args.amount,
            "currency": args.currency
        },
        "description": args.description
    }
    transaccion['hmac_md5'] = generar_hmac(transaccion)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
        cliente.connect((args.host, args.port))
        cliente.sendall(json.dumps(transaccion).encode())
        respuesta = cliente.recv(4096)
        print("Respuesta:", respuesta.decode())

def account_op(args):
    url = f"http://{args.api_host}:{args.api_port}"
    if args.action == "register":
        data = {
            "account_number": args.account,
            "nombre": args.nombre,
            "saldo": args.saldo
        }
        r = requests.post(f"{url}/register", json=data)
        print(r.json())
    elif args.action == "delete":
        r = requests.delete(f"{url}/delete/{args.account}")
        print(r.json())
    elif args.action == "deposit":
        data = {"account_number": args.account, "monto": args.monto}
        r = requests.post(f"{url}/deposit", json=data)
        print(r.json())
    elif args.action == "cashout":
        data = {"account_number": args.account, "monto": args.monto}
        r = requests.post(f"{url}/cashout", json=data)
        print(r.json())
    elif args.action == "list":
        r = requests.get(f"{url}/list")
        print(r.json())

def main():
    parser = argparse.ArgumentParser(description="Cliente BancoPy")
    subparsers = parser.add_subparsers(dest="command")

    # Transferencia
    p_transfer = subparsers.add_parser("transfer", help="Realizar transferencia")
    p_transfer.add_argument("--host", default="127.0.0.1")
    p_transfer.add_argument("--port", type=int, default=5000)
    p_transfer.add_argument("--sender", required=True)
    p_transfer.add_argument("--sender_bank", default="BBVA")
    p_transfer.add_argument("--sender_name", default="Juan Pérez")
    p_transfer.add_argument("--receiver", required=True)
    p_transfer.add_argument("--receiver_bank", default="SANTANDER")
    p_transfer.add_argument("--receiver_name", default="Ana Gómez")
    p_transfer.add_argument("--amount", type=float, required=True)
    p_transfer.add_argument("--currency", default="EUR")
    p_transfer.add_argument("--description", default="Pago de factura")
    p_transfer.set_defaults(func=transfer)

    # Operaciones de cuenta
    p_acc = subparsers.add_parser("account", help="Operaciones de cuenta")
    p_acc.add_argument("--api_host", default="127.0.0.1")
    p_acc.add_argument("--api_port", type=int, default=8000)
    p_acc.add_argument("action", choices=["register", "delete", "deposit", "cashout", "list"])
    p_acc.add_argument("--account")
    p_acc.add_argument("--nombre")
    p_acc.add_argument("--saldo", type=float, default=0.0)
    p_acc.add_argument("--monto", type=float)
    p_acc.set_defaults(func=account_op)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

import socket
import json
import hmac
import hashlib
import threading
from db_handler import init_db, add_account, delete_account, get_account, update_balance, list_accounts

API_KEY = b'secret_key_banco_A'  # clave compartida entre bancos

def verificar_hmac(data, hash_recibido):
    raw = f"{data['sender']['account_number']}|{data['timestamp']}|{data['transaction_id']}|{data['amount']['value']}"
    h = hmac.new(API_KEY, raw.encode(), hashlib.md5).hexdigest()
    return h == hash_recibido

def manejar_cliente(conn):
    datos = conn.recv(4096)
    try:
        mensaje = json.loads(datos.decode())
        valido = verificar_hmac(mensaje, mensaje['hmac_md5'])

        if not valido:
            conn.sendall(b'NACK: HMAC invalido')
            return

        receptor = mensaje['receiver']['account_number']
        monto = float(mensaje['amount']['value'])

        cuenta = get_account(receptor)
        if not cuenta:
            conn.sendall(b'NACK: Cuenta inexistente')
        elif cuenta['saldo'] + monto < 0:
            conn.sendall(b'NACK: Saldo negativo')
        else:
            update_balance(receptor, cuenta['saldo'] + monto)
            print(f"[+] Nueva transacción: +{monto} a {receptor}")
            conn.sendall(b'ACK: Transaccion completada')

    except Exception as e:
        conn.sendall(f'NACK: Error {str(e)}'.encode())

def menu():
    while True:
        print("\n--- MENU CUENTAS ---")
        print("1. Registrar cuenta")
        print("2. Eliminar cuenta")
        print("3. Hacer depósito")
        print("4. Hacer retiro")
        print("5. Listar cuentas")
        print("6. Salir del menú")
        op = input("Seleccione opción: ")
        if op == "1":
            acc = input("Número de cuenta: ")
            nombre = input("Nombre: ")
            saldo = float(input("Saldo inicial: "))
            if add_account(acc, nombre, saldo):
                print("Cuenta registrada.")
            else:
                print("Error: cuenta ya existe.")
        elif op == "2":
            acc = input("Número de cuenta a eliminar: ")
            if delete_account(acc):
                print("Cuenta eliminada.")
            else:
                print("Cuenta no encontrada.")
        elif op == "3":
            acc = input("Número de cuenta: ")
            monto = float(input("Monto a depositar: "))
            cuenta = get_account(acc)
            if cuenta:
                update_balance(acc, cuenta['saldo'] + monto)
                print("Depósito realizado.")
            else:
                print("Cuenta no encontrada.")
        elif op == "4":
            acc = input("Número de cuenta: ")
            monto = float(input("Monto a retirar: "))
            cuenta = get_account(acc)
            if cuenta:
                if cuenta['saldo'] >= monto:
                    update_balance(acc, cuenta['saldo'] - monto)
                    print("Retiro realizado.")
                else:
                    print("Fondos insuficientes.")
            else:
                print("Cuenta no encontrada.")
        elif op == "5":
            cuentas = list_accounts()
            for c in cuentas:
                print(f"{c['account_number']}: {c['nombre']} - Saldo: {c['saldo']}")
        elif op == "6":
            break
        else:
            print("Opción inválida.")

def socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind(('0.0.0.0', 5001))  # Puerto 5000
        servidor.listen(1)
        print("[*] Esperando conexiones para transferencias...")

        while True:
            conn, addr = servidor.accept()
            print(f"[+] Conexión de {addr}")
            manejar_cliente(conn)
            conn.close()

def main():
    # Initialize database
    init_db()
    
    # Start socket server in a separate thread
    server_thread = threading.Thread(target=socket_server, daemon=True)
    server_thread.start()
    
    # Run menu in main thread
    print("[*] Servidor iniciado. Accediendo al menú de administración...")
    menu()
    
    print("[*] Cerrando aplicación...")

if __name__ == "__main__":
    main()

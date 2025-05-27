from flask import Flask, request, jsonify
from db_handler import init_db, add_account, delete_account, get_account, update_balance, list_accounts

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    acc = data.get("account_number")
    nombre = data.get("nombre")
    saldo = float(data.get("saldo", 0.0))
    if not acc or not nombre:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    if add_account(acc, nombre, saldo):
        return jsonify({"message": "Cuenta registrada"}), 201
    else:
        return jsonify({"error": "La cuenta ya existe"}), 400

@app.route('/delete/<account_number>', methods=['DELETE'])
def delete(acc_number):
    if delete_account(acc_number):
        return jsonify({"message": "Cuenta eliminada"})
    else:
        return jsonify({"error": "Cuenta no encontrada"}), 404

@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    acc = data.get("account_number")
    monto = float(data.get("monto", 0.0))
    cuenta = get_account(acc)
    if not cuenta:
        return jsonify({"error": "Cuenta no encontrada"}), 404
    update_balance(acc, cuenta['saldo'] + monto)
    return jsonify({"message": "Deposito realizado", "saldo": cuenta['saldo'] + monto})

@app.route('/cashout', methods=['POST'])
def cashout():
    data = request.get_json()
    acc = data.get("account_number")
    monto = float(data.get("monto", 0.0))
    cuenta = get_account(acc)
    if not cuenta:
        return jsonify({"error": "Cuenta no encontrada"}), 404
    if cuenta['saldo'] < monto:
        return jsonify({"error": "Fondos insuficientes"}), 400
    update_balance(acc, cuenta['saldo'] - monto)
    return jsonify({"message": "Retiro realizado", "saldo": cuenta['saldo'] - monto})

@app.route('/list', methods=['GET'])
def list_all():
    return jsonify(list_accounts())

if __name__ == "__main__":
    init_db()
    app.run(port=8000, debug=True)
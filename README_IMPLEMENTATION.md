# Implementation Summary: Inter-Bank System Enhancements

This document outlines the changes made to the `bancoPy` system to meet the specified technical requirements.

## 1. Overview of Changes

The system has been significantly enhanced with a focus on security, auditable logging, and new functionalities like API-driven inter-bank transfers and a basic SINPE Móvil simulation.

*   **Database (`db_handler.py`):**
    *   The `cuentas` table now includes an optional `phone_number` field (unique) for SINPE Móvil.
    *   A new `transactions` table provides a comprehensive audit trail for all financial operations (creations, deposits, withdrawals, local transfers, inter-bank transfers).
    *   New helper functions: `log_transaction`, `get_account_by_phone`.

*   **Socket Server (`servidor.py`):**
    *   Inter-bank communication (port 5001) is now secured using **TLS/SSL**.
    *   All incoming inter-bank transactions (valid or invalid HMAC, account found/not found) are logged to the `transactions` table.
    *   Account management operations via the console menu (add account, deposit, withdrawal) are also logged.
    *   Can now receive SINPE Móvil transfers where the receiver is identified by phone number.

*   **Socket Client (`cliente.py`):**
    *   The command-line client for initiating inter-bank transfers now uses **TLS/SSL** for secure communication.
    *   Can send SINPE Móvil transfers by specifying `--receiver_phone`.

*   **API Server (`api_server.py` - Flask):**
    *   This is now the primary interface for most banking operations.
    *   **Endpoints:**
        *   `/register`: Account registration, now supports optional `phone_number`.
        *   `/account/<account_number>`: Get account details.
        *   `/delete/<account_number>`: Delete account (with basic checks).
        *   `/deposit`: Make a deposit to a local account.
        *   `/cashout`: Make a withdrawal from a local account.
        *   `/list_accounts`: List all local accounts.
        *   `/transfer_interbank`: New endpoint to initiate secure (HMAC + TLS) inter-bank transfers to other configured banks. Includes sender balance check.
        *   `/transfer_sinpe_movil`: New endpoint for SINPE Móvil. If the phone number is local, it performs an internal transfer. If external (and `receiver_bank_code` is provided), it uses the inter-bank transfer mechanism, sending the phone number as the receiver identifier.
    *   **Transaction Logging:** All operations are logged to the `transactions` table.
    *   **Security:**
        *   Uses HMAC for signing outgoing inter-bank messages.
        *   Initiates TLS/SSL secured connections when acting as a client to other banks.
        *   Includes checks for sufficient funds before debiting for transfers.

*   **Logging (`logging_config.py`):**
    *   A basic file and console logging setup is introduced for better traceability of application events.

## 2. Fulfillment of Technical Requirements

Here's how the implemented changes address the specified requirements:

### 2.1. Infraestructura de Red:

*   **Usar protocolos de enrutamiento (OSPF, EIGRP) para interconectar routers:**
    *   This is an **infrastructure-level requirement** and is outside the scope of the application code. It would be configured on network devices (routers) connecting different bank networks.
*   **Implementar servidores (Linux/Windows) para gestionar cuentas y transacciones:**
    *   `servidor.py` (socket-based) and `api_server.py` (Flask HTTP API) act as application servers managing accounts and transactions. They are platform-agnostic Python applications and can run on Linux or Windows with Python installed.

### 2.2. Protocolo de Comunicación (Inter-Bank):

*   **Definir un formato estándar para mensajes (ejm: JSON/XML) con: Origen/Destino (IP o ID de banco), monto, fecha, ID de transacción, autenticación (API keys, firmas digitales):**
    *   **Format:** JSON is used for all inter-bank messages (see `cliente.py`, `servidor.py`, and `api_server.py`'s inter-bank logic).
    *   **Contents:**
        *   `version`: Protocol version.
        *   `timestamp`: ISO format UTC timestamp (fecha).
        *   `transaction_id`: Unique UUID (ID de transacción).
        *   `sender`: Contains `account_number`, `bank_code` (ID de banco), `name` (Origen).
        *   `receiver`: Contains `account_number` or `phone_number`, `bank_code` (ID de banco), `name` (Destino).
        *   `amount`: Contains `value` (monto) and `currency`.
        *   `description`: Transaction description.
        *   `hmac_md5`: HMAC-MD5 signature for message authentication (Autenticación using API keys implicitly).
*   **Mecanismo de confirmación (ACK/NACK):**
    *   The socket server (`servidor.py`) responds with `ACK: Transaccion completada` or `NACK: <reason>` messages.
    *   The client logic (in `cliente.py` and `api_server.py`) processes these responses.

### 2.3. Funcionalidades Obligatorias:

*   **Transferencias interbancarias en tiempo real:**
    *   Implemented via:
        *   `cliente.py` (CLI tool).
        *   `api_server.py` new endpoint `/transfer_interbank`.
    *   Both use secure (TLS + HMAC) JSON messages and handle ACK/NACK responses.
*   **Registro de transacciones (logs auditables):**
    *   A dedicated `transactions` table in `cuentas_banco.db` (see `db_handler.py`) logs details of all significant operations (account creation, deposits, withdrawals, local transfers, inter-bank transfers initiated/received, status, HMACs, etc.).
    *   Application-level logging to files (e.g., `banco_api_server.log`, `banco_servidor.log`) is also set up via `logging_config.py`.
*   **SINPE Móvil básico: Transferencias usando “número de teléfono” (simulado):**
    *   The `cuentas` table now supports `phone_number`.
    *   `api_server.py` has a `/transfer_sinpe_movil` endpoint:
        *   If the receiver's phone is in the local bank's DB, an internal transfer occurs.
        *   If not local, it can initiate an inter-bank transfer (if `receiver_bank_code` is provided), sending the `phone_number` in the receiver block of the inter-bank message. The recipient bank's `servidor.py` is updated to handle lookups by phone number.
    *   `cliente.py` can also send transfers using `--receiver_phone`.

### 2.4. Seguridad:

*   **Autenticación mutua entre bancos (ejm: HMAC MD5):**
    *   HMAC-MD5 is used to sign and verify inter-bank messages. The `API_KEY` (`secret_key_banco_A`) acts as a shared secret.
    *   `generar_hmac` and `verificar_hmac` functions handle this.
    *   **Note:** While HMAC provides message authentication and integrity, true "mutua" authentication at the transport layer is provided by TLS/SSL with client and server certificates (though the current TLS setup is server-auth primarily, client-auth can be added).
*   **Cifrado de datos (ejm: TLS/SSL):**
    *   **Inter-bank socket communication:** `servidor.py` and `cliente.py` (and `api_server.py` when acting as a client) now use `ssl.wrap_socket` to enforce TLS encryption. This requires SSL certificates (`cert.pem`, `key.pem`).
    *   **API Server (Flask):** The provided code runs Flask's development server. For production, it's **critical** to deploy `api_server.py` behind a proper WSGI server (like Gunicorn) and a reverse proxy (like Nginx or Apache) that handles TLS/SSL termination for HTTPS.
*   **Prevención de fraudes (ejm: no permitir saldos negativos):**
    *   The `api_server.py` (`/cashout`, `/transfer_interbank`, `/transfer_sinpe_movil`) and `servidor.py` (menu withdrawal) check if the sender's account has sufficient funds *before* debiting the account and proceeding with the withdrawal or transfer.
    *   Transactions are logged, which helps in auditing and detecting fraudulent patterns.

## 3. Setup and Important Notes

*   **Python Version:** Assumed Python 3.7+
*   **Dependencies:** `Flask` (for `api_server.py`). Install with `pip install Flask`.
*   **Database Initialization:** Run `init_db()` (e.g., by starting `servidor.py` or `api_server.py` once) to create `cuentas_banco.db` with the necessary tables.
*   **SSL Certificates:**
    *   For TLS to work, you need `cert.pem` (certificate) and `key.pem` (private key) in the same directory as `servidor.py` and `cliente.py` (or `api_server.py` if it needs to connect to a bank that uses these specific cert names for its CA).
    *   Generate self-signed certificates for testing:
        ```bash
        openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem -subj "/CN=localhost"
        ```
        Replace `/CN=localhost` with the actual hostname if testing across different machines.
    *   The `cliente.py` and `api_server.py` (when acting as a client) use `cert.pem` as the CA certificate (`CA_CERT_FILE` or `target_bank_config['cert']`) to verify the server. This is typical for self-signed setups. In production, use certificates signed by a trusted Certificate Authority (CA).
*   **API Keys (`API_KEY`, `THIS_BANK_API_KEY`):**
    *   These are currently hardcoded. **In a production environment, these MUST be stored securely**, e.g., as environment variables or in a secure configuration management system.
*   **Inter-Bank Configuration (`OTHER_BANKS_CONFIG` in `api_server.py`):**
    *   This dictionary simulates a bank registry. In a real system, this would be more dynamic or come from a shared discovery service. Ensure hostnames, ports, and certificate paths are correct for your test environment.
*   **Transaction Rollback/Compensation for Inter-Bank Transfers:**
    *   In `api_server.py`, when an inter-bank transfer is initiated, the sender's account is debited *before* attempting to send the message to the other bank. If the send fails or the other bank NACKs, the current implementation logs this, but the debit remains.
    *   **This is a simplification.** A robust production system would require a compensation mechanism (e.g., automatically re-crediting the sender's account) or a manual reconciliation process for such failed transactions to ensure data consistency (atomicity). This is a complex topic (Two-Phase Commit, Sagas, etc.) beyond the current scope.
*   **Flask Production Deployment:**
    *   As mentioned, do not use `app.run(debug=True)` for production. Use Gunicorn/uWSGI and Nginx/Apache for proper performance, security, and SSL handling for the API.

## 4. Further Considerations (Out of Scope for Current Changes)

*   **More Sophisticated Key Management:** For multiple banks, managing symmetric shared secrets (API keys) can be complex. Asymmetric cryptography (digital signatures with public/private key pairs) could be an alternative for message authentication.
*   **Central Bank / Clearing House:** Real inter-bank systems often involve a central entity.
*   **Rate Limiting and Advanced Fraud Detection:** For API security and stability.
*   **Asynchronous Task Queues:** For handling inter-bank communication or other long-running tasks without blocking API responses (e.g., Celery).
*   **Detailed API Documentation:** Using tools like Swagger/OpenAPI for the Flask API.

This revised system provides a more robust and feature-rich foundation for your inter-bank application.
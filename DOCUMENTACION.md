


```

# Proyecto SINPE Distribuido  
**Simulación de Transferencias Interbancarias y SINPE Móvil en Python**

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura General](#arquitectura-general)
3. [Estructura del Código](#estructura-del-código)
4. [Base de Datos](#base-de-datos)
5. [Seguridad](#seguridad)
6. [Protocolo de Comunicación](#protocolo-de-comunicación)
7. [API REST (api_server.py)](#api-rest-apispy)
8. [Servidor de Sockets (servidor.py)](#servidor-de-sockets-servidorpy)
9. [Cliente de Transferencias (cliente.py)](#cliente-de-transferencias-clientepy)
10. [Configuración y Despliegue](#configuración-y-despliegue)
11. [Pruebas y Ejemplos](#pruebas-y-ejemplos)
12. [Consideraciones y Mejoras Futuras](#consideraciones-y-mejoras-futuras)

---

## Introducción

Este proyecto simula el funcionamiento del sistema **SINPE** de Costa Rica, permitiendo la integración de múltiples bancos (cada uno representado por un grupo) bajo un protocolo común para transferencias interbancarias y SINPE Móvil.  
Incluye seguridad (TLS/SSL, HMAC), registro auditable de transacciones y una API REST para operaciones bancarias.

---

## Arquitectura General

- **Cada grupo/banco** ejecuta su propio servidor y base de datos.
- **Comunicación interbancaria**: Se realiza mediante sockets seguros (TLS/SSL) y mensajes JSON autenticados con HMAC.
- **API REST**: Permite gestionar cuentas, depósitos, retiros y transferencias (incluyendo SINPE Móvil).
- **Registro de transacciones**: Todas las operaciones quedan auditadas en la base de datos.

### Diagrama Simplificado

```mermaid
graph TD
    ClienteAPI[Cliente API (curl/Postman)]
    API[API REST (Flask)]
    DB[(Base de Datos SQLite)]
    SocketSrv[Servidor de Sockets (TLS)]
    OtroBanco[Otro Banco (Socket TLS)]
    ClienteAPI -->|HTTP/JSON| API
    API -->|SQLite| DB
    API -->|Socket TLS + JSON| OtroBanco
    OtroBanco -->|Socket TLS + JSON| API
    SocketSrv -->|Socket TLS + JSON| OtroBanco
```

---

## Estructura del Código

- **api_server.py**: Servidor Flask con endpoints REST para todas las operaciones bancarias.
- **servidor.py**: Servidor de sockets para recibir transferencias interbancarias (TLS/SSL).
- **cliente.py**: Cliente de línea de comandos para enviar transferencias interbancarias.
- **db_handler.py**: Funciones para interactuar con la base de datos (cuentas, transacciones, etc).
- **logging_config.py**: Configuración centralizada de logs.
- **cert.pem / key.pem**: Certificados SSL para cifrado.
- **/logs/**: Carpeta donde se almacenan los logs de la aplicación.
- **/docs/README.md**: Este documento.

---

## Base de Datos

- **SQLite** (`cuentas_banco.db`)
- **Tablas principales**:
  - `cuentas`:  
    - `account_number` (PK), `nombre`, `saldo`, `phone_number` (único, para SINPE Móvil)
  - `transactions`:  
    - `transaction_id` (PK), `timestamp`, `transaction_type`, `from_account_number`, `to_account_number`, `to_phone_number`, `amount`, `currency`, `status`, `description`, `external_transaction_id`, `hmac_signature_sent`, `hmac_signature_received`, `notes`

**Ejemplo de registro de transacción:**
```json
{
  "transaction_id": "uuid",
  "timestamp": "2024-06-01T12:34:56Z",
  "transaction_type": "transfer_outgoing_api_debited",
  "from_account_number": "12345",
  "to_account_number": "67890",
  "amount": 100.0,
  "currency": "CRC",
  "status": "pending_send",
  "description": "Débito local para transferencia interbancaria a BCB",
  "external_transaction_id": "uuid",
  "hmac_signature_sent": "abc123...",
  "hmac_signature_received": null,
  "notes": null
}
```

---

## Seguridad

- **TLS/SSL**: Todas las comunicaciones interbancarias usan sockets cifrados.
- **HMAC-MD5**: Cada mensaje interbancario lleva una firma HMAC para autenticación mutua.
- **Prevención de fraudes**:  
  - No se permite transferir ni retirar si el saldo es insuficiente.
  - Todas las operaciones quedan registradas para auditoría.
- **API Keys**: Las claves secretas para HMAC deben almacenarse de forma segura (en variables de entorno en producción).

---

## Protocolo de Comunicación

- **Formato**: JSON
- **Campos principales**:
  - `version`, `timestamp`, `transaction_id`
  - `sender`: `{account_number, bank_code, name}`
  - `receiver`: `{account_number | phone_number, bank_code, name}`
  - `amount`: `{value, currency}`
  - `description`
  - `hmac_md5`: Firma HMAC del mensaje

**Ejemplo de mensaje interbancario:**
```json
{
  "version": "1.0",
  "timestamp": "2024-06-01T12:34:56Z",
  "transaction_id": "uuid",
  "sender": {"account_number": "12345", "bank_code": "BCA", "name": "Juan"},
  "receiver": {"account_number": "67890", "bank_code": "BCB", "name": "Maria"},
  "amount": {"value": 100.0, "currency": "CRC"},
  "description": "Pago de servicios",
  "hmac_md5": "abc123..."
}
```

- **Confirmación**:  
  - El receptor responde con `ACK: Transaccion completada` o `NACK: <motivo>`.

---

## API REST (`api_server.py`)

### Endpoints principales

| Método | Endpoint                  | Descripción                                      |
|--------|---------------------------|--------------------------------------------------|
| POST   | `/register`               | Crear cuenta (opcional: phone_number)            |
| GET    | `/account/<account_number>` | Consultar detalles de cuenta                   |
| DELETE | `/delete/<account_number>` | Eliminar cuenta (si saldo es 0)                 |
| POST   | `/deposit`                | Depositar a cuenta local                         |
| POST   | `/cashout`                | Retirar de cuenta local                          |
| GET    | `/list_accounts`          | Listar todas las cuentas                         |
| POST   | `/transfer_interbank`     | Transferencia interbancaria                      |
| POST   | `/transfer_sinpe_movil`   | Transferencia SINPE Móvil (por teléfono)         |

### Ejemplo de uso: Crear cuenta

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"account_number": "12345", "nombre": "Juan Perez", "saldo": 1000, "phone_number": "88889999"}'
```

### Ejemplo de uso: Transferencia interbancaria

```bash
curl -X POST http://localhost:8000/transfer_interbank \
  -H "Content-Type: application/json" \
  -d '{
    "sender_account_number": "12345",
    "receiver_account_number": "67890",
    "receiver_bank_code": "BCB",
    "receiver_name": "Maria",
    "amount": 100,
    "currency": "CRC",
    "description": "Pago de servicios"
  }'
```

### Ejemplo de uso: SINPE Móvil

```bash
curl -X POST http://localhost:8000/transfer_sinpe_movil \
  -H "Content-Type: application/json" \
  -d '{
    "sender_account_number": "12345",
    "receiver_phone_number": "88887777",
    "receiver_bank_code": "BCB",
    "amount": 50,
    "currency": "CRC"
  }'
```

---

## Servidor de Sockets (`servidor.py`)

- Escucha en el puerto 5001 (por defecto) usando TLS/SSL.
- Recibe transferencias interbancarias y SINPE Móvil de otros bancos.
- Verifica la firma HMAC y el saldo antes de acreditar.
- Responde con `ACK` o `NACK` según el resultado.
- Incluye un menú interactivo para administración local de cuentas.

---

## Cliente de Transferencias (`cliente.py`)

- Permite enviar transferencias interbancarias o SINPE Móvil desde la línea de comandos.
- Usa TLS/SSL y firma HMAC.
- Ejemplo de uso:

```bash
python cliente.py --host localhost --port 5001 \
  --sender 12345 --sender_bank BCA --sender_name "Juan" \
  --receiver 67890 --receiver_bank BCB --receiver_name "Maria" \
  --amount 100 --currency CRC --description "Pago"
```

Para SINPE Móvil (por teléfono):

```bash
python cliente.py --host localhost --port 5001 \
  --sender 12345 --sender_bank BCA --sender_name "Juan" \
  --receiver_phone 88887777 --receiver_bank BCB --receiver_name "Maria" \
  --amount 50 --currency CRC --description "SINPE"
```

---

## Configuración y Despliegue

### 1. Instalar dependencias

```bash
pip install Flask
```

### 2. Generar certificados SSL

```bash
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem -subj "/CN=localhost"
```

### 3. Inicializar la base de datos

Se crea automáticamente al ejecutar el servidor, o manualmente:

```python
from db_handler import init_db
init_db()
```

### 4. Ejecutar el servidor de sockets

```bash
python servidor.py
```

### 5. Ejecutar el API REST

```bash
python api_server.py
```

### 6. Probar con curl o Postman

Ver ejemplos en la sección de [API REST](#api-rest-apispy).

---

## Pruebas y Ejemplos

- Crear cuentas, depositar, retirar, transferir entre bancos y por SINPE Móvil.
- Consultar la base de datos (`cuentas_banco.db`) con [DB Browser for SQLite](https://sqlitebrowser.org/).
- Revisar los logs en la carpeta `/logs/`.

---

## Consideraciones y Mejoras Futuras

- **Banco Central**: Se puede agregar como otro servidor para validar o autorizar transferencias.
- **Rollback automático**: Si una transferencia interbancaria falla, implementar reversión automática del débito.
- **Gestión de claves**: Usar variables de entorno o un gestor seguro para las claves HMAC.
- **Despliegue en producción**: Usar Gunicorn/uWSGI y Nginx para el API REST.
- **Escalabilidad**: Adaptar para múltiples bancos y mayor concurrencia.
- **Documentación OpenAPI/Swagger**: Para describir la API REST de forma interactiva.

---

## Créditos

Desarrollado por [Tu Nombre/Grupo], para el curso de Redes/Seguridad/Desarrollo de Software.

---

```


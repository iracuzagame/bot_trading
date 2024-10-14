import websocket
import json
import numpy as np
import time
import certifi


def on_open(ws):
    print("Conexión abierta.")
    authorize_message = {
        "authorize": token
    }
    ws.send(json.dumps(authorize_message))


def on_message(ws, message):
    data = json.loads(message)

    if 'error' in data.keys():
        print('Error:', data['error']['message'])

    elif data.get("msg_type") == "authorize":
        print("Autorización exitosa. Suscribiéndose a datos de mercado...")
        subscribe_to_candles(ws)

    elif data.get("msg_type") == "candles":
        analyze_market(ws, data['candles'])

    elif data.get("msg_type") == "buy":
        # Confirmación de la compra del contrato
        contract_id = data['buy']['contract_id']
        print(f"Operación ejecutada. ID del contrato: {contract_id}")
        subscribe_to_contract(ws, contract_id)

    elif data.get("msg_type") == "proposal_open_contract":
        # Detalles del contrato en tiempo real
        print(f"Detalles del contrato: {data['proposal_open_contract']}")
        if data['proposal_open_contract']['is_sold']:
            print(f"El contrato ha sido vendido. Ganancia: {data['proposal_open_contract']['profit']}")


def subscribe_to_candles(ws):
    candles_message = {
        "ticks_history": symbol,
        "subscribe": 1,
        "end": "latest",
        "style": "candles",
        "count": 50,  # Cantidad de velas para el análisis de SMA
        "granularity": 60  # 1 vela por minuto
    }
    ws.send(json.dumps(candles_message))


def analyze_market(ws, candles):
    print("Analizando velas...")

    # Calcula el SMA-10 y SMA-50
    sma_10 = np.mean([candle['close'] for candle in candles[-10:]])
    sma_50 = np.mean([candle['close'] for candle in candles[-50:]])

    print(f"SMA-10: {sma_10}, SMA-50: {sma_50}")

    if sma_10 > sma_50:
        print("Señal de compra detectada. Ejecutando operación Rise.")
        execute_rise_trade(ws)
    elif sma_10 < sma_50:
        print("Señal de venta detectada. Ejecutando operación Fall.")
        execute_fall_trade(ws)


def execute_rise_trade(ws):
    rise_trade_message = {
        "buy": 1,
        "subscribe": 1,
        "price": 10,
        "parameters": {
            "amount": 10,
            "basis": "stake",
            "contract_type": "CALL",
            "currency": "USD",
            "duration": 2,
            "duration_unit": "m",
            "symbol": symbol
        }
    }
    ws.send(json.dumps(rise_trade_message))
    print("Operación Rise enviada. Esperando confirmación...")


def execute_fall_trade(ws):
    fall_trade_message = {
        "buy": 1,
        "subscribe": 1,
        "price": 10,
        "parameters": {
            "amount": 10,
            "basis": "stake",
            "contract_type": "PUT",
            "currency": "USD",
            "duration": 2,
            "duration_unit": "m",
            "symbol": symbol
        }
    }
    ws.send(json.dumps(fall_trade_message))
    print("Operación Fall enviada. Esperando confirmación...")


def subscribe_to_contract(ws, contract_id):
    
    contract_message = {
        "proposal_open_contract": 1,
        "contract_id": contract_id
    }
    ws.send(json.dumps(contract_message))


def on_error(ws, error):
    print("Error en WebSocket:", error)


def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada. Intentando reconectar...")
    time.sleep(10)  # Aumentar tiempo de espera antes de intentar reconectar
    ws.run_forever()


# Variables globales
app_id = '64652'
token = 'ME6BuzlrA96RbUo'
symbol = 'R_100'

ws = websocket.WebSocketApp(
    "wss://ws.binaryws.com/websockets/v3?app_id=" + app_id,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close)
ws.run_forever(sslopt={"ca_certs": certifi.where()})

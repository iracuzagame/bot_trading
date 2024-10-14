import websocket
import json
import numpy as np
import time


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
        print("Autorización exitosa. Esperando señales...")
        analyze_market(ws)


def analyze_market(ws):
    candles = get_fake_candles(20)
    print("Analizando velas...")

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
    print("Operación Rise ejecutada. Esperando confirmación...")


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
    print("Operación Fall ejecutada. Esperando confirmación...")


def get_fake_candles(n):
    return [{'close': 1475.2} for _ in range(n)]


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

# Iniciar WebSocket
ws.run_forever()

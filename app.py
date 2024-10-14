import websocket
import json
import numpy as np
import time
import certifi


# Función para conectarse y autorizar
def on_open(ws):
    print("Conexión abierta.")
    authorize_message = {
        "authorize": token
    }
    ws.send(json.dumps(authorize_message))


# Función para manejar los mensajes entrantes
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


# Suscripción a las velas (ticks)
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


# Función para calcular el RSI
def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Función para calcular MACD
def calculate_macd(prices, short_period=12, long_period=26, signal_period=9):
    short_ema = np.mean(prices[-short_period:])
    long_ema = np.mean(prices[-long_period:])
    macd_line = short_ema - long_ema
    signal_line = np.mean([macd_line for _ in range(signal_period)])
    return macd_line, signal_line


# Función para analizar el mercado usando indicadores
def analyze_market(ws, candles):
    print("Analizando velas...")

    # Verifica si tienes suficientes velas para el análisis (al menos 50 para SMA-20 y 14 para RSI)
    if len(candles) < 50:
        print("No hay suficientes velas para realizar el análisis.")
        return

    closes = [candle['close'] for candle in candles]

    # Calcular SMA-20 y EMA-5
    sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.nan
    ema_5 = np.mean(closes[-5:]) if len(closes) >= 5 else np.nan

    # Calcular el RSI (14-periodos)
    rsi = calculate_rsi(closes, 14) if len(closes) >= 14 else np.nan

    # Calcular MACD
    macd_line, signal_line = calculate_macd(closes, 12, 26, 9) if len(closes) >= 26 else (np.nan, np.nan)

    # Mostrar resultados del análisis
    print(f"SMA-20: {sma_20}, EMA-5: {ema_5}, RSI: {rsi if not np.isnan(rsi) else 'N/A'}")
    print(
        f"MACD: {macd_line if not np.isnan(macd_line) else 'N/A'}, Signal: {signal_line if not np.isnan(signal_line) else 'N/A'}")

    # Estrategia de compra y venta
    if ema_5 > sma_20 and rsi < 30 and macd_line > signal_line:
        print("Señal de compra detectada. Ejecutando operación Rise.")
        execute_rise_trade(ws)
    elif ema_5 < sma_20 and rsi > 70 and macd_line < signal_line:
        print("Señal de venta detectada. Ejecutando operación Fall.")
        execute_fall_trade(ws)


# Ejecuta la operación de compra (Rise)
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


# Ejecuta la operación de venta (Fall)
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


# Suscripción a los detalles del contrato
def subscribe_to_contract(ws, contract_id):
    contract_message = {
        "proposal_open_contract": 1,
        "contract_id": contract_id
    }
    ws.send(json.dumps(contract_message))


# Manejo de errores
def on_error(ws, error):
    print("Error en WebSocket:", error)


# Manejo del cierre de la conexión
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

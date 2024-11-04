import websocket
import json
import numpy as np
import time
import certifi

# Variables globales
app_id = 'coloca_tu_appid'
token = 'Coloca_tu_token_api'
symbol = 'R_25'
subscription_id = None  # Para almacenar el ID de la suscripción activa
contract_id = None  # Para almacenar el ID del contrato en curso
initial_investment = 10  # Inversión inicial para los contratos
target_profit_percentage = 0.25  # 25% de ganancia
contract_check_interval = 5  # Verificar cada 5 segundos el estado del contrato

def on_open(ws):
    print("Conexión abierta.")
    authorize_message = {
        "authorize": token
    }
    ws.send(json.dumps(authorize_message))

def on_message(ws, message):
    global subscription_id, contract_id
    data = json.loads(message)

    if 'error' in data.keys():
        print('Error:', data['error']['message'])

    elif data.get("msg_type") == "authorize":
        print("Autorización exitosa. Suscribiéndose a datos de mercado...")
        subscribe_to_candles(ws)

    elif data.get("msg_type") == "candles":
        subscription_id = data['subscription']['id']  # Guardar ID de suscripción
        analyze_market(ws, data['candles'])

    elif data.get("msg_type") == "buy":
        contract_id = data['buy']['contract_id']
        print(f"Operación ejecutada. ID del contrato: {contract_id}")
        subscribe_to_contract(ws, contract_id)

    elif data.get("msg_type") == "proposal_open_contract":
        print(f"Detalles del contrato: {data['proposal_open_contract']}")
        if data['proposal_open_contract']['is_sold']:
            print(f"El contrato ha sido vendido. Ganancia: {data['proposal_open_contract']['profit']}")
            # Reiniciar análisis tras vender el contrato
            reanalyze_after_contract(ws)
        else:
            # Check and sell contract if the take profit is reached
            check_and_finalize_contract(ws, data['proposal_open_contract'])

def subscribe_to_candles(ws):
    global subscription_id
    if subscription_id:
        # Cancelar suscripción anterior si ya existe una
        unsubscribe_message = {
            "forget": subscription_id
        }
        ws.send(json.dumps(unsubscribe_message))
        print(f"Cancelando suscripción previa: {subscription_id}")

    # Nueva suscripción a velas
    candles_message = {
        "ticks_history": symbol,
        "subscribe": 1,
        "end": "latest",
        "style": "candles",
        "count": 50,  # Cantidad de velas para análisis
        "granularity": 60  # 1 vela por minuto
    }
    ws.send(json.dumps(candles_message))

def calculate_sma(data, window):
    sma = np.mean(data[-window:])
    return sma

def calculate_rsi(candles, period=4):
    closes = [c['close'] for c in candles]
    deltas = np.diff(closes)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down
    rsi = np.zeros_like(closes)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(closes)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi[-1]

def calculate_adx(candles, period=4):
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]

    plus_dm = [highs[i] - highs[i-1] if highs[i] - highs[i-1] > lows[i-1] - lows[i] else 0 for i in range(1, len(highs))]
    minus_dm = [lows[i-1] - lows[i] if lows[i-1] - lows[i] > highs[i] - highs[i-1] else 0 for i in range(1, len(lows))]

    trs = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])) for i in range(1, len(closes))]

    plus_di = [100 * (sum(plus_dm[:i+1]) / sum(trs[:i+1])) for i in range(len(plus_dm))]
    minus_di = [100 * (sum(minus_dm[:i+1]) / sum(trs[:i+1])) for i in range(len(minus_dm))]

    adx = np.mean([abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i]) for i in range(1, len(plus_di))])
    return plus_di[-1], minus_di[-1], adx

def analyze_market(ws, candles):
    print("Analizando mercado...")

    # Calcular indicadores RSI, ADX y SMA-12
    rsi = calculate_rsi(candles)
    sma_12 = calculate_sma([candle['close'] for candle in candles], 12)
    plus_di, minus_di, adx = calculate_adx(candles)

    last_close = candles[-1]['close']
    last_open = candles[-1]['open']

    # Identificar si la vela es verde o roja
    is_green_candle = last_close > last_open
    is_red_candle = last_close < last_open

    print(f"RSI: {rsi}, SMA-12: {sma_12}, DI+: {plus_di}, DI-: {minus_di}, ADX: {adx}, Último Cierre: {last_close}, Vela Verde: {is_green_candle}, Vela Roja: {is_red_candle}")

    # Estrategia basada en los indicadores
    if rsi > 70 and last_close > sma_12 and plus_di > minus_di:
        print("Señal de compra detectada. Ejecutando operación Rise.")
        execute_rise_trade(ws)
    elif rsi < 30 and last_close < sma_12 and minus_di > plus_di:
        print("Señal de venta detectada. Ejecutando operación Fall.")
        execute_fall_trade(ws)
    else:
        print("No se han cumplido las condiciones para operar. Reanalizando en 30 segundos...")
        time.sleep(30)  # Esperar 30 segundos antes de reanalizar
        reanalyze_if_no_signal(ws)

def execute_rise_trade(ws):
    global contract_id
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
    global contract_id
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
        "proposal_open_contract": 1
    }
    ws.send(json.dumps(contract_message))

def reanalyze_after_contract(ws):
    print("Reiniciando análisis después de la finalización del contrato...")
    subscribe_to_candles(ws)

def reanalyze_if_no_signal(ws):
    print("Reanalizando inmediatamente...")
    subscribe_to_candles(ws)

def check_and_finalize_contract(ws, contract_data):
    global contract_id, initial_investment, target_profit_percentage
    # Verificar si la ganancia alcanza el 25%
    profit_percentage = contract_data['profit'] / initial_investment
    print(f"Ganancia actual del contrato: {profit_percentage * 100}%")

    if profit_percentage >= target_profit_percentage:
        print(f"Ganancia del contrato ha alcanzado el 25% ({profit_percentage * 100}%). Vendiendo contrato...")
        sell_contract(ws, contract_data['contract_id'])
    else:
        print(f"Ganancia del contrato: {profit_percentage * 100}%. Esperando...")

def sell_contract(ws, contract_id):
    sell_message = { "sell": 1, "contract_id": contract_id }
    ws.send(json.dumps(sell_message))
    print(f"Contrato {contract_id} vendido.")

def on_error(ws, error):
    print("Error en WebSocket:", error)

def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada. Intentando reconectar...")
    time.sleep(10)
    ws.run_forever()

ws = websocket.WebSocketApp(
    "wss://ws.binaryws.com/websockets/v3?app_id=" + app_id,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close)

ws.run_forever(sslopt={"ca_certs": certifi.where()})

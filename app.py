import time
import os
import sys
import json
import time
import random
import asyncio
import pandas as pd
#from quotexpy import Quotex
from quotexapi.stable_api import Quotex
from getpass import getpass
#import talib as ta

# Función para obtener las credenciales del usuario
def obtener_credenciales():
    email = input("Introduce tu correo: ")
    password = input("Introduce tu contraseña: ")
    #cuenta = input("¿Deseas operar en demo o real? (demo/real): ").lower()
    return email, password #cuenta

# Conexión a Quotex
def conectar_quotex(email, password): #cuenta
    try:
        api = Quotex(email, password) #type_account=cuenta
        if api.check_connect():
            print(f"Conectado exitosamente a la cuenta {email}")
            return api
        else:
            print("Error en la conexión, verifica tus credenciales")
            return None
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return None

# Estrategia de trading basada en SMA, ADX y RSI
def ejecutar_estrategia(api, market='EURUSD', timeframe=1):
    while True:
        # Obtener datos de velas
        data = api.get_candles(asset=market, period=timeframe, number=50)  # Últimas 50 velas
        df = pd.DataFrame(data)

        # Calcular indicadores
        close = df['close']
        sma = ta.SMA(close, timeperiod=12)
        adx = ta.ADX(df['high'], df['low'], close, timeperiod=4)
        plus_di = ta.PLUS_DI(df['high'], df['low'], close, timeperiod=3)
        minus_di = ta.MINUS_DI(df['high'], df['low'], close, timeperiod=3)
        rsi = ta.RSI(close, timeperiod=4)

        # Últimos valores para validar la estrategia
        last_sma = sma.iloc[-1]
        last_close = close.iloc[-1]
        last_adx = adx.iloc[-1]
        last_plus_di = plus_di.iloc[-1]
        last_minus_di = minus_di.iloc[-1]
        last_rsi = rsi.iloc[-1]

        # Verificar condiciones de compra
        if (last_close > last_sma and last_adx > last_plus_di and last_adx > last_minus_di
            and last_plus_di > last_minus_di and last_rsi > 70):
            print(f"Condiciones para compra detectadas - {market}")
            try:
                api.buy(asset=market, amount=1, direction="call", duration=2)  # Compra de 2 minutos
                print(f"Compra realizada en {market}")
            except Exception as e:
                print(f"Error al realizar la compra: {e}")
        else:
            print(f"No se cumplen las condiciones de compra en {market}")
        
        time.sleep(60)  # Esperar un minuto antes de la siguiente comprobación

# Función principal
def main():
    email, password, cuenta = obtener_credenciales()
    api = conectar_quotex(email, password, cuenta)
    if api:
        ejecutar_estrategia(api)

if __name__ == "__main__":
    main()

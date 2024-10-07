from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
#import talib
import pandas as pd

# Configurar Chrome para Selenium
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Configurar opciones de Chrome
chrome_options = webdriver.ChromeOptions()

try:
  # Iniciar el navegador con la versión correcta de ChromeDriver
 driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

  # Navegar a la página
 driver.get("https://qxbroker.com/es")

  # Esperar a que la página cargue completamente
 time.sleep(5)

    
 # Pedir credenciales de usuario
 email = input("Ingresa tu correo: ")
 password = input("Ingresa tu contraseña: ")

 # Ingresar credenciales en la página
 driver.find_element(By.ID, 'email_input_field').send_keys(email)  # Cambia el ID según corresponda
 driver.find_element(By.ID, 'password_input_field').send_keys(password)  # Cambia el ID según corresponda

# Hacer clic en el botón de inicio de sesión
 driver.find_element(By.ID, 'login_button').click()  # Cambia el ID según corresponda

# Esperar a que la página cargue después del login
 time.sleep(10)

# Seleccionar la cuenta demo/practice
# Cambia el ID o XPATH según la estructura del DOM de la página
 driver.find_element(By.XPATH, '//button[contains(text(), "Cuenta Demo")]').click()

# Esperar para asegurar la selección
 time.sleep(5)

# Supongamos que obtienes los datos de las velas desde alguna API o scraping
# Aquí un ejemplo ficticio con pandas
# time, open, high, low, close son las columnas necesarias para calcular indicadores
 data = {
    'time': ['2024-10-05 10:00', '2024-10-05 10:01', '2024-10-05 10:02'],
    'open': [1.12, 1.13, 1.14],
    'high': [1.15, 1.16, 1.17],
    'low': [1.11, 1.12, 1.13],
    'close': [1.14, 1.15, 1.16]
 }

 df = pd.DataFrame(data)

# Calcular Media Móvil, ADX, DI+, DI-, y RSI
 df['SMA'] = talib.SMA(df['close'], timeperiod=12)
 df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=4)
 df['PLUS_DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=3)
 df['MINUS_DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=3)
 df['RSI'] = talib.RSI(df['close'], timeperiod=4)

# Definir los niveles de sobrecompra y sobreventa para RSI
 overbought = 70
 oversold = 30

# Lógica de la estrategia
 def should_buy(df):
    last_row = df.iloc[-1]
    
    # Condiciones para comprar
    return (last_row['close'] > last_row['SMA'] and
            last_row['ADX'] > last_row['PLUS_DI'] and
            last_row['ADX'] > last_row['MINUS_DI'] and
            last_row['PLUS_DI'] > last_row['MINUS_DI'] and
            last_row['RSI'] > overbought)

 # Ejecutar la estrategia y realizar operación si se cumple la condición de compra
 if should_buy(df):
    print("Ejecutando operación de compra...")
    # Buscar el par del mercado OTC
    driver.find_element(By.XPATH, '//button[contains(text(), "OTC Market Pair")]').click()

    # Seleccionar el tiempo de operación (2 minutos)
    driver.find_element(By.XPATH, '//button[contains(text(), "2M")]').click()

    # Realizar operación de compra
    driver.find_element(By.XPATH, '//button[contains(text(), "Buy")]').click()

    # Esperar a que la operación se ejecute
    time.sleep(5)

    # Debes ubicar los elementos de compra y tiempo de la operación

except Exception as e:
    print(f"Error: {e}")

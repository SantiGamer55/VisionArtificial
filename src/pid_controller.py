from logs.config_logger import configurar_logging
import mysql.connector
from datetime import datetime
from pytz import timezone
import requests

# Configuración del logger
logger = configurar_logging()

class PIDController:
    # Inicializar el controlador PID con los coeficientes K_p, K_i y K_d
    def __init__(self, K_p, K_i, K_d):
        self.K_p = K_p
        self.K_i = K_i
        self.K_d = K_d
        self.previous_error = 0
        self.cumulative_error = 0

    def calculate(self, error):
        p = self.K_p * error # Proporcional
        self.cumulative_error += error # Integral
        i = self.K_i * self.cumulative_error # Integral
        d = self.K_d * (error - self.previous_error) # Derivativo
        self.previous_error = error
        return p + i + d

def enviar_datos(web, desvio_mm):
    print(f"Enviando datos al espwroonm32 {web}")
    K_p = 1
    K_i = 0
    K_d = 0
    controller = PIDController(K_p, K_i, K_d)
    p = controller.calculate(desvio_mm) # Calcular el valor de P
    IP = "192.168.1.184"
    url = f"http://{IP}/{web}?p={p}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Datos enviados exitosamente a {url}")
        else:
            print(f"Error al enviar datos a {url}. Estado de la respuesta: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error de conexión: {e}")


def enviar_datos_sql(desvio_mm):
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="registro_va"
        )
        cursor = conn.cursor()

        unixtime = int(datetime.now().timestamp())
        # Obtener la zona horaria de Buenos Aires
        tz = timezone('America/Argentina/Buenos_Aires')

        # Obtener la fecha y hora en la zona horaria de Buenos Aires
        dt = datetime.fromtimestamp(unixtime, tz)

        
        # Calcular direccion
        direccion = 1 if desvio_mm > 0 else 0
        
        # Calcular enable
        enable_val = 1 if abs(desvio_mm) > 2 else 0

        # Insertar datos en la tabla
        cursor.execute('''
            INSERT INTO desvio_papel (unixtime, datetime, desvio, direccion, enable)
            VALUES (%s, %s, %s, %s, %s)
        ''', (unixtime, dt, desvio_mm, direccion, enable_val))

        # Confirmar la transacción
        conn.commit()
        logger.info("Datos de desvío registrados en la base de datos.")

    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")

    finally:
        # Cerrar la conexión
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()



"""
registro.py
-----------
Configuración del archivo de logs del sistema.

Toda la información de eventos y errores se escribe en logs/software_fj.log.
No se usa base de datos: el archivo de texto es el único medio persistente.
"""

import logging  # Módulo estándar de Python para registrar eventos
import os  # Permite construir rutas y crear carpetas

# Ruta de la carpeta logs ubicada en la raíz del proyecto (un nivel arriba de este paquete)
CARPETA_LOGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
# Ruta completa del archivo de logs
ARCHIVO_LOG = os.path.join(CARPETA_LOGS, "software_fj.log")


def obtener_logger(nombre="software_fj"):  # Devuelve un logger listo para usar
    """Crea (una sola vez) y devuelve el logger del sistema."""
    logger = logging.getLogger(nombre)  # Obtiene o crea el logger con ese nombre
    if logger.handlers:  # Si ya tiene manejadores configurados...
        return logger  # ...lo devuelve tal cual para no duplicar líneas en el archivo
    os.makedirs(CARPETA_LOGS, exist_ok=True)  # Crea la carpeta logs si no existe
    logger.setLevel(logging.DEBUG)  # Registra todos los niveles: DEBUG, INFO, WARNING, ERROR
    manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")  # Escribe en el archivo con tildes y ñ
    formato = logging.Formatter(  # Define cómo se verá cada línea del log
        "%(asctime)s | %(levelname)-8s | %(module)-12s | %(message)s",  # Fecha | nivel | módulo | mensaje
        datefmt="%Y-%m-%d %H:%M:%S",  # Formato de fecha y hora
    )
    manejador.setFormatter(formato)  # Asigna el formato al manejador
    logger.addHandler(manejador)  # Conecta el manejador al logger
    logger.propagate = False  # Evita que los mensajes se repitan en la consola
    return logger  # Devuelve el logger configurado

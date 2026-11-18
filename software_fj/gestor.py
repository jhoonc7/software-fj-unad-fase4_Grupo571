"""
gestor.py
---------
SistemaSoftwareFJ: administra clientes, servicios y reservas en listas
internas (sin base de datos) y registra cada evento o error en el log.
"""

from .entidades import Cliente  # Clase Cliente
from .excepciones import (  # Excepciones del dominio
    ClienteDuplicadoError,
    ClienteInvalidoError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from .registro import obtener_logger  # Logger del sistema
from .reservas import EstadoReserva, Reserva  # Reserva y sus estados

log = obtener_logger()  # Logger compartido


class SistemaSoftwareFJ:
    """Fachada que coordina todas las operaciones del sistema."""

    def __init__(self):
        self._clientes = []  # Lista interna de clientes
        self._servicios = []  # Lista interna de servicios
        self._reservas = []  # Lista interna de reservas
        log.info("=== Sistema Software FJ iniciado ===")  # Evento de arranque

    # ---------------- clientes ----------------
    def registrar_cliente(self, nombre, documento, correo, telefono):
        """Crea y registra un cliente; si los datos fallan se registra el error."""
        if any(c.documento == str(documento).strip() for c in self._clientes):  # ¿Ya existe?
            log.error("Cliente duplicado: documento %s", documento)
            raise ClienteDuplicadoError(f"Ya existe un cliente con documento {documento}.")
        try:  # try/except/else
            cliente = Cliente(nombre, documento, correo, telefono)  # Puede lanzar ClienteInvalidoError
        except ClienteInvalidoError as error:  # Datos personales incorrectos
            log.error("Registro de cliente rechazado: %s", error)  # Se guarda en el log
            raise  # Se propaga para que la capa superior lo informe
        else:  # Solo si el cliente se creó bien
            self._clientes.append(cliente)  # Se agrega a la lista
            log.info("Cliente registrado: %s", cliente.describir())
            return cliente

    def buscar_cliente(self, documento):  # Búsqueda lineal en la lista
        for cliente in self._clientes:
            if cliente.documento == str(documento):
                return cliente
        raise ClienteInvalidoError(f"No existe un cliente con documento {documento}.")

    # ---------------- servicios ----------------
    def registrar_servicio(self, clase_servicio, *args, **kwargs):
        """Crea cualquier tipo de servicio (polimorfismo por clase) y lo agrega a la lista."""
        try:
            servicio = clase_servicio(*args, **kwargs)  # Instancia la subclase indicada
        except TypeError as error:  # Faltan argumentos obligatorios en el constructor
            log.error("Faltan parámetros para crear %s: %s", clase_servicio.__name__, error)
            # Encadenamiento: se transforma un error de Python en uno del dominio
            raise ServicioNoDisponibleError(
                f"No se pudo crear el servicio {clase_servicio.__name__}: parámetros incompletos."
            ) from error
        except SoftwareFJError as error:  # Valores inválidos (tarifa, capacidad, nivel...)
            log.error("Servicio rechazado: %s", error)
            raise
        self._servicios.append(servicio)  # Se agrega solo si no hubo error
        log.info("Servicio registrado: %s", servicio.describir())
        return servicio

    # ---------------- reservas ----------------
    def crear_reserva(self, cliente, servicio, duracion, **parametros):
        """Crea una reserva pendiente y la guarda en la lista interna."""
        try:
            reserva = Reserva(cliente, servicio, duracion, **parametros)  # Valida al construir
        except ReservaInvalidaError as error:  # Reserva incorrecta
            causa = f" (causa: {error.__cause__})" if error.__cause__ else ""  # Muestra la causa encadenada
            log.error("Reserva rechazada: %s%s", error, causa)
            raise
        self._reservas.append(reserva)
        log.info("Reserva creada: %s", reserva.describir())
        return reserva

    # ---------------- reportes ----------------
    def resumen(self):
        """Devuelve un diccionario con totales para el reporte final."""
        ingresos = sum(r.costo for r in self._reservas if r.estado is EstadoReserva.PROCESADA)
        return {
            "clientes": len(self._clientes),
            "servicios": len(self._servicios),
            "reservas": len(self._reservas),
            "procesadas": sum(r.estado is EstadoReserva.PROCESADA for r in self._reservas),
            "canceladas": sum(r.estado is EstadoReserva.CANCELADA for r in self._reservas),
            "ingresos": ingresos,
        }

    @property
    def clientes(self):  # Copia de la lista para no exponer la original
        return list(self._clientes)

    @property
    def servicios(self):
        return list(self._servicios)

    @property
    def reservas(self):
        return list(self._reservas)

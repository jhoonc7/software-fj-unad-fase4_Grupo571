"""
reservas.py
-----------
Clase Reserva: integra cliente, servicio, duración y estado.

Implementa confirmación, cancelación y procesamiento usando los bloques
try/except, try/except/else, try/except/finally y encadenamiento de
excepciones (raise ... from ...).
"""

from enum import Enum  # Para definir los estados posibles de una reserva

from .entidades import Cliente, EntidadBase  # Cliente y clase abstracta general
from .excepciones import (  # Excepciones usadas en las reservas
    OperacionNoPermitidaError,
    ParametroInvalidoError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from .registro import obtener_logger  # Logger del sistema
from .servicios import IVA, Servicio  # Tarifa de IVA y clase base de servicios

log = obtener_logger()  # Logger compartido por el módulo


class EstadoReserva(Enum):  # Estados del ciclo de vida de una reserva
    PENDIENTE = "Pendiente"  # Recién creada
    CONFIRMADA = "Confirmada"  # Aprobada y con costo calculado
    CANCELADA = "Cancelada"  # Anulada por el cliente o el sistema
    PROCESADA = "Procesada"  # Pagada y finalizada


class Reserva(EntidadBase):  # La reserva también es una entidad del sistema
    """Reserva de un servicio realizada por un cliente."""

    def __init__(self, cliente, servicio, duracion, **parametros):
        super().__init__("RES")  # Id con prefijo RES
        self._cliente = cliente  # Cliente que reserva
        self._servicio = servicio  # Servicio reservado
        self._duracion = duracion  # Horas reservadas
        self._parametros = parametros  # Datos extra (personas, cantidad, modalidad)
        self._estado = EstadoReserva.PENDIENTE  # Toda reserva inicia pendiente
        self._costo = None  # Aún no se ha calculado el costo
        self.validar()  # Valida que la reserva sea coherente

    # ---------------- propiedades de solo lectura ----------------
    @property
    def estado(self):
        return self._estado

    @property
    def costo(self):
        return self._costo

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    def validar(self):  # Implementa el método abstracto
        if not isinstance(self._cliente, Cliente):  # El cliente debe ser un objeto Cliente
            raise ReservaInvalidaError("La reserva necesita un cliente válido.")
        if not isinstance(self._servicio, Servicio):  # El servicio debe ser un objeto Servicio
            raise ReservaInvalidaError("La reserva necesita un servicio válido.")
        try:  # try/except con encadenamiento de excepciones
            self._servicio.verificar_disponibilidad()  # ¿El servicio está activo?
            self._servicio.validar_parametros(self._duracion, **self._parametros)  # ¿Parámetros correctos?
        except (ServicioNoDisponibleError, ParametroInvalidoError) as error:  # Captura el error original
            # Se lanza un error de más alto nivel conservando la causa original (__cause__)
            raise ReservaInvalidaError(f"No se pudo crear la reserva: {error.mensaje}") from error
        return True

    def confirmar(self, impuesto=IVA, descuento=None):
        """Confirma la reserva y calcula su costo (try/except/else)."""
        if self._estado is not EstadoReserva.PENDIENTE:  # Solo se confirman reservas pendientes
            raise OperacionNoPermitidaError(
                f"La reserva {self.id} está {self._estado.value}; no se puede confirmar."
            )
        try:  # Intenta calcular el costo
            costo = self._servicio.calcular_costo(  # Llamado polimórfico al servicio
                self._duracion, impuesto, descuento, **self._parametros
            )
        except SoftwareFJError as error:  # Si falla el cálculo...
            log.error("Error al confirmar %s: %s", self.id, error)  # ...se registra en el log
            raise ReservaInvalidaError(f"No se pudo confirmar {self.id}.") from error  # Encadenamiento
        else:  # Solo se ejecuta si NO hubo excepción
            self._costo = costo  # Guarda el costo calculado
            self._estado = EstadoReserva.CONFIRMADA  # Cambia el estado
            log.info("Reserva %s confirmada por $%s", self.id, f"{costo:,.2f}")  # Evento en el log
            return costo  # Devuelve el costo al llamador

    def cancelar(self, motivo="Sin motivo"):
        """Cancela la reserva si aún no ha sido procesada."""
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):  # Estados finales
            raise OperacionNoPermitidaError(
                f"La reserva {self.id} ya está {self._estado.value}; no se puede cancelar."
            )
        self._estado = EstadoReserva.CANCELADA  # Cambia el estado
        log.warning("Reserva %s cancelada. Motivo: %s", self.id, motivo)  # Evento en el log

    def procesar(self, pago):
        """Procesa el pago de una reserva confirmada (try/except/finally)."""
        try:  # Bloque protegido
            if self._estado is not EstadoReserva.CONFIRMADA:  # Solo se procesan confirmadas
                raise OperacionNoPermitidaError(
                    f"La reserva {self.id} está {self._estado.value}; debe estar Confirmada."
                )
            try:  # Conversión del pago: puede fallar con ValueError o TypeError
                pago = float(pago)
            except (TypeError, ValueError) as error:  # Error de Python nativo...
                raise ParametroInvalidoError(f"Pago inválido: {pago!r}.") from error  # ...encadenado al dominio
            if pago < self._costo:  # Pago insuficiente
                raise ReservaInvalidaError(
                    f"Pago insuficiente para {self.id}: ${pago:,.2f} de ${self._costo:,.2f}."
                )
            self._estado = EstadoReserva.PROCESADA  # Pago correcto: reserva finalizada
            cambio = round(pago - self._costo, 2)  # Calcula el cambio a devolver
            log.info("Reserva %s procesada. Cambio: $%s", self.id, f"{cambio:,.2f}")
            return cambio  # Devuelve el cambio
        except SoftwareFJError:  # Cualquier error del dominio...
            log.error("Fallo al procesar la reserva %s", self.id)  # ...se registra
            raise  # ...y se propaga sin perder el tipo original
        finally:  # Se ejecuta SIEMPRE, haya o no error
            log.debug("Intento de procesamiento de %s finalizado (estado: %s)",
                      self.id, self._estado.value)

    def describir(self):  # Implementa el método abstracto
        costo = f"${self._costo:,.2f}" if self._costo is not None else "sin calcular"
        return (f"{self.id} | {self._cliente.nombre} -> {self._servicio.nombre} | "
                f"{self._duracion} h | {self._estado.value} | {costo}")

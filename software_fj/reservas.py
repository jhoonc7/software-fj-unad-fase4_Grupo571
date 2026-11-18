"""
reservas.py
-----------
Clase Reserva: integra cliente, servicio, duración y estado.

Implementa confirmación, cancelación y procesamiento usando los bloques
try/except, try/except/else, try/except/finally y encadenamiento de
excepciones (raise ... from ...).
"""

from enum import Enum  # Importa Enum para definir un conjunto fijo de estados

from .entidades import Cliente, EntidadBase  # Importa Cliente y la superclase EntidadBase
from .excepciones import (  # Importa las excepciones personalizadas necesarias
    OperacionNoPermitidaError,
    ParametroInvalidoError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from .registro import obtener_logger  # Importa la función configuradora de logs
from .servicios import IVA, AlquilerEquipo, Servicio  # Importa constante IVA, AlquilerEquipo y clase Servicio

log = obtener_logger()  # Instancia el logger para registrar eventos de este módulo


class EstadoReserva(Enum):  # Enumeración con los 4 estados posibles de una reserva
    PENDIENTE = "Pendiente"  # Estado inicial cuando se crea pero no se ha confirmado
    CONFIRMADA = "Confirmada"  # Estado cuando se valida el costo y se separa el cupo/equipo
    CANCELADA = "Cancelada"  # Estado cuando se anula la reserva antes de pagarse
    PROCESADA = "Procesada"  # Estado final cuando el cliente realiza el pago


class Reserva(EntidadBase):  # Clase Reserva que hereda identificador y estructura de EntidadBase
    """Reserva de un servicio realizada por un cliente."""

    def __init__(self, cliente, servicio, duracion, **parametros):  # Constructor de la reserva
        super().__init__("RES")  # Inicializa EntidadBase con el prefijo 'RES' (ej. RES-001)
        self._cliente = cliente  # Asigna el objeto Cliente asociado a la reserva
        self._servicio = servicio  # Asigna el objeto Servicio que se desea contratar
        self._duracion = duracion  # Guarda la cantidad de horas solicitadas
        self._parametros = parametros  # Guarda diccionario de argumentos extra (personas, cantidad, modalidad)
        self._estado = EstadoReserva.PENDIENTE  # Toda reserva nace en estado PENDIENTE
        self._costo = None  # Inicializa el costo en None hasta que se confirme la reserva
        self.validar()  # Ejecuta la validación inicial al construir el objeto

    @property
    def estado(self):  # Propiedad getter para consultar el estado actual
        return self._estado  # Retorna el miembro de EstadoReserva correspondiente

    @property
    def costo(self):  # Propiedad getter para consultar el costo total calculado
        return self._costo  # Retorna el monto numérico o None si no se ha confirmado

    @property
    def cliente(self):  # Propiedad getter para obtener el cliente dueño de la reserva
        return self._cliente  # Retorna la instancia de Cliente

    @property
    def servicio(self):  # Propiedad getter para obtener el servicio reservado
        return self._servicio  # Retorna la instancia de Servicio

    def validar(self):  # Implementación del método abstracto validar()
        if not isinstance(self._cliente, Cliente):  # Comprueba que _cliente sea realmente un objeto Cliente
            raise ReservaInvalidaError("La reserva necesita un cliente válido.")  # Lanza error SFJ-401 si no lo es
        if not isinstance(self._servicio, Servicio):  # Comprueba que _servicio sea una instancia de Servicio
            raise ReservaInvalidaError("La reserva necesita un servicio válido.")  # Lanza error SFJ-401 si no lo es
        try:  # Bloque try/except para capturar fallos del servicio y encadenarlos
            self._servicio.verificar_disponibilidad()  # Verifica que el servicio esté activo
            self._servicio.validar_parametros(self._duracion, **self._parametros)  # Valida horas y requisitos propios
        except (ServicioNoDisponibleError, ParametroInvalidoError) as error:  # Si el servicio lanza error...
            # ...encadena la excepción original (from error) dentro de ReservaInvalidaError
            raise ReservaInvalidaError(f"No se pudo crear la reserva: {error.mensaje}") from error
        return True  # Retorna True si todas las validaciones fueron exitosas

    def confirmar(self, impuesto=IVA, descuento=None):
        """Confirma la reserva, descuenta stock si aplica y calcula su costo (try/except/else)."""
        if self._estado is not EstadoReserva.PENDIENTE:  # Verifica que la reserva esté en estado PENDIENTE
            raise OperacionNoPermitidaError(  # Impide confirmar reservas ya confirmadas, canceladas o procesadas
                f"La reserva {self.id} está {self._estado.value}; no se puede confirmar."
            )
        try:  # Intenta realizar el cálculo del costo total
            costo = self._servicio.calcular_costo(  # Llama polimórficamente a calcular_costo del servicio
                self._duracion, impuesto, descuento, **self._parametros
            )
            # ---- MEJORA YONATAN CAGUA: Descontar unidades del inventario al confirmar AlquilerEquipo ----
            if isinstance(self._servicio, AlquilerEquipo):  # Si el servicio reservado es un equipo tecnológico...
                self._servicio.ocupar_unidades(self._parametros.get("cantidad", 1))  # ...resta las unidades del stock
        except SoftwareFJError as error:  # Si ocurre cualquier error de negocio durante el cálculo...
            log.error("Error al confirmar %s: %s", self.id, error)  # ...deja constancia en el archivo .log
            raise ReservaInvalidaError(f"No se pudo confirmar {self.id}.") from error  # Encadena y propaga el error
        else:  # Bloque else: se ejecuta ÚNICAMENTE si el bloque try no lanzó ninguna excepción
            self._costo = costo  # Almacena el costo definitivo en el atributo _costo
            self._estado = EstadoReserva.CONFIRMADA  # Actualiza el estado a CONFIRMADA
            log.info("Reserva %s confirmada por $%s", self.id, f"{costo:,.2f}")  # Registra el éxito en el log
            return costo  # Devuelve el valor calculado

    def cancelar(self, motivo="Sin motivo"):
        """Cancela la reserva y libera stock si estaba confirmada."""
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):  # Verifica si ya está en estado final
            raise OperacionNoPermitidaError(  # No permite cancelar algo que ya fue pagado o anulado antes
                f"La reserva {self.id} ya está {self._estado.value}; no se puede cancelar."
            )
        # ---- MEJORA YONATAN CAGUA: Devolver unidades al inventario si se cancela un alquiler confirmado ----
        if self._estado is EstadoReserva.CONFIRMADA and isinstance(self._servicio, AlquilerEquipo):
            self._servicio.liberar_unidades(self._parametros.get("cantidad", 1))  # Reintegra los equipos al stock
        self._estado = EstadoReserva.CANCELADA  # Cambia el estado de la reserva a CANCELADA
        log.warning("Reserva %s cancelada. Motivo: %s", self.id, motivo)  # Registra advertencia en el archivo .log

    def procesar(self, pago):
        """Procesa el pago de una reserva confirmada empleando try/except/finally."""
        try:  # Inicia bloque protegido para el procesamiento del pago
            if self._estado is not EstadoReserva.CONFIRMADA:  # Exige que la reserva esté previamente CONFIRMADA
                raise OperacionNoPermitidaError(  # Lanza error SFJ-402 si intentan pagar una pendiente o cancelada
                    f"La reserva {self.id} está {self._estado.value}; debe estar Confirmada."
                )
            try:  # Sub-bloque try para validar que el pago ingresado sea convertible a número
                pago = float(pago)  # Intenta convertir el parámetro pago a punto flotante
            except (TypeError, ValueError) as error:  # Captura error nativo de Python si meten letras o None
                raise ParametroInvalidoError(f"Pago inválido: {pago!r}.") from error  # Encadena a excepción del dominio
            if pago < self._costo:  # Comprueba si el dinero entregado es menor al costo de la reserva
                raise ReservaInvalidaError(  # Lanza error SFJ-401 por dinero insuficiente
                    f"Pago insuficiente para {self.id}: ${pago:,.2f} de ${self._costo:,.2f}."
                )
            self._estado = EstadoReserva.PROCESADA  # Si el pago es válido y suficiente, pasa a estado PROCESADA
            cambio = round(pago - self._costo, 2)  # Calcula las vueltas o cambio a devolver al cliente
            log.info("Reserva %s procesada. Cambio: $%s", self.id, f"{cambio:,.2f}")  # Registra pago exitoso en log
            return cambio  # Retorna el cambio calculado
        except SoftwareFJError:  # Si ocurre cualquier excepción de SoftwareFJError...
            log.error("Fallo al procesar la reserva %s", self.id)  # ...registra el fallo en el archivo .log
            raise  # ...y vuelve a lanzar la excepción para que el programa principal se entere
        finally:  # Bloque finally: se ejecuta SIEMPRE (haya ocurrido error o todo haya salido bien)
            log.debug("Intento de procesamiento de %s finalizado (estado: %s)",
                      self.id, self._estado.value)  # Deja traza de auditoría en el log

    def describir(self):  # Implementación del método abstracto describir()
        costo = f"${self._costo:,.2f}" if self._costo is not None else "sin calcular"  # Formatea el costo si existe
        return (f"{self.id} | {self._cliente.nombre} -> {self._servicio.nombre} | "
                f"{self._duracion} h | {self._estado.value} | {costo}")  # Retorna resumen de la reserva

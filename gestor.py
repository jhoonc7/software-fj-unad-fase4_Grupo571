"""
gestor.py
---------
SistemaSoftwareFJ: administra clientes, servicios y reservas en listas
internas (sin base de datos) y registra cada evento o error en el log.
"""

from .entidades import Cliente  # Importa la clase Cliente
from .excepciones import (  # Importa las excepciones personalizadas para gestionar errores
    ClienteDuplicadoError,
    ClienteInvalidoError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from .registro import obtener_logger  # Importa el generador del archivo de logs
from .reservas import EstadoReserva, Reserva  # Importa Reserva y la enumeración de estados

log = obtener_logger()  # Obtiene la instancia activa del logger


class SistemaSoftwareFJ:
    """Clase fachada (Control Central) que coordina clientes, servicios y reservas."""

    def __init__(self):  # Constructor del gestor principal
        self._clientes = []  # Inicializa lista vacía en memoria para almacenar objetos Cliente
        self._servicios = []  # Inicializa lista vacía en memoria para almacenar objetos Servicio
        self._reservas = []  # Inicializa lista vacía en memoria para almacenar objetos Reserva
        log.info("=== Sistema Software FJ iniciado ===")  # Escribe marca de inicio en software_fj.log

    # ---------------- GESTIÓN DE CLIENTES ----------------
    def registrar_cliente(self, nombre, documento, correo, telefono):
        """Crea y registra un cliente usando try/except/else."""
        if any(c.documento == str(documento).strip() for c in self._clientes):  # Busca si el documento ya está en la lista
            log.error("Cliente duplicado: documento %s", documento)  # Registra el intento duplicado en el log
            raise ClienteDuplicadoError(f"Ya existe un cliente con documento {documento}.")  # Lanza error SFJ-102
        try:  # Intenta instanciar el objeto Cliente (ejecuta los setters de validación)
            cliente = Cliente(nombre, documento, correo, telefono)  # Crea el cliente
        except ClienteInvalidoError as error:  # Si algún dato personal falla la validación...
            log.error("Registro de cliente rechazado: %s", error)  # ...guarda el motivo en el archivo .log
            raise  # ...y propaga la excepción hacia afuera
        else:  # Si el cliente se construyó sin lanzar errores...
            self._clientes.append(cliente)  # ...lo agrega a la lista interna _clientes
            log.info("Cliente registrado: %s", cliente.describir())  # Registra el ingreso exitoso en el log
            return cliente  # Devuelve el objeto Cliente creado

    def buscar_cliente(self, documento):  # Busca un cliente registrado por su número de documento
        for cliente in self._clientes:  # Recorre uno por uno los clientes almacenados en memoria
            if cliente.documento == str(documento).strip():  # Si el documento coincide...
                return cliente  # ...retorna el objeto Cliente encontrado
        raise ClienteInvalidoError(f"No existe un cliente con documento {documento}.")  # Si termina el ciclo sin éxito, lanza error

    # ---------------- GESTIÓN DE SERVICIOS ----------------
    def registrar_servicio(self, clase_servicio, *args, **kwargs):
        """Instancia polimórficamente cualquier subclase de Servicio y la guarda."""
        try:  # Intenta construir el servicio con los argumentos posicionales y nombrados recibidos
            servicio = clase_servicio(*args, **kwargs)  # Llama al constructor de ReservaSala, AlquilerEquipo o Asesoria
        except TypeError as error:  # Si faltan argumentos obligatorios en el llamado a la clase...
            log.error("Faltan parámetros para crear %s: %s", clase_servicio.__name__, error)  # ...lo anota en el log
            raise ServicioNoDisponibleError(  # Encadena el TypeError nativo dentro de ServicioNoDisponibleError
                f"No se pudo crear el servicio {clase_servicio.__name__}: parámetros incompletos."
            ) from error
        except SoftwareFJError as error:  # Si fallan las reglas de negocio (ej. tarifa negativa)...
            log.error("Servicio rechazado: %s", error)  # ...registra el error en el log
            raise  # ...y relanza la excepción
        self._servicios.append(servicio)  # Agrega el servicio válido a la lista interna
        log.info("Servicio registrado: %s", servicio.describir())  # Registra el evento en el log
        return servicio  # Retorna el objeto Servicio creado

    # ---- MEJORA YONATAN CAGUA: Método para buscar servicios por ID y consultar historial por cliente ----
    def buscar_servicio(self, id_servicio):  # Permite localizar un servicio por su código (ej. 'SRV-001')
        for servicio in self._servicios:  # Recorre la lista interna de servicios
            if servicio.id == str(id_servicio).strip().upper():  # Compara el ID normalizado
                return servicio  # Retorna el servicio si lo encuentra
        raise ServicioNoDisponibleError(f"No existe un servicio con ID '{id_servicio}'.")  # Lanza SFJ-301 si no existe

    def obtener_reservas_cliente(self, documento):  # Devuelve todas las reservas asociadas a un cliente
        cliente = self.buscar_cliente(documento)  # Primero valida que el cliente exista usando buscar_cliente
        return [r for r in self._reservas if r.cliente.documento == cliente.documento]  # Filtra reservas por documento

    # ---------------- GESTIÓN DE RESERVAS ----------------
    def crear_reserva(self, cliente, servicio, duracion, **parametros):
        """Crea una reserva en estado pendiente y la almacena en la lista interna."""
        try:  # Intenta instanciar la clase Reserva
            reserva = Reserva(cliente, servicio, duracion, **parametros)  # Ejecuta validaciones al construir
        except ReservaInvalidaError as error:  # Si la creación falla...
            causa = f" (causa: {error.__cause__})" if error.__cause__ else ""  # Extrae la causa raíz si hubo encadenamiento
            log.error("Reserva rechazada: %s%s", error, causa)  # Registra el fallo detallado en el log
            raise  # Propaga el error
        self._reservas.append(reserva)  # Guarda la reserva válida en la lista _reservas
        log.info("Reserva creada: %s", reserva.describir())  # Registra la creación en el log
        return reserva  # Retorna el objeto Reserva

    # ---------------- REPORTES Y ESTADÍSTICAS ----------------
    def resumen(self):
        """Calcula totales operativos y financieros del sistema en memoria."""
        ingresos = sum(r.costo for r in self._reservas if r.estado is EstadoReserva.PROCESADA)  # Suma costos de reservas pagadas
        return {  # Retorna diccionario con métricas consolidadas
            "clientes": len(self._clientes),  # Total de clientes registrados
            "servicios": len(self._servicios),  # Total de servicios en catálogo
            "reservas": len(self._reservas),  # Total de reservas creadas
            "procesadas": sum(r.estado is EstadoReserva.PROCESADA for r in self._reservas),  # Cantidad de reservas pagadas
            "canceladas": sum(r.estado is EstadoReserva.CANCELADA for r in self._reservas),  # Cantidad de reservas anuladas
            "ingresos": ingresos,  # Dinero total recaudado
        }

    @property
    def clientes(self):  # Getter que entrega una copia superficial de la lista de clientes
        return list(self._clientes)  # Protege la lista interna contra modificaciones accidentales externas

    @property
    def servicios(self):  # Getter que entrega una copia de la lista de servicios
        return list(self._servicios)  # Retorna nueva lista con los servicios

    @property
    def reservas(self):  # Getter que entrega una copia de la lista de reservas
        return list(self._reservas)  # Retorna nueva lista con las reservas

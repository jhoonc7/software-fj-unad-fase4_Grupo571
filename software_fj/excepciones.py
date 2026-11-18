"""
excepciones.py
--------------
Jerarquía de excepciones personalizadas del sistema Software FJ.

Todas las excepciones del dominio heredan de SoftwareFJError, lo que permite
capturar cualquier error propio del sistema con un único bloque except y,
al mismo tiempo, distinguir cada caso concreto cuando se necesita.
"""


class SoftwareFJError(Exception):  # Excepción base de todo el sistema
    """Excepción raíz del dominio Software FJ."""

    def __init__(self, mensaje, codigo="SFJ-000"):  # Recibe un mensaje y un código de error
        super().__init__(mensaje)  # Inicializa la clase Exception con el mensaje
        self.mensaje = mensaje  # Guarda el mensaje legible para el usuario
        self.codigo = codigo  # Guarda un código que facilita rastrear el error en los logs

    def __str__(self):  # Representación en texto de la excepción
        return f"[{self.codigo}] {self.mensaje}"  # Ej.: [SFJ-101] El correo no es válido


class ClienteInvalidoError(SoftwareFJError):  # Errores en los datos de un cliente
    """Se lanza cuando los datos personales de un cliente no superan la validación."""

    def __init__(self, mensaje):  # Solo necesita el mensaje
        super().__init__(mensaje, "SFJ-101")  # Asigna el código propio de clientes


class ClienteDuplicadoError(SoftwareFJError):  # Intento de registrar un cliente que ya existe
    """Se lanza cuando se intenta registrar un documento ya existente."""

    def __init__(self, mensaje):  # Solo necesita el mensaje
        super().__init__(mensaje, "SFJ-102")  # Código para duplicados


class ParametroInvalidoError(SoftwareFJError):  # Parámetros faltantes o con valores fuera de rango
    """Se lanza cuando un parámetro obligatorio falta o tiene un valor no permitido."""

    def __init__(self, mensaje):  # Solo necesita el mensaje
        super().__init__(mensaje, "SFJ-201")  # Código para parámetros


class ServicioNoDisponibleError(SoftwareFJError):  # El servicio existe pero no se puede usar
    """Se lanza cuando se intenta reservar un servicio inactivo o inexistente."""

    def __init__(self, mensaje):  # Solo necesita el mensaje
        super().__init__(mensaje, "SFJ-301")  # Código para servicios


class ReservaInvalidaError(SoftwareFJError):  # Errores al crear o procesar reservas
    """Se lanza cuando una reserva no cumple las reglas de negocio."""

    def __init__(self, mensaje):  # Solo necesita el mensaje
        super().__init__(mensaje, "SFJ-401")  # Código para reservas


class OperacionNoPermitidaError(SoftwareFJError):  # Transiciones de estado prohibidas
    """Se lanza cuando se intenta una operación no válida para el estado actual."""

    def __init__(self, mensaje):  # Solo necesita el mensaje
        super().__init__(mensaje, "SFJ-402")  # Código para operaciones no permitidas


class CalculoInconsistenteError(SoftwareFJError):  # Resultados numéricos imposibles
    """Se lanza cuando un cálculo de costos produce un resultado inválido (p. ej., negativo)."""

    def __init__(self, mensaje):  # Solo necesita el mensaje
        super().__init__(mensaje, "SFJ-501")  # Código para cálculos

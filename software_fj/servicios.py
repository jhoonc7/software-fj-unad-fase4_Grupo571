"""
servicios.py
------------
Clase abstracta Servicio y tres servicios especializados:
ReservaSala, AlquilerEquipo y Asesoria.

Cada servicio sobrescribe (polimorfismo) los métodos para calcular el costo
base, describirse y validar sus parámetros. El cálculo final de costos se
ofrece en varias variantes (sobrecarga simulada): sin argumentos opcionales,
con impuesto, con impuesto y descuento, o con un cupón de texto.
"""

from abc import abstractmethod  # Importa el decorador para declarar métodos obligatorios en clases hijas
from functools import singledispatchmethod  # Importa herramienta para sobrecarga de métodos según tipo de dato

from .entidades import EntidadBase  # Importa la clase abstracta raíz del sistema
from .excepciones import (  # Importa las excepciones personalizadas del dominio
    CalculoInconsistenteError,
    ParametroInvalidoError,
    ServicioNoDisponibleError,
)

IVA = 0.19  # Constante con el porcentaje de IVA vigente en Colombia (19%)
CUPONES = {"FJ10": 0.10, "BIENVENIDA": 0.15, "UNAD20": 0.20}  # Diccionario de cupones promocionales válidos


class Servicio(EntidadBase):  # Define la clase abstracta Servicio que hereda de EntidadBase
    """Clase abstracta para todos los servicios que ofrece Software FJ."""

    def __init__(self, nombre, tarifa_hora, disponible=True):  # Constructor con atributos comunes
        super().__init__("SRV")  # Llama al constructor padre asignando el prefijo 'SRV' para el ID
        if not isinstance(nombre, str) or not nombre.strip():  # Valida que el nombre sea un texto no vacío
            raise ParametroInvalidoError("El servicio debe tener un nombre.")  # Lanza error si el nombre falla
        if isinstance(tarifa_hora, bool) or not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:  # Valida número positivo (excluyendo booleanos)
            raise ParametroInvalidoError(f"Tarifa por hora inválida: {tarifa_hora!r}.")  # Lanza error si la tarifa es inválida
        self._nombre = nombre.strip()  # Guarda el nombre limpio en un atributo protegido
        self._tarifa_hora = float(tarifa_hora)  # Convierte y guarda la tarifa como número decimal
        self._disponible = bool(disponible)  # Guarda el estado de disponibilidad como booleano

    @property
    def nombre(self):  # Propiedad getter para leer el nombre de forma segura
        return self._nombre  # Retorna el atributo protegido _nombre

    @property
    def tarifa_hora(self):  # Propiedad getter para leer la tarifa por hora
        return self._tarifa_hora  # Retorna el atributo protegido _tarifa_hora

    @property
    def disponible(self):  # Propiedad getter para saber si el servicio está activo
        return self._disponible  # Retorna True o False según disponibilidad

    def activar(self):  # Método para habilitar el servicio
        self._disponible = True  # Cambia el estado interno a disponible

    def desactivar(self):  # Método para inhabilitar el servicio temporalmente
        self._disponible = False  # Cambia el estado interno a no disponible

    def verificar_disponibilidad(self):  # Método que comprueba si el servicio puede reservarse
        if not self._disponible:  # Si el atributo _disponible es False...
            raise ServicioNoDisponibleError(f"El servicio '{self._nombre}' no está disponible.")  # ...lanza excepción SFJ-301

    @abstractmethod
    def costo_base(self, duracion, **parametros):  # Firma abstracta: obliga a las subclases a definir su fórmula de cobro
        """Calcula el costo base según las reglas propias del servicio."""

    @abstractmethod
    def validar_parametros(self, duracion, **parametros):  # Firma abstracta: obliga a validar datos propios de cada subclase
        """Valida duración y parámetros adicionales del servicio."""

    def validar(self):  # Implementación del método abstracto heredado de EntidadBase
        if self._tarifa_hora <= 0:  # Verifica que la tarifa siga siendo positiva
            raise ParametroInvalidoError("La tarifa debe ser mayor que cero.")  # Lanza error si es cero o negativa
        return True  # Confirma que el servicio es válido

    @staticmethod
    def _validar_duracion(duracion, minimo=1, maximo=12):  # Método estático auxiliar para validar rangos de horas
        if duracion is None:  # Verifica si no se envió la duración
            raise ParametroInvalidoError("Falta la duración de la reserva.")  # Lanza excepción por parámetro faltante
        if not isinstance(duracion, (int, float)) or isinstance(duracion, bool):  # Verifica que sea número real y no booleano
            raise ParametroInvalidoError(f"La duración debe ser numérica, se recibió {duracion!r}.")  # Lanza error de tipo
        if not minimo <= duracion <= maximo:  # Comprueba que las horas estén dentro del límite permitido
            raise ParametroInvalidoError(f"La duración debe estar entre {minimo} y {maximo} horas.")  # Lanza error de rango

    # ---- MEJORA YONATAN CAGUA: Integración de sobrecarga de cupones y bono regalo en calcular_costo ----
    def calcular_costo(self, duracion, impuesto=None, descuento=None, bono_regalo=0, **parametros):
        """Calcula el costo total aplicando sobrecarga de descuentos (porcentaje o cupón), impuestos y bonos."""
        self.validar_parametros(duracion, **parametros)  # Ejecuta la validación polimórfica de la subclase correspondiente
        subtotal = self.costo_base(duracion, **parametros)  # Obtiene el costo base polimórfico según el tipo de servicio
        if descuento is not None:  # Si el usuario proporcionó un descuento (numérico o texto)...
            subtotal = self.aplicar_descuento(descuento, subtotal)  # ...delega al método sobrecargado singledispatchmethod
        if impuesto is not None:  # Si se especificó una tasa de impuesto...
            if isinstance(impuesto, bool) or not 0 <= impuesto <= 1:  # ...valida que sea un porcentaje entre 0 y 100%
                raise ParametroInvalidoError(f"Impuesto fuera de rango: {impuesto}.")  # Lanza error si el impuesto es inválido
            subtotal += subtotal * impuesto  # Suma el valor del impuesto al subtotal
        if bono_regalo:  # Si se incluyó un bono de descuento fijo en dinero...
            subtotal -= bono_regalo  # ...resta el valor del bono al subtotal calculado
        if subtotal <= 0:  # Si el resultado final es cero o negativo...
            raise CalculoInconsistenteError(f"Costo calculado inconsistente: ${subtotal:,.2f}.")  # ...dispara el código SFJ-501
        return round(subtotal, 2)  # Retorna el costo final redondeado a 2 decimales

    @singledispatchmethod
    def aplicar_descuento(self, descuento, monto):  # Método base sobrecargado por tipo de dato
        raise ParametroInvalidoError(f"Tipo de descuento no soportado: {type(descuento).__name__}.")  # Error si el tipo no es int/float/str

    @aplicar_descuento.register(int)  # Registra soporte para enteros (ej. descuento = 0)
    @aplicar_descuento.register(float)  # Registra soporte para decimales (ej. descuento = 0.15)
    def _(self, descuento, monto):  # Implementación para descuentos numéricos porcentuales
        if isinstance(descuento, bool) or not 0 <= descuento < 1:  # Valida que esté entre 0% y 99%
            raise ParametroInvalidoError(f"Descuento fuera de rango: {descuento}.")  # Lanza error SFJ-201 si sale del rango
        return round(monto * (1 - descuento), 2)  # Retorna el monto disminuido en el porcentaje indicado

    @aplicar_descuento.register(str)  # Registra soporte para cadenas de texto (cupones)
    def _(self, descuento: str, monto):  # Implementación para descuentos mediante código promocional
        codigo = descuento.strip().upper()  # Limpia espacios y convierte el código a mayúsculas
        if codigo not in CUPONES:  # Verifica si el cupón existe en el diccionario oficial CUPONES
            raise ParametroInvalidoError(f"El cupón '{descuento}' no existe.")  # Lanza error si el cupón es inválido
        return round(monto * (1 - CUPONES[codigo]), 2)  # Descuenta el porcentaje asociado al cupón


class ReservaSala(Servicio):  # Subclase 1: Servicio de alquiler de salas físicas
    """Reserva de salas de reuniones o capacitación."""

    def __init__(self, nombre, tarifa_hora, capacidad, disponible=True):  # Constructor de ReservaSala
        super().__init__(nombre, tarifa_hora, disponible)  # Inicializa nombre, tarifa y disponibilidad en la superclase
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:  # Valida aforo entero positivo
            raise ParametroInvalidoError(f"Capacidad de sala inválida: {capacidad!r}.")  # Lanza error si la capacidad es incorrecta
        self._capacidad = capacidad  # Guarda el aforo máximo de la sala

    def validar_parametros(self, duracion, **parametros):  # Polimorfismo: validación específica para salas
        self._validar_duracion(duracion, 1, 10)  # Verifica que la sala se reserve entre 1 y 10 horas
        personas = parametros.get("personas")  # Extrae la cantidad de asistentes de los parámetros clave
        if personas is None:  # Verifica si olvidaron indicar cuántas personas asistirán
            raise ParametroInvalidoError("Para reservar una sala indique el número de 'personas'.")  # Error por dato faltante
        if isinstance(personas, bool) or not isinstance(personas, int) or personas <= 0:  # Valida que sea un entero positivo
            raise ParametroInvalidoError(f"Número de personas inválido: {personas!r}.")  # Error si el número es inválido
        if personas > self._capacidad:  # Comprueba si los asistentes superan el aforo máximo de la sala
            raise ParametroInvalidoError(  # Lanza excepción detallando el exceso de aforo
                f"La sala '{self.nombre}' admite {self._capacidad} personas; se pidieron {personas}."
            )

    def costo_base(self, duracion, **parametros):  # Polimorfismo: cálculo de costo para salas
        costo = self.tarifa_hora * duracion  # Multiplica la tarifa horaria por el tiempo de uso
        if parametros.get("personas", 0) > self._capacidad * 0.8:  # Si la ocupación supera el 80% de la capacidad...
            costo *= 1.10  # ...aplica un recargo logístico adicional del 10%
        return costo  # Retorna el costo base de la sala

    def describir(self):  # Polimorfismo: resumen textual de la sala
        estado = "Disponible" if self.disponible else "No disponible"  # Traduce el booleano a texto legible
        return (f"{self.id} | Sala '{self.nombre}' | Capacidad {self._capacidad} | "
                f"${self.tarifa_hora:,.0f}/h | {estado}")  # Retorna la ficha técnica de la sala


class AlquilerEquipo(Servicio):  # Subclase 2: Servicio de préstamo de hardware
    """Alquiler de equipos tecnológicos con control de inventario."""

    def __init__(self, nombre, tarifa_hora, unidades, deposito=0, disponible=True):  # Constructor de AlquilerEquipo
        super().__init__(nombre, tarifa_hora, disponible)  # Inicializa atributos heredados de Servicio
        if isinstance(unidades, bool) or not isinstance(unidades, int) or unidades <= 0:  # Valida stock inicial positivo
            raise ParametroInvalidoError(f"Unidades disponibles inválidas: {unidades!r}.")  # Error si las unidades fallan
        if isinstance(deposito, bool) or deposito < 0:  # Verifica que el depósito en garantía no sea negativo
            raise ParametroInvalidoError("El depósito de garantía no puede ser negativo.")  # Error por depósito inválido
        self._unidades = unidades  # Guarda la cantidad actual de equipos disponibles en inventario
        self._deposito = float(deposito)  # Guarda el monto fijo de garantía

    @property
    def unidades(self):  # Getter para consultar cuántas unidades quedan disponibles
        return self._unidades  # Retorna el stock actual

    # ---- MEJORA YONATAN CAGUA: Métodos para descontar y reintegrar inventario real ----
    def ocupar_unidades(self, cantidad=1):  # Método para descontar equipos cuando se confirma una reserva
        if cantidad > self._unidades:  # Verifica que aún haya stock suficiente al momento de confirmar
            raise ServicioNoDisponibleError(f"Stock insuficiente de '{self.nombre}': quedan {self._unidades}.")
        self._unidades -= cantidad  # Resta las unidades reservadas del inventario

    def liberar_unidades(self, cantidad=1):  # Método para devolver equipos al stock si se cancela la reserva
        self._unidades += cantidad  # Suma nuevamente las unidades al inventario disponible

    def validar_parametros(self, duracion, **parametros):  # Polimorfismo: validación para alquiler de equipos
        self._validar_duracion(duracion, 1, 72)  # Permite alquileres desde 1 hasta 72 horas (3 días)
        cantidad = parametros.get("cantidad", 1)  # Obtiene cuántos equipos se solicitan (1 por defecto)
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:  # Valida entero positivo
            raise ParametroInvalidoError(f"Cantidad de equipos inválida: {cantidad!r}.")  # Lanza error si es inválido
        if cantidad > self._unidades:  # Verifica si piden más equipos de los que existen en bodega
            raise ParametroInvalidoError(  # Lanza excepción informando el límite de inventario
                f"Solo hay {self._unidades} unidades de '{self.nombre}'; se pidieron {cantidad}."
            )

    def costo_base(self, duracion, **parametros):  # Polimorfismo: cálculo de costo para equipos
        cantidad = parametros.get("cantidad", 1)  # Obtiene el número de unidades solicitadas
        return self.tarifa_hora * duracion * cantidad + self._deposito  # Multiplica tarifa * horas * equipos y suma el depósito

    def describir(self):  # Polimorfismo: descripción del equipo y su stock actual
        estado = "Disponible" if self.disponible else "No disponible"  # Traduce estado a texto
        return (f"{self.id} | Equipo '{self.nombre}' | {self._unidades} unid. | "
                f"${self.tarifa_hora:,.0f}/h + depósito ${self._deposito:,.0f} | {estado}")  # Ficha del equipo


class Asesoria(Servicio):  # Subclase 3: Servicio de consultoría profesional
    """Asesorías especializadas con un nivel que modifica la tarifa."""

    NIVELES = {"basico": 1.0, "avanzado": 1.4, "experto": 1.8}  # Multiplicadores de tarifa según experiencia del consultor

    def __init__(self, nombre, tarifa_hora, especialidad, nivel="basico", disponible=True):  # Constructor de Asesoria
        super().__init__(nombre, tarifa_hora, disponible)  # Inicializa atributos base en Servicio
        nivel = str(nivel).lower()  # Convierte el nivel a texto en minúsculas para estandarizar
        if nivel not in self.NIVELES:  # Comprueba si el nivel ingresado existe en el diccionario NIVELES
            raise ParametroInvalidoError(f"Nivel de asesoría '{nivel}' no existe.")  # Error si el nivel no es válido
        if not especialidad or not str(especialidad).strip():  # Verifica que se haya especificado un tema o área
            raise ParametroInvalidoError("La asesoría debe indicar una especialidad.")  # Error si falta especialidad
        self._especialidad = str(especialidad).strip()  # Guarda el área de especialidad limpia
        self._nivel = nivel  # Guarda el nivel de experiencia validado

    def validar_parametros(self, duracion, **parametros):  # Polimorfismo: validación para sesiones de asesoría
        self._validar_duracion(duracion, 1, 8)  # Las asesorías duran mínimo 1 hora y máximo 8 horas por sesión
        modalidad = parametros.get("modalidad", "virtual")  # Toma la modalidad (por defecto 'virtual')
        if modalidad not in ("virtual", "presencial"):  # Verifica que sea una de las dos opciones válidas
            raise ParametroInvalidoError(f"Modalidad '{modalidad}' no válida.")  # Error si escriben otra modalidad

    def costo_base(self, duracion, **parametros):  # Polimorfismo: cálculo de costo para asesorías
        costo = self.tarifa_hora * duracion * self.NIVELES[self._nivel]  # Aplica tarifa por horas y multiplicador de nivel
        if parametros.get("modalidad") == "presencial":  # Si el cliente exige atención presencial...
            costo += 50_000  # ...adiciona un recargo fijo de $50,000 por desplazamiento
        return costo  # Retorna el costo base de la consultoría

    def describir(self):  # Polimorfismo: descripción detallada de la asesoría
        estado = "Disponible" if self.disponible else "No disponible"  # Estado legible
        return (f"{self.id} | Asesoría '{self.nombre}' ({self._especialidad}, nivel {self._nivel}) | "
                f"${self.tarifa_hora:,.0f}/h | {estado}")  # Ficha técnica de la asesoría
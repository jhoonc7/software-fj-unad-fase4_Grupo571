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

from abc import abstractmethod  # Para declarar métodos abstractos
from functools import singledispatchmethod  # Sobrecarga por tipo de argumento

from .entidades import EntidadBase  # Clase abstracta general
from .excepciones import (  # Excepciones propias que usan los servicios
    CalculoInconsistenteError,
    ParametroInvalidoError,
    ServicioNoDisponibleError,
)

IVA = 0.19  # Impuesto al valor agregado vigente en Colombia (19 %)
CUPONES = {"FJ10": 0.10, "BIENVENIDA": 0.15, "UNAD20": 0.20}  # Cupones de descuento válidos


class Servicio(EntidadBase):  # Servicio también es una entidad del sistema
    """Clase abstracta para todos los servicios que ofrece Software FJ."""

    def __init__(self, nombre, tarifa_hora, disponible=True):  # Datos comunes de cualquier servicio
        super().__init__("SRV")  # Id con prefijo SRV
        if not isinstance(nombre, str) or not nombre.strip():  # El nombre es obligatorio
            raise ParametroInvalidoError("El servicio debe tener un nombre.")
        if not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:  # Tarifa numérica positiva
            raise ParametroInvalidoError(f"Tarifa por hora inválida: {tarifa_hora!r}.")
        self._nombre = nombre.strip()  # Atributo protegido: nombre del servicio
        self._tarifa_hora = float(tarifa_hora)  # Atributo protegido: tarifa por hora
        self._disponible = bool(disponible)  # Indica si el servicio puede reservarse

    @property
    def nombre(self):  # Getter del nombre
        return self._nombre

    @property
    def tarifa_hora(self):  # Getter de la tarifa
        return self._tarifa_hora

    @property
    def disponible(self):  # Getter de disponibilidad
        return self._disponible

    def activar(self):  # Habilita el servicio
        self._disponible = True

    def desactivar(self):  # Deshabilita el servicio (mantenimiento, sin personal, etc.)
        self._disponible = False

    def verificar_disponibilidad(self):  # Lanza error si el servicio no se puede usar
        if not self._disponible:  # Si está desactivado...
            raise ServicioNoDisponibleError(f"El servicio '{self._nombre}' no está disponible.")

    # ---------------- métodos que cada subclase DEBE sobrescribir ----------------
    @abstractmethod
    def costo_base(self, duracion, **parametros):  # Costo antes de impuestos y descuentos
        """Calcula el costo base según las reglas propias del servicio."""

    @abstractmethod
    def validar_parametros(self, duracion, **parametros):  # Reglas propias de cada servicio
        """Valida duración y parámetros adicionales del servicio."""

    # ---------------- validación común ----------------
    def validar(self):  # Implementa el método abstracto de EntidadBase
        if self._tarifa_hora <= 0:  # Una tarifa no positiva no tiene sentido
            raise ParametroInvalidoError("La tarifa debe ser mayor que cero.")
        return True

    @staticmethod
    def _validar_duracion(duracion, minimo=1, maximo=12):  # Regla compartida por todos los servicios
        if duracion is None:  # Parámetro faltante
            raise ParametroInvalidoError("Falta la duración de la reserva.")
        if not isinstance(duracion, (int, float)) or isinstance(duracion, bool):  # Debe ser numérica
            raise ParametroInvalidoError(f"La duración debe ser numérica, se recibió {duracion!r}.")
        if not minimo <= duracion <= maximo:  # Debe estar en el rango permitido
            raise ParametroInvalidoError(f"La duración debe estar entre {minimo} y {maximo} horas.")

    # ---------------- cálculo de costos (sobrecarga con parámetros opcionales) ----------------
    def calcular_costo(self, duracion, impuesto=None, descuento=None, **parametros):
        """
        Variantes de uso (sobrecarga simulada):
          calcular_costo(duracion)                       -> costo base
          calcular_costo(duracion, impuesto)             -> base + impuesto
          calcular_costo(duracion, impuesto, descuento)  -> base - descuento + impuesto
        """
        self.validar_parametros(duracion, **parametros)  # Primero valida los datos de entrada
        subtotal = self.costo_base(duracion, **parametros)  # Costo base polimórfico
        if descuento is not None:  # Si se envió descuento...
            if not 0 <= descuento < 1:  # ...debe ser un porcentaje entre 0 y 99 %
                raise ParametroInvalidoError(f"Descuento fuera de rango: {descuento}.")
            subtotal -= subtotal * descuento  # Aplica el descuento
        if impuesto is not None:  # Si se envió impuesto...
            if not 0 <= impuesto <= 1:  # ...debe ser un porcentaje válido
                raise ParametroInvalidoError(f"Impuesto fuera de rango: {impuesto}.")
            subtotal += subtotal * impuesto  # Suma el impuesto
        if subtotal <= 0:  # Un total cero o negativo indica un error de cálculo
            raise CalculoInconsistenteError(f"Costo calculado inconsistente: {subtotal:.2f}.")
        return round(subtotal, 2)  # Devuelve el total redondeado a dos decimales

    # ---------------- sobrecarga por tipo con singledispatchmethod ----------------
    @singledispatchmethod
    def aplicar_descuento(self, descuento, monto):  # Caso por defecto: tipo no soportado
        raise ParametroInvalidoError(f"Tipo de descuento no soportado: {type(descuento).__name__}.")

    @aplicar_descuento.register
    def _(self, descuento: float, monto):  # Variante 1: descuento como porcentaje (0.1 = 10 %)
        if not 0 <= descuento < 1:  # Rango válido
            raise ParametroInvalidoError(f"Porcentaje de descuento inválido: {descuento}.")
        return round(monto * (1 - descuento), 2)  # Monto con descuento

    @aplicar_descuento.register
    def _(self, descuento: str, monto):  # Variante 2: descuento como cupón de texto
        codigo = descuento.strip().upper()  # Normaliza el cupón
        if codigo not in CUPONES:  # Cupón desconocido
            raise ParametroInvalidoError(f"El cupón '{descuento}' no existe.")
        return round(monto * (1 - CUPONES[codigo]), 2)  # Aplica el porcentaje del cupón


class ReservaSala(Servicio):  # Servicio especializado 1
    """Reserva de salas de reuniones o capacitación."""

    def __init__(self, nombre, tarifa_hora, capacidad, disponible=True):
        super().__init__(nombre, tarifa_hora, disponible)  # Inicializa la parte común
        if not isinstance(capacidad, int) or capacidad <= 0:  # La capacidad debe ser un entero positivo
            raise ParametroInvalidoError(f"Capacidad de sala inválida: {capacidad!r}.")
        self._capacidad = capacidad  # Número máximo de personas

    def validar_parametros(self, duracion, **parametros):  # Sobrescritura (polimorfismo)
        self._validar_duracion(duracion, 1, 10)  # Las salas se reservan de 1 a 10 horas
        personas = parametros.get("personas")  # Número de asistentes
        if personas is None:  # Parámetro obligatorio para salas
            raise ParametroInvalidoError("Para reservar una sala indique el número de 'personas'.")
        if not isinstance(personas, int) or personas <= 0:  # Debe ser entero positivo
            raise ParametroInvalidoError(f"Número de personas inválido: {personas!r}.")
        if personas > self._capacidad:  # No puede superar la capacidad
            raise ParametroInvalidoError(
                f"La sala '{self.nombre}' admite {self._capacidad} personas; se pidieron {personas}."
            )

    def costo_base(self, duracion, **parametros):  # Sobrescritura (polimorfismo)
        costo = self.tarifa_hora * duracion  # Tarifa por hora por número de horas
        if parametros.get("personas", 0) > self._capacidad * 0.8:  # Ocupación mayor al 80 %...
            costo *= 1.10  # ...genera un recargo de logística del 10 %
        return costo

    def describir(self):  # Sobrescritura (polimorfismo)
        estado = "Disponible" if self.disponible else "No disponible"
        return (f"{self.id} | Sala '{self.nombre}' | Capacidad {self._capacidad} | "
                f"${self.tarifa_hora:,.0f}/h | {estado}")


class AlquilerEquipo(Servicio):  # Servicio especializado 2
    """Alquiler de equipos tecnológicos (portátiles, videobeam, etc.)."""

    def __init__(self, nombre, tarifa_hora, unidades, deposito=0, disponible=True):
        super().__init__(nombre, tarifa_hora, disponible)  # Parte común
        if not isinstance(unidades, int) or unidades <= 0:  # Inventario positivo
            raise ParametroInvalidoError(f"Unidades disponibles inválidas: {unidades!r}.")
        if deposito < 0:  # El depósito no puede ser negativo
            raise ParametroInvalidoError("El depósito de garantía no puede ser negativo.")
        self._unidades = unidades  # Cantidad de equipos en inventario
        self._deposito = float(deposito)  # Valor fijo de garantía por alquiler

    def validar_parametros(self, duracion, **parametros):  # Sobrescritura (polimorfismo)
        self._validar_duracion(duracion, 1, 72)  # Los equipos se alquilan hasta 72 horas
        cantidad = parametros.get("cantidad", 1)  # Por defecto se alquila un equipo
        if not isinstance(cantidad, int) or cantidad <= 0:  # Entero positivo
            raise ParametroInvalidoError(f"Cantidad de equipos inválida: {cantidad!r}.")
        if cantidad > self._unidades:  # No hay inventario suficiente
            raise ParametroInvalidoError(
                f"Solo hay {self._unidades} unidades de '{self.nombre}'; se pidieron {cantidad}."
            )

    def costo_base(self, duracion, **parametros):  # Sobrescritura (polimorfismo)
        cantidad = parametros.get("cantidad", 1)  # Número de equipos
        return self.tarifa_hora * duracion * cantidad + self._deposito  # Alquiler + depósito

    def describir(self):  # Sobrescritura (polimorfismo)
        estado = "Disponible" if self.disponible else "No disponible"
        return (f"{self.id} | Equipo '{self.nombre}' | {self._unidades} unid. | "
                f"${self.tarifa_hora:,.0f}/h + depósito ${self._deposito:,.0f} | {estado}")


class Asesoria(Servicio):  # Servicio especializado 3
    """Asesorías especializadas con un nivel que modifica la tarifa."""

    NIVELES = {"basico": 1.0, "avanzado": 1.4, "experto": 1.8}  # Multiplicador por nivel

    def __init__(self, nombre, tarifa_hora, especialidad, nivel="basico", disponible=True):
        super().__init__(nombre, tarifa_hora, disponible)  # Parte común
        nivel = str(nivel).lower()  # Normaliza el nivel
        if nivel not in self.NIVELES:  # Solo se aceptan los niveles definidos
            raise ParametroInvalidoError(f"Nivel de asesoría '{nivel}' no existe.")
        if not especialidad:  # La especialidad es obligatoria
            raise ParametroInvalidoError("La asesoría debe indicar una especialidad.")
        self._especialidad = especialidad  # Área de la asesoría
        self._nivel = nivel  # Nivel del asesor

    def validar_parametros(self, duracion, **parametros):  # Sobrescritura (polimorfismo)
        self._validar_duracion(duracion, 1, 8)  # Una asesoría dura entre 1 y 8 horas
        modalidad = parametros.get("modalidad", "virtual")  # Virtual por defecto
        if modalidad not in ("virtual", "presencial"):  # Modalidades permitidas
            raise ParametroInvalidoError(f"Modalidad '{modalidad}' no válida.")

    def costo_base(self, duracion, **parametros):  # Sobrescritura (polimorfismo)
        costo = self.tarifa_hora * duracion * self.NIVELES[self._nivel]  # Tarifa ajustada por nivel
        if parametros.get("modalidad") == "presencial":  # La modalidad presencial...
            costo += 50_000  # ...suma un valor fijo de desplazamiento
        return costo

    def describir(self):  # Sobrescritura (polimorfismo)
        estado = "Disponible" if self.disponible else "No disponible"
        return (f"{self.id} | Asesoría '{self.nombre}' ({self._especialidad}, nivel {self._nivel}) | "
                f"${self.tarifa_hora:,.0f}/h | {estado}")

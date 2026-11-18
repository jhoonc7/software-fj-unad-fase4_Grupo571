"""
entidades.py
------------
Clase abstracta EntidadBase y clase Cliente.

EntidadBase representa cualquier entidad general del sistema (clientes,
servicios, reservas): todas tienen un identificador, una fecha de creación
y deben saber validarse y describirse.
"""

import re  # Expresiones regulares para validar correo y teléfono
from abc import ABC, abstractmethod  # Herramientas para definir clases abstractas
from datetime import datetime  # Para registrar la fecha de creación

from .excepciones import ClienteInvalidoError  # Excepción propia para datos de clientes


class EntidadBase(ABC):  # Clase abstracta: no se puede instanciar directamente
    """Entidad general del sistema con identificador y fecha de creación."""

    _contadores = {}  # Contador por prefijo (CLI, SRV, RES) para generar identificadores únicos

    def __init__(self, prefijo):  # El prefijo distingue el tipo (CLI, SRV, RES)
        self._prefijo = prefijo  # Guarda el prefijo del tipo de entidad
        self._id = None  # El id se asigna solo cuando el objeto se crea correctamente
        self._fecha_creacion = datetime.now()  # Guarda el momento de creación

    @property
    def id(self):  # Propiedad de solo lectura para el identificador
        if self._id is None:  # La primera vez que se consulta...
            numero = EntidadBase._contadores.get(self._prefijo, 0) + 1  # ...toma el siguiente número
            EntidadBase._contadores[self._prefijo] = numero  # Actualiza el contador del prefijo
            self._id = f"{self._prefijo}-{numero:03d}"  # Construye un id como CLI-001
        return self._id  # Devuelve el id encapsulado

    @property
    def fecha_creacion(self):  # Propiedad de solo lectura para la fecha
        return self._fecha_creacion  # Devuelve la fecha encapsulada

    @abstractmethod
    def validar(self):  # Cada entidad define sus propias reglas de validación
        """Valida el estado interno de la entidad; lanza excepción si es inválido."""

    @abstractmethod
    def describir(self):  # Cada entidad define cómo se presenta en texto
        """Devuelve una descripción legible de la entidad."""

    def __str__(self):  # La representación en texto reutiliza describir()
        return self.describir()  # Polimorfismo: cada subclase da su propia descripción


class Cliente(EntidadBase):  # Cliente hereda de la entidad general
    """Cliente de Software FJ con datos personales encapsulados y validados."""

    PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")  # Formato básico usuario@dominio.ext
    PATRON_TELEFONO = re.compile(r"^\d{7,10}$")  # Entre 7 y 10 dígitos

    def __init__(self, nombre, documento, correo, telefono):  # Datos personales obligatorios
        super().__init__("CLI")  # Genera el id con prefijo CLI
        self.nombre = nombre  # Usa el setter: valida el nombre
        self.documento = documento  # Usa el setter: valida el documento
        self.correo = correo  # Usa el setter: valida el correo
        self.telefono = telefono  # Usa el setter: valida el teléfono
        self.validar()  # Validación final del objeto completo

    # ---------- nombre ----------
    @property
    def nombre(self):  # Getter del nombre
        return self.__nombre  # Atributo privado (name mangling)

    @nombre.setter
    def nombre(self, valor):  # Setter con validación
        if not isinstance(valor, str) or not valor.strip():  # Debe ser texto no vacío
            raise ClienteInvalidoError("El nombre es obligatorio y debe ser texto.")
        if len(valor.strip()) < 3:  # Mínimo tres caracteres
            raise ClienteInvalidoError("El nombre debe tener al menos 3 caracteres.")
        if any(c.isdigit() for c in valor):  # No se permiten números en el nombre
            raise ClienteInvalidoError(f"El nombre '{valor}' no puede contener números.")
        self.__nombre = valor.strip().title()  # Guarda el nombre limpio y capitalizado

    # ---------- documento ----------
    @property
    def documento(self):  # Getter del documento
        return self.__documento  # Atributo privado

    @documento.setter
    def documento(self, valor):  # Setter con validación
        valor = str(valor).strip() if valor is not None else ""  # Convierte a texto y limpia espacios
        if not valor.isdigit() or not 6 <= len(valor) <= 12:  # Solo dígitos, entre 6 y 12
            raise ClienteInvalidoError(f"Documento '{valor}' inválido: use de 6 a 12 dígitos.")
        self.__documento = valor  # Guarda el documento validado

    # ---------- correo ----------
    @property
    def correo(self):  # Getter del correo
        return self.__correo  # Atributo privado

    @correo.setter
    def correo(self, valor):  # Setter con validación
        if not isinstance(valor, str) or not self.PATRON_CORREO.match(valor.strip()):  # Debe cumplir el patrón
            raise ClienteInvalidoError(f"El correo '{valor}' no tiene un formato válido.")
        self.__correo = valor.strip().lower()  # Guarda el correo en minúsculas

    # ---------- teléfono ----------
    @property
    def telefono(self):  # Getter del teléfono
        return self.__telefono  # Atributo privado

    @telefono.setter
    def telefono(self, valor):  # Setter con validación
        valor = str(valor).strip() if valor is not None else ""  # Convierte a texto
        if not self.PATRON_TELEFONO.match(valor):  # Debe tener de 7 a 10 dígitos
            raise ClienteInvalidoError(f"El teléfono '{valor}' debe tener entre 7 y 10 dígitos.")
        self.__telefono = valor  # Guarda el teléfono validado

    def validar(self):  # Implementación obligatoria del método abstracto
        """Verifica que todos los datos estén presentes después de construir el objeto."""
        for campo in ("nombre", "documento", "correo", "telefono"):  # Recorre los campos obligatorios
            if not getattr(self, campo, None):  # Si alguno quedó vacío...
                raise ClienteInvalidoError(f"Falta el campo obligatorio '{campo}'.")  # ...se informa
        return True  # El cliente es válido

    def describir(self):  # Implementación obligatoria del método abstracto
        correo_oculto = self.__correo[:3] + "***" + self.__correo[self.__correo.index("@"):]  # Protege el dato personal
        return f"{self.id} | {self.nombre} | Doc. {self.documento} | {correo_oculto}"  # Texto resumido

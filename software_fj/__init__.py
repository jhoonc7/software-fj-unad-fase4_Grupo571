"""Paquete Software FJ: gestión de clientes, servicios y reservas sin base de datos."""

from .entidades import Cliente, EntidadBase  # Entidades generales
from .gestor import SistemaSoftwareFJ  # Fachada del sistema
from .reservas import EstadoReserva, Reserva  # Reservas
from .servicios import AlquilerEquipo, Asesoria, ReservaSala, Servicio  # Servicios

__all__ = [  # Elementos públicos del paquete
    "EntidadBase", "Cliente", "Servicio", "ReservaSala", "AlquilerEquipo",
    "Asesoria", "Reserva", "EstadoReserva", "SistemaSoftwareFJ",
]

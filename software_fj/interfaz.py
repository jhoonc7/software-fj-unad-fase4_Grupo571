import tkinter as tk
"""
interfaz.py
-----------

Interfaz gráfica desarrollada mediante Tkinter para
visualizar los servicios implementados en Software FJ.

Esta interfaz permite evidenciar la aplicación práctica
de conceptos como:

- Abstracción
- Herencia
- Polimorfismo
- Programación Orientada a Objetos
"""
from software_fj.servicios import (
    ReservaSala,
    AlquilerEquipo,
    Asesoria
)


def mostrar_servicios():

    servicios = [

        ReservaSala(
            "Sala Innovacion",
            50000,
            20
        ),

        AlquilerEquipo(
            "Portatil Lenovo",
            30000,
            10
        ),

        Asesoria(
            "Python",
            80000,
            "Programacion"
        )

    ]

    resultado = ""

    for servicio in servicios:

        resultado += (
            servicio.describir()
            + "\n\n"
        )

    texto.config(text=resultado)


ventana = tk.Tk()

ventana.title(
    "Software FJ"
)

ventana.geometry(
    "800x500"
)

titulo = tk.Label(
    ventana,
    text="Sistema Integral de Gestion de Clientes, Servicios y Reservas",
    font=("Arial", 12, "bold")
)

titulo.pack(pady=15)

boton = tk.Button(
    ventana,
    text="Mostrar Servicios",
    command=mostrar_servicios
)

boton.pack(pady=10)

texto = tk.Label(
    ventana,
    justify="left"
)

texto.pack(pady=20)

ventana.mainloop()

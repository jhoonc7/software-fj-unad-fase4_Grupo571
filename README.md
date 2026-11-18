# Software FJ — Sistema Integral de Gestión de Clientes, Servicios y Reservas

Proyecto de la **Fase 4 – Prácticas simuladas** del curso **Programación (213023)** – UNAD.
Aplicación orientada a objetos en Python, **sin base de datos**, que gestiona clientes, servicios
(reservas de salas, alquiler de equipos y asesorías especializadas) y reservas, con manejo avanzado
de excepciones y registro de eventos en un archivo de logs.

## Requisitos

- Python 3.10 o superior (no requiere librerías externas).

## Ejecución

```bash
python main.py
```

El programa ejecuta 26 operaciones simuladas (válidas e inválidas) y al final muestra un reporte.
Todos los eventos y errores quedan en `logs/software_fj.log`.

## Estructura

```
software-fj/
├── main.py                  # Simulación de 26 operaciones y reporte final
├── software_fj/
│   ├── __init__.py          # Exporta las clases públicas del paquete
│   ├── excepciones.py       # Jerarquía de excepciones personalizadas
│   ├── registro.py          # Configuración del archivo de logs
│   ├── entidades.py         # Clase abstracta EntidadBase y clase Cliente
│   ├── servicios.py         # Clase abstracta Servicio + ReservaSala, AlquilerEquipo, Asesoria
│   ├── reservas.py          # Clase Reserva y estados (confirmar, cancelar, procesar)
│   └── gestor.py            # SistemaSoftwareFJ: listas internas y operaciones
└── logs/
    └── software_fj.log      # Se genera al ejecutar
```

## Conceptos aplicados

| Concepto | Dónde |
|---|---|
| Abstracción | `EntidadBase` y `Servicio` (heredan de `ABC`, métodos `@abstractmethod`) |
| Herencia | `Cliente`, `Servicio`, `Reserva` ← `EntidadBase`; `ReservaSala`, `AlquilerEquipo`, `Asesoria` ← `Servicio` |
| Polimorfismo | `costo_base()`, `validar_parametros()` y `describir()` sobrescritos en cada servicio |
| Encapsulación | Atributos privados (`__nombre`, `__correo`…) con `@property` y setters que validan |
| Sobrecarga | `calcular_costo(duracion[, impuesto[, descuento[, bono_regalo]]])` y `aplicar_descuento()` con `singledispatchmethod` (porcentaje `int`/`float` o cupón `str`) |
| Excepciones personalizadas | `SoftwareFJError` y 7 subclases con código de error (`SFJ-101` a `SFJ-501`) |
| `try/except` | `Reserva.validar()`, `gestor.registrar_servicio()` |
| `try/except/else` | `Reserva.confirmar()`, `gestor.registrar_cliente()` |
| `try/except/finally` | `Reserva.procesar()`, `main.ejecutar()` |
| Encadenamiento (`raise … from …`) | `TypeError` → `ServicioNoDisponibleError`; `ParametroInvalidoError` → `ReservaInvalidaError`; `ValueError` → `ParametroInvalidoError` |
| Logs | `logging` en `logs/software_fj.log` (INFO, WARNING, ERROR, DEBUG) |

## Operaciones simuladas

| # | Operación | Resultado esperado |
|---|---|---|
| 1, 4 | Registrar clientes válidos | Éxito |
| 2, 3 | Cliente con correo inválido / nombre con números | Error controlado |
| 5 | Cliente con documento duplicado | Error controlado |
| 6–8 | Crear sala, alquiler de equipo y asesoría | Éxito |
| 9, 10 | Servicio con tarifa negativa / nivel inexistente | Error controlado |
| 11 | Servicio sin parámetros obligatorios | Error encadenado (`TypeError`) |
| 12 | Reserva de sala: crear, confirmar y pagar | Éxito |
| 13 | Reserva que excede la capacidad | Error encadenado |
| 14, 15 | Pago insuficiente y reintento correcto | Error y luego éxito |
| 16 | Reservar servicio desactivado | Error encadenado |
| 17 | Procesar una reserva cancelada | Operación no permitida |
| 18 | Reserva sin duración | Error encadenado |
| 19 | Variantes sobrecargadas de costos y descuentos | Éxito |
| 20 | Descuento fuera de rango | Error controlado |
| 21 | Buscar cliente inexistente por documento | Error controlado (`SFJ-101`) |
| 22 | Reserva aplicando cupón `'UNAD20'` al confirmar y búsqueda por ID | Éxito |
| 23 | Intentar aplicar un cupón promocional inexistente | Error controlado (`SFJ-201`) |
| 24 | Procesar pago con texto inválido (no numérico) | Error encadenado (`ValueError` → `SFJ-201`) |
| 25 | Cálculo inconsistente por bono regalo mayor al subtotal | Error controlado (`SFJ-501`) |
| 26 | Verificar descuento real de stock en equipos e historial por cliente | Éxito |

## Integrantes – Grupo 213023_571

| Integrante | Aporte en el repositorio |
|---|---|
| Jhon Frey Acosta Gómez | Estructura del proyecto, `excepciones.py`, `registro.py`, `main.py` |
| Yonatan Fabian Cagua Lopez | `entidades.py` (EntidadBase y Cliente), control de stock en equipos (`servicios.py`, `reservas.py`), integración de cupones en reservas, consultas en `gestor.py`, pruebas 21–26 y documentación línea a línea |
| Integrante 3 | `servicios.py` (Servicio y servicios especializados) |
| Integrante 4 | `reservas.py` (Reserva y estados) |
| Integrante 5 | `gestor.py`, pruebas y documentación |

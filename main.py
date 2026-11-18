"""
main.py
-------
Simulación de operaciones del Sistema Integral de Gestión de Clientes,
Servicios y Reservas de Software FJ.

Se ejecutan 20 operaciones con casos válidos e inválidos para demostrar
que la aplicación sigue funcionando ante errores y que cada evento queda
registrado en logs/software_fj.log.

Ejecución:  python main.py
"""

from software_fj import AlquilerEquipo, Asesoria, ReservaSala, SistemaSoftwareFJ  # Clases del sistema
from software_fj.excepciones import SoftwareFJError  # Excepción base del dominio
from software_fj.registro import ARCHIVO_LOG, obtener_logger  # Ruta del log y logger
from software_fj.servicios import IVA  # Tasa de IVA

log = obtener_logger()  # Logger del programa principal
resultados = {"exitosas": 0, "fallidas": 0}  # Contador de operaciones


def ejecutar(numero, descripcion, operacion):
    """
    Ejecuta una operación protegida con try/except/else/finally.
    La aplicación NUNCA se detiene: cualquier error queda informado y registrado.
    """
    print(f"\n[{numero:02d}] {descripcion}")  # Encabezado de la operación
    try:  # Intenta ejecutar la operación
        resultado = operacion()  # Llama a la función recibida
    except SoftwareFJError as error:  # Errores esperados del dominio
        resultados["fallidas"] += 1  # Cuenta la operación fallida
        print(f"     ✗ ERROR CONTROLADO: {error}")  # Muestra el error al usuario
        if error.__cause__ is not None:  # Si el error fue encadenado...
            print(f"       ↳ causa original: {type(error.__cause__).__name__}: {error.__cause__}")
        log.warning("Operación %02d fallida: %s", numero, error)  # Registro en el log
    except Exception as error:  # Red de seguridad para errores inesperados
        resultados["fallidas"] += 1
        print(f"     ✗ ERROR INESPERADO: {type(error).__name__}: {error}")
        log.critical("Operación %02d con error inesperado: %r", numero, error, exc_info=True)
    else:  # Solo si no hubo excepción
        resultados["exitosas"] += 1  # Cuenta la operación exitosa
        if resultado is not None:  # Si la operación devolvió algo...
            print(f"     ✓ OK: {resultado}")  # ...se muestra
        else:
            print("     ✓ OK")
    finally:  # Se ejecuta siempre
        log.debug("Operación %02d finalizada", numero)  # Traza de cierre


def main():
    sistema = SistemaSoftwareFJ()  # Crea el sistema con listas vacías
    ctx = {}  # Diccionario para compartir objetos entre operaciones

    print("=" * 78)
    print(" SOFTWARE FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas")
    print("=" * 78)

    # ------------------------- CLIENTES -------------------------
    def op1():  # Cliente válido
        ctx["ana"] = sistema.registrar_cliente("ana maría rojas", "1012345678", "ana.rojas@correo.com", "3104567890")
        return ctx["ana"].describir()
    ejecutar(1, "Registrar cliente válido (Ana María Rojas)", op1)

    ejecutar(2, "Registrar cliente con correo inválido",
             lambda: sistema.registrar_cliente("Pedro Gómez", "80123456", "pedro.gomez@", "3001234567"))

    ejecutar(3, "Registrar cliente con números en el nombre y teléfono corto",
             lambda: sistema.registrar_cliente("Luis 2024", "79111222", "luis@correo.com", "123"))

    def op4():  # Segundo cliente válido
        ctx["carlos"] = sistema.registrar_cliente("Carlos Pérez", "1098765432", "carlos.perez@empresa.co", "3209876543")
        return ctx["carlos"].describir()
    ejecutar(4, "Registrar cliente válido (Carlos Pérez)", op4)

    ejecutar(5, "Registrar cliente con documento duplicado",
             lambda: sistema.registrar_cliente("Otra Persona", "1012345678", "otra@correo.com", "3111111111"))

    # ------------------------- SERVICIOS -------------------------
    def op6():  # Servicio de sala
        ctx["sala"] = sistema.registrar_servicio(ReservaSala, "Sala Innovación", 80_000, capacidad=20)
        return ctx["sala"].describir()
    ejecutar(6, "Crear servicio: Reserva de sala", op6)

    def op7():  # Servicio de equipos
        ctx["equipo"] = sistema.registrar_servicio(AlquilerEquipo, "Portátil Core i7", 15_000, unidades=10, deposito=100_000)
        return ctx["equipo"].describir()
    ejecutar(7, "Crear servicio: Alquiler de equipos", op7)

    def op8():  # Servicio de asesoría
        ctx["asesoria"] = sistema.registrar_servicio(Asesoria, "Arquitectura de Software", 120_000,
                                                     especialidad="Python POO", nivel="experto")
        return ctx["asesoria"].describir()
    ejecutar(8, "Crear servicio: Asesoría especializada", op8)

    ejecutar(9, "Crear servicio con tarifa negativa",
             lambda: sistema.registrar_servicio(ReservaSala, "Sala Error", -5000, capacidad=10))

    ejecutar(10, "Crear asesoría con nivel inexistente",
             lambda: sistema.registrar_servicio(Asesoria, "Ciberseguridad", 90_000, especialidad="Redes", nivel="maestro"))

    ejecutar(11, "Crear alquiler de equipo sin parámetros obligatorios (encadenamiento)",
             lambda: sistema.registrar_servicio(AlquilerEquipo, "Videobeam"))

    # ------------------------- RESERVAS -------------------------
    def op12():  # Flujo completo exitoso
        r = sistema.crear_reserva(ctx["ana"], ctx["sala"], 3, personas=18)  # 18 > 80 % de 20: recargo
        costo = r.confirmar()  # Confirma con IVA por defecto
        cambio = r.procesar(400_000)  # Paga en efectivo
        return f"{r.describir()} | cambio ${cambio:,.2f}"
    ejecutar(12, "Reserva de sala: crear, confirmar (IVA 19 %) y procesar pago", op12)

    ejecutar(13, "Reserva de sala que excede la capacidad",
             lambda: sistema.crear_reserva(ctx["carlos"], ctx["sala"], 2, personas=35))

    def op14():  # Pago insuficiente
        ctx["r_equipo"] = sistema.crear_reserva(ctx["carlos"], ctx["equipo"], 24, cantidad=3)
        ctx["r_equipo"].confirmar(IVA, 0.10)  # Variante con impuesto y descuento
        return ctx["r_equipo"].procesar(200_000)  # El pago no alcanza
    ejecutar(14, "Alquiler de 3 portátiles con 10 % de descuento y pago insuficiente", op14)

    ejecutar(15, "Reintentar el pago del alquiler con el valor correcto",
             lambda: f"cambio ${ctx['r_equipo'].procesar(1_500_000):,.2f} | {ctx['r_equipo'].describir()}")

    def op16():  # Servicio desactivado
        ctx["asesoria"].desactivar()  # Simula que el asesor no está disponible
        try:
            return sistema.crear_reserva(ctx["ana"], ctx["asesoria"], 2)
        finally:
            ctx["asesoria"].activar()  # Se reactiva para las siguientes operaciones
    ejecutar(16, "Reservar una asesoría mientras el servicio está desactivado", op16)

    def op17():  # Cancelación y luego intento de procesar
        r = sistema.crear_reserva(ctx["carlos"], ctx["asesoria"], 2, modalidad="presencial")
        r.confirmar()
        r.cancelar("El cliente reprogramó su agenda")
        return r.procesar(1_000_000)  # No se puede procesar una reserva cancelada
    ejecutar(17, "Confirmar y cancelar una asesoría; intentar procesarla después", op17)

    ejecutar(18, "Crear reserva con duración faltante",
             lambda: sistema.crear_reserva(ctx["ana"], ctx["equipo"], None, cantidad=1))

    # ------------------------- SOBRECARGA DE MÉTODOS -------------------------
    def op19():  # Variantes de calcular_costo y aplicar_descuento
        a = ctx["asesoria"]
        v1 = a.calcular_costo(2)  # Solo duración
        v2 = a.calcular_costo(2, IVA)  # Duración + impuesto
        v3 = a.calcular_costo(2, IVA, 0.15)  # Duración + impuesto + descuento
        v4 = a.aplicar_descuento(0.20, v2)  # Descuento como porcentaje (float)
        v5 = a.aplicar_descuento("FJ10", v2)  # Descuento como cupón (str)
        return (f"base ${v1:,.0f} | +IVA ${v2:,.0f} | +IVA-15 % ${v3:,.0f} | "
                f"20 % ${v4:,.0f} | cupón FJ10 ${v5:,.0f}")
    ejecutar(19, "Sobrecarga: variantes de cálculo de costos y descuentos", op19)

    ejecutar(20, "Cálculo con descuento fuera de rango (150 %)",
             lambda: ctx["sala"].calcular_costo(2, IVA, 1.5, personas=5))

    # ------------------------- REPORTE FINAL -------------------------
    print("\n" + "=" * 78)
    print(" REPORTE FINAL")
    print("=" * 78)
    for r in sistema.reservas:  # Lista todas las reservas registradas
        print("  •", r.describir())
    datos = sistema.resumen()  # Totales del sistema
    print(f"\n  Clientes: {datos['clientes']} | Servicios: {datos['servicios']} | "
          f"Reservas: {datos['reservas']} (procesadas {datos['procesadas']}, canceladas {datos['canceladas']})")
    print(f"  Ingresos procesados: ${datos['ingresos']:,.2f}")
    print(f"  Operaciones exitosas: {resultados['exitosas']} | con error controlado: {resultados['fallidas']}")
    print(f"  Log de eventos: {ARCHIVO_LOG}")
    print("\n  El sistema terminó la simulación sin interrupciones.")
    log.info("=== Simulación finalizada: %s ===", resultados)


if __name__ == "__main__":  # Punto de entrada del programa
    main()

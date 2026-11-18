"""Reglas del módulo de alquileres.

HU-3.05 (incluido): tarifario por tipo de vehículo y, como excepción, por unidad (VIN), con
modalidad (diaria, semanal, mensual o por kilometraje), moneda, monto, kilometraje incluido, precio
por kilómetro adicional y vigencia. Una tarifa nunca se edita: un cambio es una tarifa nueva con
su vigencia y la abierta anterior se cierra el día previo, así un contrato que copió los valores al
firmarse no se altera (criterio 4). No se traslapan vigencias del mismo (tipo de vehículo o VIN,
modalidad, moneda).
HU-3.05 (diferido): aprobación del gerente financiero de descuentos sobre el porcentaje configurado
(criterio 3, Sprint 3, con el contrato).

Para otros módulos: `tarifa_vigente` (el contrato, HU-3.06, copia el resultado al firmarse).

shortcut: el traslape se revisa en el service sin restricción de exclusión en la base; dos altas
simultáneas del mismo grupo podrían traslaparse, se cambia a EXCLUDE (btree_gist) si el tarifario
llega a editarse en paralelo.

HU-3.06 (incluido): contrato con cliente (`facturacion`), unidad (VIN), salida, devolución
prevista, kilometraje y combustible de salida (octavos de tanque, 0 a 8), depósito esperado y
número correlativo. Copia los valores de la tarifa vigente el día de salida, así un cambio
posterior del tarifario no lo altera. El contrato se registra al salir la unidad: la unidad debe
estar en flota y sin otro contrato abierto (un contrato abierto la retiene hasta su cierre, así que
se traslapa con cualquier fecha nueva) y pasa a "alquilada" con `unidades.cambiar_estado`, en la
misma transacción. Monto estimado = periodos × monto de la tarifa (`_periodos`):
- días = días calendario entre la fecha de salida y la devolución prevista, mínimo 1;
- diaria: un periodo por día; semanal: semanas iniciadas (días / 7, hacia arriba); mensual: meses
  de 30 días iniciados; por kilometraje: un solo periodo (el monto cubre los km incluidos y el
  resto se cobra por km adicional). Los km incluidos de la tarifa son por periodo.
  Supuesto para el contador: las tres reglas anteriores y que los montos de tarifa incluyen IVA.
La impresión es la vista de detalle del front.
HU-3.06 (diferido): quién registra si los usuarios son solo contables (pendiente de la historia);
reservas a futuro (el contrato no admite salida en un día posterior a hoy).

HU-3.08 (incluido): cierre con fecha y hora de devolución, kilometraje y combustible de entrada y
observaciones de daños. Calcula, con la tarifa copiada:
- días efectivos = periodos de 24 horas iniciados desde la salida, mínimo 1 (supuesto para el
  contador: sin horas de gracia);
- km recorridos = entrada − salida; km excedentes = recorridos − km incluidos × periodos, si es
  positivo; combustible faltante = octavos de salida − octavos de entrada, si es positivo;
- monto final = periodos × monto de la tarifa + km excedentes × precio por km adicional.
El kilometraje de entrada actualiza el de la unidad (nunca retrocede) y la unidad vuelve a "en
flota", todo en la misma transacción. Un contrato cerrado no se vuelve a cerrar ni se edita.
Para `facturacion`: `resumen_para_facturar` (líneas del cobro de un contrato cerrado).
HU-3.08 (diferido): el cobro en dinero del combustible faltante y otros cargos adicionales
(HU-3.09, Sprint 3; hoy solo se muestra el faltante en octavos); abrir la orden de taller por daños
y dejar la unidad "en taller" (órdenes de mantenimiento, Sprint 5).

HU-3.07 (incluido): depósito en garantía ligado al contrato abierto, en la moneda recibida, a una
cuenta bancaria activa de esa moneda. Es pasivo: partida (`deposito_garantia`) débito al banco y
crédito a depósitos en garantía (regla `pasivo_gtq`/`pasivo_usd`); en USD las dos líneas van en
dólares y cuadran al tipo de cambio del día. Una autorización de tarjeta sin cobro queda solo como
referencia, sin partida ni saldo. Con el contrato cerrado el depósito se aplica, total o
parcialmente, a sus cargos (`aplicacion_deposito`: débito al pasivo, crédito a la cuenta por
cobrar al cliente; nunca más que el saldo ni que el monto final del contrato, y en la moneda del
contrato) y el resto se devuelve (`devolucion_deposito`: débito al pasivo, crédito al banco; una
sola vez y nunca más que el saldo). Cada documento y su partida se confirman juntos o nada. La
consulta de vigentes da el saldo de cada uno y el total por moneda (`saldo_depositos`).
Supuesto para el contador: la aplicación y la devolución debitan el pasivo de la regla vigente.
HU-3.07 (diferido): bajar el saldo de la cuenta por cobrar de la factura al aplicar el depósito
(cobros, HU-6.07, Sprint 3; hoy solo se contabiliza contra la cuenta por cobrar); aplicar un
depósito en una moneda distinta a la del contrato; cobrar una autorización de tarjeta.
"""

import math
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.comun.dinero import redondear
from app.comun.errores import ErrorNegocio
from app.modulos.alquileres.models import (
    MODALIDADES,
    ContratoAlquiler,
    DepositoGarantia,
    MovimientoDeposito,
    Tarifa,
)
from app.modulos.alquileres.schemas import (
    AplicacionEntrada,
    CierreEntrada,
    ContratoEntrada,
    DepositoEntrada,
    DevolucionDepositoEntrada,
    TarifaEntrada,
)
from app.modulos.configuracion import service as configuracion
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaEntrada
from app.modulos.facturacion import service as facturacion
from app.modulos.unidades import service as unidades

_LIMITE_MONTO = Decimal("1000000000000")
_BLOQUEO_CONTRATOS = 20261806  # candado de transacción: correlativo y disponibilidad de contratos


def _monto(texto: str, campo: str, permite_cero: bool) -> Decimal:
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        raise ErrorNegocio(f"{campo} no es un número válido") from None
    if not valor.is_finite():
        raise ErrorNegocio(f"{campo} no es un número válido")
    if -valor.as_tuple().exponent > 6:  # type: ignore[operator]
        raise ErrorNegocio(f"{campo} admite hasta 6 decimales")
    if valor < 0 or (valor == 0 and not permite_cero):
        raise ErrorNegocio(
            f"{campo} {'no puede ser negativo' if permite_cero else 'debe ser mayor que cero'}"
        )
    if valor >= _LIMITE_MONTO:
        raise ErrorNegocio(f"{campo} excede el máximo permitido")
    return valor


def _misma_clave(consulta, tipo_vehiculo: str | None, vin: str | None, modalidad: str, moneda: str):
    por = Tarifa.vin == vin if vin else Tarifa.tipo_vehiculo == tipo_vehiculo
    return consulta.where(por, Tarifa.modalidad == modalidad, Tarifa.moneda == moneda)


def registrar_tarifa(db: Session, datos: TarifaEntrada) -> Tarifa:
    if bool(datos.tipo_vehiculo) == bool(datos.vin):
        raise ErrorNegocio("Indique el tipo de vehículo o, como excepción, el VIN de la unidad (solo uno)")
    vin = None
    if datos.vin:
        vin = unidades.validar_vin(datos.vin)
        if not unidades.existe_vin(db, vin):
            raise ErrorNegocio(f"No existe una unidad con el VIN {vin}")
    elif datos.tipo_vehiculo not in unidades.TIPOS_VEHICULO:
        raise ErrorNegocio(f"Tipo de vehículo desconocido. Use uno de: {', '.join(unidades.TIPOS_VEHICULO)}")
    monto = _monto(datos.monto, "El monto", permite_cero=False)
    precio_km = _monto(datos.precio_km_adicional, "El precio por kilómetro adicional", permite_cero=True)
    desde, hasta = datos.vigente_desde, datos.vigente_hasta
    if hasta is not None and hasta < desde:
        raise ErrorNegocio("La vigencia termina antes de empezar")

    existentes = db.scalars(
        _misma_clave(select(Tarifa), datos.tipo_vehiculo, vin, datos.modalidad, datos.moneda)
        .where(Tarifa.vigente_hasta.is_(None) | (Tarifa.vigente_hasta >= desde))
        .with_for_update()
    ).all()
    por_cerrar = []
    for tarifa in existentes:
        if hasta is not None and tarifa.vigente_desde > hasta:
            continue
        # La abierta que empezó antes se cierra el día previo, solo si la nueva también es abierta.
        if tarifa.vigente_hasta is None and tarifa.vigente_desde < desde and hasta is None:
            por_cerrar.append(tarifa)
            continue
        raise ErrorNegocio(
            f"La vigencia se traslapa con la tarifa {tarifa.id} (desde {tarifa.vigente_desde}"
            f"{f' hasta {tarifa.vigente_hasta}' if tarifa.vigente_hasta else ''}); "
            "cierre esa tarifa con una nueva que empiece después",
            status=409,
        )
    for tarifa in por_cerrar:
        tarifa.vigente_hasta = desde - timedelta(days=1)

    tarifa = Tarifa(
        tipo_vehiculo=None if vin else datos.tipo_vehiculo,
        vin=vin,
        modalidad=datos.modalidad,
        moneda=datos.moneda,
        monto=monto,
        km_incluido=datos.km_incluido,
        precio_km_adicional=precio_km,
        vigente_desde=desde,
        vigente_hasta=hasta,
    )
    db.add(tarifa)
    db.commit()
    db.refresh(tarifa)
    return tarifa


def listar_tarifas(
    db: Session, tipo_vehiculo: str | None = None, vin: str | None = None, modalidad: str | None = None
) -> list[Tarifa]:
    """Todas las tarifas (vigentes, cerradas y futuras), de la más reciente a la más antigua."""
    consulta = select(Tarifa).order_by(Tarifa.vigente_desde.desc(), Tarifa.id.desc())
    if tipo_vehiculo:
        consulta = consulta.where(Tarifa.tipo_vehiculo == tipo_vehiculo)
    if vin:
        consulta = consulta.where(Tarifa.vin == vin.strip().upper())
    if modalidad:
        consulta = consulta.where(Tarifa.modalidad == modalidad)
    return list(db.scalars(consulta))


def tarifa_vigente(
    db: Session, fecha: date, modalidad: str, moneda: str, tipo_vehiculo: str, vin: str | None = None
) -> Tarifa:
    """La tarifa que aplica en `fecha`: la de la unidad (VIN) si la tiene; si no, la de su tipo de
    vehículo. Sin ninguna, `ErrorNegocio` (404)."""

    def buscar(por) -> Tarifa | None:
        return db.scalars(
            select(Tarifa).where(
                por,
                Tarifa.modalidad == modalidad,
                Tarifa.moneda == moneda,
                Tarifa.vigente_desde <= fecha,
                Tarifa.vigente_hasta.is_(None) | (Tarifa.vigente_hasta >= fecha),
            )
        ).first()

    tarifa = (vin and buscar(Tarifa.vin == vin.strip().upper())) or buscar(
        Tarifa.tipo_vehiculo == tipo_vehiculo
    )
    if tarifa is None:
        raise ErrorNegocio(
            f"No hay tarifa {modalidad} en {moneda} vigente el {fecha} para {tipo_vehiculo}", status=404
        )
    return tarifa


def catalogos() -> dict[str, list[str]]:
    return {
        "modalidades": list(MODALIDADES),
        "monedas": ["GTQ", "USD"],
        "tipos_vehiculo": list(unidades.TIPOS_VEHICULO),
    }


# ── HU-3.06: contratos ─────────────────────────────────────────────────────────


def _periodos(modalidad: str, dias: int) -> int:
    """Periodos de la tarifa que cubren `dias` (ver la regla en el docstring del módulo)."""
    if modalidad == "semanal":
        return math.ceil(dias / 7)
    if modalidad == "mensual":
        return math.ceil(dias / 30)
    if modalidad == "por_kilometraje":
        return 1
    return dias


def registrar_contrato(
    db: Session, datos: ContratoEntrada, usuario_id: int | None = None
) -> ContratoAlquiler:
    """Registra el contrato y pasa la unidad a "alquilada" en una transacción, o nada."""
    cliente = facturacion.obtener_cliente(db, datos.cliente_id)
    vin = unidades.validar_vin(datos.vin)
    # Serializa los contratos: correlativo sin repetirse y una sola salida por unidad a la vez.
    db.execute(text("SELECT pg_advisory_xact_lock(:llave)"), {"llave": _BLOQUEO_CONTRATOS})
    unidad = unidades.obtener_por_vin(db, vin)
    salida_dia = datos.salida.date()
    if salida_dia > date.today():
        raise ErrorNegocio(
            "El contrato se registra al salir la unidad: la salida no puede ser en un día futuro"
        )
    if datos.devolucion_prevista < salida_dia:
        raise ErrorNegocio("La devolución prevista no puede ser antes de la salida")
    if unidad.kilometraje is not None and datos.km_salida < unidad.kilometraje:
        raise ErrorNegocio(
            f"El kilometraje de salida no puede ser menor que el de la unidad ({unidad.kilometraje} km)"
        )
    deposito = _monto(datos.deposito_esperado, "El depósito esperado", permite_cero=True)

    if unidad.estado != "en_flota":
        raise ErrorNegocio(f"La unidad {vin} no está disponible: su estado es {unidad.estado}", status=409)
    abierto = db.scalar(
        select(ContratoAlquiler.numero).where(
            ContratoAlquiler.vin == vin, ContratoAlquiler.estado == "abierto"
        )
    )
    if abierto is not None:
        raise ErrorNegocio(f"La unidad {vin} ya tiene abierto el contrato {abierto}", status=409)
    tarifa = tarifa_vigente(db, salida_dia, datos.modalidad, datos.moneda, unidad.tipo_vehiculo, vin)

    dias = max((datos.devolucion_prevista - salida_dia).days, 1)
    contrato = ContratoAlquiler(
        numero=(db.scalar(select(func.max(ContratoAlquiler.numero))) or 0) + 1,
        cliente_id=cliente.id,
        vin=vin,
        salida=datos.salida,
        devolucion_prevista=datos.devolucion_prevista,
        tarifa_id=tarifa.id,
        modalidad=tarifa.modalidad,
        moneda=tarifa.moneda,
        tarifa_monto=tarifa.monto,
        km_incluido=tarifa.km_incluido,
        precio_km_adicional=tarifa.precio_km_adicional,
        km_salida=datos.km_salida,
        combustible_salida=datos.combustible_salida,
        deposito_esperado=deposito,
        dias_previstos=dias,
        monto_estimado=redondear(tarifa.monto * _periodos(tarifa.modalidad, dias)),
        estado="abierto",
        usuario_id=usuario_id,
    )
    db.add(contrato)
    try:
        db.flush()
        unidades.cambiar_estado(
            db, vin, "alquilada", f"Contrato de alquiler {contrato.numero}", usuario_id, confirmar=False
        )
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    db.refresh(contrato)
    return contrato


def listar_contratos(
    db: Session, estado: str | None = None, vin: str | None = None
) -> list[ContratoAlquiler]:
    """Contratos del más reciente al más antiguo, opcionalmente por estado o unidad."""
    consulta = select(ContratoAlquiler).order_by(ContratoAlquiler.numero.desc())
    if estado:
        consulta = consulta.where(ContratoAlquiler.estado == estado)
    if vin:
        consulta = consulta.where(ContratoAlquiler.vin == vin.strip().upper())
    return list(db.scalars(consulta))


def obtener_contrato(db: Session, contrato_id: int) -> ContratoAlquiler:
    contrato = db.get(ContratoAlquiler, contrato_id)
    if contrato is None:
        raise ErrorNegocio("El contrato no existe", status=404)
    return contrato


# ── HU-3.08: cierre ────────────────────────────────────────────────────────────


def _cargos(contrato: ContratoAlquiler) -> tuple[int, Decimal, Decimal]:
    """(periodos, cargo por tiempo, cargo por km excedentes) de un contrato cerrado."""
    periodos = _periodos(contrato.modalidad, contrato.dias_efectivos)
    return (
        periodos,
        contrato.tarifa_monto * periodos,
        contrato.precio_km_adicional * contrato.km_excedentes,
    )


def cerrar_contrato(
    db: Session, contrato_id: int, datos: CierreEntrada, usuario_id: int | None = None
) -> ContratoAlquiler:
    """Registra la devolución, calcula el cierre, actualiza la unidad y la regresa a la flota, en
    una transacción, o nada."""
    contrato = db.get(ContratoAlquiler, contrato_id, with_for_update=True)
    if contrato is None:
        raise ErrorNegocio("El contrato no existe", status=404)
    if contrato.estado == "cerrado":
        raise ErrorNegocio(f"El contrato {contrato.numero} ya está cerrado", status=409)
    if datos.devolucion < contrato.salida:
        raise ErrorNegocio("La devolución no puede ser antes de la salida")
    if datos.devolucion > datetime.now(UTC):
        raise ErrorNegocio("La devolución no puede ser en el futuro")
    if datos.km_devolucion < contrato.km_salida:
        raise ErrorNegocio(
            f"El kilometraje de entrada no puede ser menor que el de salida ({contrato.km_salida} km)"
        )

    contrato.devolucion = datos.devolucion
    contrato.km_devolucion = datos.km_devolucion
    contrato.combustible_devolucion = datos.combustible_devolucion
    contrato.observaciones_danos = (datos.observaciones_danos or "").strip() or None
    contrato.dias_efectivos = max(math.ceil((datos.devolucion - contrato.salida) / timedelta(days=1)), 1)
    periodos = _periodos(contrato.modalidad, contrato.dias_efectivos)
    contrato.km_recorridos = datos.km_devolucion - contrato.km_salida
    contrato.km_excedentes = max(contrato.km_recorridos - contrato.km_incluido * periodos, 0)
    contrato.combustible_faltante = max(contrato.combustible_salida - datos.combustible_devolucion, 0)
    _, tiempo, excedente = _cargos(contrato)
    contrato.monto_final = redondear(tiempo + excedente)
    contrato.estado = "cerrado"
    contrato.cerrado_por = usuario_id
    try:
        db.flush()
        unidades.fijar_kilometraje(db, contrato.vin, datos.km_devolucion)
        # Si la unidad ya salió de "alquilada" a mano (por ejemplo, al taller), se respeta ese estado.
        if unidades.obtener_por_vin(db, contrato.vin).estado == "alquilada":
            unidades.cambiar_estado(
                db, contrato.vin, "en_flota", f"Cierre del contrato de alquiler {contrato.numero}",
                usuario_id, confirmar=False,
            )  # fmt: skip
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    db.refresh(contrato)
    return contrato


def resumen_para_facturar(db: Session, contrato_id: int) -> dict:
    """Para `facturacion` (factura de cierre): cliente, moneda, VIN, línea de negocio y las líneas
    del cobro de un contrato cerrado, con cantidades y precios en Decimal.

    Supuesto para el contador: los montos de la tarifa son precios con IVA incluido.
    """
    contrato = obtener_contrato(db, contrato_id)
    if contrato.estado != "cerrado":
        raise ErrorNegocio(f"El contrato {contrato.numero} no está cerrado; ciérrelo antes de facturar", 409)
    periodos, _, _ = _cargos(contrato)
    unidad_tiempo = {
        "diaria": "días",
        "semanal": "semanas",
        "mensual": "meses",
        "por_kilometraje": "contrato",
    }
    lineas = [
        {
            "descripcion": f"Alquiler de la unidad {contrato.vin}, contrato {contrato.numero} "
            f"({periodos} {unidad_tiempo[contrato.modalidad]})",
            "cantidad": Decimal(periodos),
            "precio_unitario": contrato.tarifa_monto,
        }
    ]
    if contrato.km_excedentes:
        lineas.append(
            {
                "descripcion": f"Kilómetros excedentes, contrato {contrato.numero}",
                "cantidad": Decimal(contrato.km_excedentes),
                "precio_unitario": contrato.precio_km_adicional,
            }
        )
    return {
        "cliente_id": contrato.cliente_id,
        "moneda": contrato.moneda,
        "vin": contrato.vin,
        "linea_negocio": "alquiler",
        "lineas": lineas,
    }


# ── HU-3.07: depósitos en garantía ─────────────────────────────────────────────


def _banco(db: Session, cuenta_bancaria_id: int, moneda: str) -> int:
    """Cuenta contable de una cuenta bancaria activa en `moneda`."""
    banco = configuracion.obtener_cuenta_bancaria(db, cuenta_bancaria_id)
    if not banco.activa:
        raise ErrorNegocio(f"La cuenta bancaria {banco.banco} {banco.numero} está inactiva")
    if banco.moneda != moneda:
        raise ErrorNegocio(
            f"La cuenta bancaria {banco.banco} {banco.numero} es en {banco.moneda}, no en {moneda}"
        )
    return banco.cuenta_id


def _pasivo(db: Session, moneda: str) -> int:
    return contabilidad.cuenta_regla(db, "deposito_garantia", f"pasivo_{moneda.lower()}")


def _linea(db: Session, cuenta_id: int, lado: str, monto: Decimal, moneda: str, vin: str) -> LineaEntrada:
    """Línea en la moneda del depósito, en la línea de alquiler y con el VIN si la cuenta lo admite."""
    admite_vin = configuracion.obtener_cuenta(db, cuenta_id).vin != configuracion.VIN_NO_APLICA
    return LineaEntrada(
        cuenta_id=cuenta_id,
        lado=lado,
        monto=f"{monto:.6f}",
        moneda=moneda,
        linea_negocio="alquiler",
        vin=vin if admite_vin else None,
    )


def _confirmar_con_partida(
    db: Session,
    documento: DepositoGarantia | MovimientoDeposito,
    documento_tipo: str,
    concepto: str,
    debe: int,
    haber: int,
    deposito: DepositoGarantia,
    usuario_id: int | None,
) -> None:
    """Escribe el documento, pide su partida y confirma los dos, o revierte todo."""
    db.add(documento)
    try:
        db.flush()  # el id del documento liga su partida
        contabilidad.registrar_automatica(
            db,
            fecha=documento.fecha,
            concepto=concepto[:300],
            lineas=[
                _linea(db, debe, "debe", documento.monto, deposito.moneda, deposito.vin),
                _linea(db, haber, "haber", documento.monto, deposito.moneda, deposito.vin),
            ],
            documento_tipo=documento_tipo,
            documento_id=documento.id,
            usuario_id=usuario_id,
        )
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise


def _validar_fecha(fecha: date) -> None:
    if fecha > date.today():
        raise ErrorNegocio("La fecha no puede ser futura")


def recibir_deposito(
    db: Session, contrato_id: int, datos: DepositoEntrada, usuario_id: int | None = None
) -> DepositoGarantia:
    """Registra el depósito del contrato abierto con su partida (pasivo), o la autorización de
    tarjeta solo como referencia."""
    contrato = obtener_contrato(db, contrato_id)
    if contrato.estado != "abierto":
        raise ErrorNegocio(
            f"El contrato {contrato.numero} está cerrado; el depósito se recibe con el contrato abierto"
        )
    _validar_fecha(datos.fecha)
    monto = _monto(datos.monto, "El monto del depósito", permite_cero=False)
    referencia = (datos.referencia or "").strip() or None
    deposito = DepositoGarantia(
        contrato_id=contrato.id,
        vin=contrato.vin,
        tipo=datos.tipo,
        fecha=datos.fecha,
        moneda=datos.moneda,
        monto=monto,
        saldo=monto,
        referencia=referencia,
        usuario_id=usuario_id,
    )
    if datos.tipo == "autorizacion_tarjeta":
        if referencia is None or datos.cuenta_bancaria_id is not None:
            raise ErrorNegocio("La autorización de tarjeta lleva su referencia y no una cuenta bancaria")
        deposito.saldo = Decimal(0)  # no es dinero recibido: sin saldo ni partida
        db.add(deposito)
        db.commit()
        db.refresh(deposito)
        return deposito

    if datos.cuenta_bancaria_id is None:
        raise ErrorNegocio("Indique la cuenta bancaria donde se recibió el depósito")
    banco = _banco(db, datos.cuenta_bancaria_id, datos.moneda)
    pasivo = _pasivo(db, datos.moneda)
    deposito.cuenta_bancaria_id = datos.cuenta_bancaria_id
    _confirmar_con_partida(
        db, deposito, "deposito_garantia",
        f"Depósito en garantía del contrato de alquiler {contrato.numero}, unidad {contrato.vin}",
        banco, pasivo, deposito, usuario_id,
    )  # fmt: skip
    db.refresh(deposito)
    return deposito


def _deposito_para_mover(db: Session, deposito_id: int, monto_texto: str) -> tuple[DepositoGarantia, Decimal]:
    """Depósito en dinero de un contrato cerrado, con el contrato bloqueado (los movimientos de un
    mismo contrato van de uno en uno) y el monto validado contra su saldo."""
    deposito = db.get(DepositoGarantia, deposito_id)
    if deposito is None:
        raise ErrorNegocio("El depósito no existe", status=404)
    contrato = db.get(ContratoAlquiler, deposito.contrato_id, with_for_update=True, populate_existing=True)
    db.refresh(deposito)
    if deposito.tipo != "deposito":
        raise ErrorNegocio("Una autorización de tarjeta no tiene saldo que aplicar o devolver")
    if contrato.estado != "cerrado":
        raise ErrorNegocio(f"El depósito se aplica o devuelve al cerrar el contrato {contrato.numero}")
    monto = _monto(monto_texto, "El monto", permite_cero=False)
    if monto > deposito.saldo:
        raise ErrorNegocio(f"El monto excede el saldo del depósito ({deposito.saldo:.2f} {deposito.moneda})")
    return deposito, monto


def aplicar_deposito(
    db: Session, deposito_id: int, datos: AplicacionEntrada, usuario_id: int | None = None
) -> DepositoGarantia:
    """Aplica parte o todo el saldo a los cargos del contrato cerrado, con su partida.

    Pendiente (HU-6.07, cobros, Sprint 3): bajar el saldo del documento por cobrar de la factura
    del contrato; hoy la aplicación solo se contabiliza contra la cuenta por cobrar al cliente.
    """
    _validar_fecha(datos.fecha)
    deposito, monto = _deposito_para_mover(db, deposito_id, datos.monto)
    contrato = deposito.contrato
    if deposito.moneda != contrato.moneda:
        raise ErrorNegocio(f"El depósito es en {deposito.moneda} y el contrato en {contrato.moneda}")
    aplicado = db.scalar(
        select(func.coalesce(func.sum(MovimientoDeposito.monto), 0))
        .join(DepositoGarantia, DepositoGarantia.id == MovimientoDeposito.deposito_id)
        .where(DepositoGarantia.contrato_id == contrato.id, MovimientoDeposito.tipo == "aplicacion")
    )
    if aplicado + monto > contrato.monto_final:
        raise ErrorNegocio(
            "Lo aplicado excedería el monto final del contrato "
            f"({contrato.monto_final:.2f} {contrato.moneda}; ya aplicado {aplicado:.2f})"
        )
    por_cobrar = contabilidad.cuenta_regla(db, "aplicacion_deposito", f"por_cobrar_{deposito.moneda.lower()}")
    pasivo = _pasivo(db, deposito.moneda)
    deposito.saldo -= monto
    movimiento = MovimientoDeposito(
        deposito_id=deposito.id, tipo="aplicacion", fecha=datos.fecha, monto=monto, usuario_id=usuario_id
    )
    _confirmar_con_partida(
        db, movimiento, "aplicacion_deposito",
        f"Aplicación del depósito en garantía a los cargos del contrato de alquiler {contrato.numero}",
        pasivo, por_cobrar, deposito, usuario_id,
    )  # fmt: skip
    db.refresh(deposito)
    return deposito


def devolver_deposito(
    db: Session, deposito_id: int, datos: DevolucionDepositoEntrada, usuario_id: int | None = None
) -> DepositoGarantia:
    """Devuelve al cliente el saldo (o parte) desde una cuenta bancaria, con su partida; una vez."""
    _validar_fecha(datos.fecha)
    deposito, monto = _deposito_para_mover(db, deposito_id, datos.monto)
    ya_devuelto = db.scalar(
        select(MovimientoDeposito.id).where(
            MovimientoDeposito.deposito_id == deposito.id, MovimientoDeposito.tipo == "devolucion"
        )
    )
    if ya_devuelto is not None:
        raise ErrorNegocio("El depósito ya se devolvió; no se puede devolver dos veces", status=409)
    banco = _banco(db, datos.cuenta_bancaria_id, deposito.moneda)
    pasivo = _pasivo(db, deposito.moneda)
    deposito.saldo -= monto
    movimiento = MovimientoDeposito(
        deposito_id=deposito.id,
        tipo="devolucion",
        fecha=datos.fecha,
        monto=monto,
        cuenta_bancaria_id=datos.cuenta_bancaria_id,
        usuario_id=usuario_id,
    )
    _confirmar_con_partida(
        db, movimiento, "devolucion_deposito",
        f"Devolución del depósito en garantía del contrato de alquiler {deposito.contrato.numero}",
        pasivo, banco, deposito, usuario_id,
    )  # fmt: skip
    db.refresh(deposito)
    return deposito


def depositos_de_contrato(db: Session, contrato_id: int) -> list[DepositoGarantia]:
    obtener_contrato(db, contrato_id)
    return list(
        db.scalars(
            select(DepositoGarantia)
            .where(DepositoGarantia.contrato_id == contrato_id)
            .order_by(DepositoGarantia.id)
        )
    )


def depositos_vigentes(db: Session) -> list[DepositoGarantia]:
    """Depósitos en dinero con saldo, del más antiguo al más reciente."""
    return list(
        db.scalars(
            select(DepositoGarantia)
            .where(DepositoGarantia.tipo == "deposito", DepositoGarantia.saldo > 0)
            .order_by(DepositoGarantia.fecha, DepositoGarantia.id)
        )
    )


def saldo_depositos(db: Session) -> dict[str, Decimal]:
    """Para el cuadre con el mayor: saldo total de los depósitos vigentes por moneda.

    Pendiente (coordinador, con HU-2.16): comparar cada total con el saldo de su cuenta de pasivo
    (reglas `deposito_garantia`) en el mayor; en USD, contra el saldo en dólares de la cuenta.
    """
    totales = dict(
        db.execute(
            select(DepositoGarantia.moneda, func.sum(DepositoGarantia.saldo))
            .where(DepositoGarantia.tipo == "deposito")
            .group_by(DepositoGarantia.moneda)
        ).all()
    )
    return {moneda: totales.get(moneda, Decimal(0)) for moneda in ("GTQ", "USD")}

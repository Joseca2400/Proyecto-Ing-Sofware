"""E1 (multimoneda) y E2 (partidas, contabilización y consultas)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Cuenta,
    EstadoPartida,
    ExigenciaVin,
    LineaPartida,
    Moneda,
    Partida,
    TipoCambio,
    Unidad,
    Usuario,
)
from app.services.base import (
    Conflicto,
    ErrorNegocio,
    NoEncontrado,
    Prohibido,
    obtener,
    q2,
    registrar_bitacora,
)

SISTEMA = "SISTEMA"


# ======================================================================= Tipo de cambio (HU-1.06)

def registrar_tipo_cambio(db: Session, fecha: date, valor: Decimal, usuario: str) -> TipoCambio:
    if valor <= 0:
        raise ErrorNegocio("El tipo de cambio debe ser mayor que 0")
    existente = db.scalar(select(TipoCambio).where(TipoCambio.fecha == fecha))
    if existente:
        if tipo_cambio_usado(db, fecha):
            raise Conflicto(
                f"El tipo de cambio del {fecha} ya se usó en partidas contabilizadas; "
                "corregirlo requiere aprobación del gerente financiero"
            )
        existente.valor = valor
        existente.registrado_por = usuario
        db.commit()
        return existente
    tc = TipoCambio(fecha=fecha, valor=valor, origen="MANUAL", registrado_por=usuario)
    db.add(tc)
    db.flush()
    db.commit()
    return tc


def tipo_cambio_usado(db: Session, fecha: date) -> bool:
    return bool(db.scalar(
        select(func.count()).select_from(LineaPartida).join(Partida)
        .where(Partida.fecha == fecha, Partida.estado == EstadoPartida.CONTABILIZADA,
               LineaPartida.moneda == Moneda.USD)
    ))


def tipo_cambio_de(db: Session, fecha: date) -> Decimal:
    """Tipo de cambio de la fecha; si no existe, la transacción en USD no se puede registrar."""
    tc = db.scalar(select(TipoCambio).where(TipoCambio.fecha == fecha))
    if tc is None:
        raise ErrorNegocio(
            f"No hay tipo de cambio registrado para el {fecha:%d/%m/%Y}. "
            "Regístrelo antes de guardar transacciones en dólares."
        )
    return tc.valor


# ======================================================================= Construcción de partidas

@dataclass
class LineaIn:
    """Línea de partida tal como la arma un módulo o el usuario."""

    cuenta: str                      # código de cuenta
    lado: str                        # DEBE / HABER
    monto: Decimal                   # en la moneda de la línea
    moneda: str = Moneda.GTQ
    linea_negocio: str | None = None
    unidad_id: int | None = None
    detalle: str | None = None
    tipo_cambio: Decimal | None = None   # sólo para forzar un TC distinto al del Banguat
    monto_q: Decimal | None = None       # para cuadrar exacto en partidas automáticas


def _cuenta(db: Session, codigo: str) -> Cuenta:
    cuenta = db.scalar(select(Cuenta).where(Cuenta.codigo == codigo))
    if cuenta is None:
        raise ErrorNegocio(f"La cuenta {codigo} no existe")
    if not cuenta.activa:
        raise ErrorNegocio(f"La cuenta {codigo} está inactiva y no acepta movimientos")
    if not cuenta.es_detalle:
        raise ErrorNegocio(f"La cuenta {codigo} es de agrupación; sólo las de detalle reciben movimientos")
    return cuenta


def _construir_lineas(db: Session, fecha: date, lineas: list[LineaIn]) -> list[LineaPartida]:
    if len(lineas) < 2:
        raise ErrorNegocio("La partida debe tener al menos dos líneas")
    resultado = []
    for i, l in enumerate(lineas, start=1):
        try:
            cuenta = _cuenta(db, l.cuenta)
            if l.monto <= 0:
                raise ErrorNegocio("el monto debe ser mayor que 0")
            if l.lado not in ("DEBE", "HABER"):
                raise ErrorNegocio("el lado debe ser DEBE o HABER")

            linea_neg = l.linea_negocio or cuenta.linea_defecto
            if not linea_neg:
                raise ErrorNegocio(f"la cuenta {cuenta.codigo} exige indicar la línea de negocio")

            if cuenta.exige_vin == ExigenciaVin.OBLIGATORIO and l.unidad_id is None:
                raise ErrorNegocio(f"la cuenta {cuenta.codigo} ({cuenta.nombre}) exige el VIN de la unidad")
            if cuenta.exige_vin == ExigenciaVin.NO_APLICA and l.unidad_id is not None:
                raise ErrorNegocio(f"la cuenta {cuenta.codigo} no lleva VIN")
            if l.unidad_id is not None:
                obtener(db, Unidad, l.unidad_id, "La unidad")

            if l.moneda == Moneda.USD:
                tc = l.tipo_cambio or tipo_cambio_de(db, fecha)
                monto_q = l.monto_q if l.monto_q is not None else q2(l.monto * tc)
                original = l.monto
            else:
                tc, original, monto_q = None, None, q2(l.monto)
        except ErrorNegocio as e:
            raise ErrorNegocio(f"Línea {i}: {e.mensaje}", e.status) from None

        resultado.append(LineaPartida(
            cuenta_id=cuenta.id,
            debe=monto_q if l.lado == "DEBE" else Decimal("0"),
            haber=monto_q if l.lado == "HABER" else Decimal("0"),
            moneda=l.moneda, monto_original=original, tipo_cambio=tc,
            linea_negocio=linea_neg, unidad_id=l.unidad_id, detalle=l.detalle,
        ))
    return resultado


def diferencia(partida_o_lineas) -> Decimal:
    lineas = partida_o_lineas.lineas if isinstance(partida_o_lineas, Partida) else partida_o_lineas
    return sum((l.debe for l in lineas), Decimal("0")) - sum((l.haber for l in lineas), Decimal("0"))


def _validar_cuadre(lineas) -> None:
    dif = diferencia(lineas)
    if dif != 0:
        raise ErrorNegocio(f"La partida no cuadra en quetzales: diferencia de Q{dif:,.2f}")


def _siguiente_numero(db: Session) -> int:
    return (db.scalar(select(func.max(Partida.numero))) or 0) + 1


# ======================================================================= Partidas manuales (HU-2.01, HU-2.02)

def crear_partida_manual(db: Session, fecha: date, concepto: str, lineas: list[LineaIn], usuario: str,
                         justificacion_tc: str | None = None) -> Partida:
    if any(l.tipo_cambio for l in lineas) and not justificacion_tc:
        raise ErrorNegocio("Para usar un tipo de cambio distinto al del Banguat debe indicar la justificación")
    partida = Partida(fecha=fecha, concepto=concepto, estado=EstadoPartida.BORRADOR,
                      registrada_por=usuario, lineas=_construir_lineas(db, fecha, lineas))
    db.add(partida)
    db.flush()
    if justificacion_tc:
        registrar_bitacora(db, usuario, "TC_DISTINTO", "Partida", partida.id, detalle=justificacion_tc)
    db.commit()
    return partida


def editar_partida(db: Session, partida_id: int, fecha: date, concepto: str, lineas: list[LineaIn],
                   usuario: str, justificacion_tc: str | None = None) -> Partida:
    """Corrige un borrador o una partida devuelta. Sólo quien la registró; vuelve a borrador."""
    partida = obtener(db, Partida, partida_id, "La partida")
    if partida.estado not in (EstadoPartida.BORRADOR, EstadoPartida.DEVUELTA):
        raise Conflicto(f"Sólo se corrigen partidas en borrador o devueltas (estado: {partida.estado})")
    if partida.automatica:
        raise Conflicto("Una partida automática se corrige desde su documento de origen")
    if partida.registrada_por != usuario:
        raise Prohibido("Sólo quien registró la partida puede corregirla")
    if any(l.tipo_cambio for l in lineas) and not justificacion_tc:
        raise ErrorNegocio("Para usar un tipo de cambio distinto al del Banguat debe indicar la justificación")
    nuevas = _construir_lineas(db, fecha, lineas)
    partida.lineas.clear()
    db.flush()
    partida.fecha, partida.concepto = fecha, concepto
    partida.lineas.extend(nuevas)
    partida.estado = EstadoPartida.BORRADOR
    if justificacion_tc:
        registrar_bitacora(db, usuario, "TC_DISTINTO", "Partida", partida.id, detalle=justificacion_tc)
    db.commit()
    db.refresh(partida)
    return partida


def enviar_a_revision(db: Session, partida_id: int, usuario: str) -> Partida:
    partida = obtener(db, Partida, partida_id, "La partida")
    if partida.estado not in (EstadoPartida.BORRADOR, EstadoPartida.DEVUELTA):
        raise Conflicto(f"Sólo se envían a revisión partidas en borrador o devueltas (estado: {partida.estado})")
    _validar_cuadre(partida)
    partida.estado = EstadoPartida.EN_REVISION
    registrar_bitacora(db, usuario, "ENVIAR_REVISION", "Partida", partida.id)
    db.commit()
    return partida


def contabilizar(db: Session, partida_id: int, usuario: Usuario) -> Partida:
    partida = obtener(db, Partida, partida_id, "La partida")
    if partida.estado != EstadoPartida.EN_REVISION:
        raise Conflicto(f"Sólo se contabilizan partidas en revisión (estado: {partida.estado})")
    # HU-1.10: quien registra no aprueba, aunque su rol lo permita.
    if partida.registrada_por == usuario.usuario:
        raise Prohibido("Quien registró la partida no puede contabilizarla (separación de funciones)")
    partida.estado = EstadoPartida.CONTABILIZADA
    partida.contabilizada_por = usuario.usuario
    partida.numero = _siguiente_numero(db)
    registrar_bitacora(db, usuario.usuario, "CONTABILIZAR", "Partida", partida.id, detalle=f"No. {partida.numero}")
    db.commit()
    return partida


def devolver(db: Session, partida_id: int, usuario: Usuario, comentario: str) -> Partida:
    partida = obtener(db, Partida, partida_id, "La partida")
    if partida.estado != EstadoPartida.EN_REVISION:
        raise Conflicto("Sólo se devuelven partidas en revisión")
    if partida.registrada_por == usuario.usuario:
        raise Prohibido("Quien registró la partida no puede revisarla")
    partida.estado = EstadoPartida.DEVUELTA
    partida.comentario_revision = comentario
    registrar_bitacora(db, usuario.usuario, "DEVOLVER", "Partida", partida.id, detalle=comentario)
    db.commit()
    return partida


# ======================================================================= Partidas automáticas (HU-2.03)

def partida_automatica(db: Session, fecha: date, concepto: str, lineas: list[LineaIn],
                       origen_tipo: str, origen_id: int, usuario: str) -> Partida:
    """Genera y contabiliza la partida de un documento. No hace commit: va en la transacción del documento.

    Si falta una cuenta o la partida no cuadra, se lanza el error y el documento no se confirma.
    """
    construidas = _construir_lineas(db, fecha, lineas)
    _validar_cuadre(construidas)
    partida = Partida(
        fecha=fecha, concepto=concepto, estado=EstadoPartida.CONTABILIZADA, automatica=True,
        origen_tipo=origen_tipo, origen_id=origen_id, registrada_por=usuario,
        contabilizada_por=SISTEMA, numero=_siguiente_numero(db), lineas=construidas,
    )
    db.add(partida)
    db.flush()
    return partida


# ======================================================================= Consultas (HU-2.16)

def _movimientos(db: Session, desde: date | None, hasta: date | None,
                 linea_negocio: str | None, unidad_id: int | None):
    stmt = (
        select(LineaPartida, Partida, Cuenta)
        .join(Partida, LineaPartida.partida_id == Partida.id)
        .join(Cuenta, LineaPartida.cuenta_id == Cuenta.id)
        .where(Partida.estado == EstadoPartida.CONTABILIZADA)
    )
    if desde:
        stmt = stmt.where(Partida.fecha >= desde)
    if hasta:
        stmt = stmt.where(Partida.fecha <= hasta)
    if linea_negocio:
        stmt = stmt.where(LineaPartida.linea_negocio == linea_negocio)
    if unidad_id:
        stmt = stmt.where(LineaPartida.unidad_id == unidad_id)
    return db.execute(stmt.order_by(Partida.fecha, Partida.numero, LineaPartida.id)).all()


def saldo_natural(cuenta: Cuenta, debe: Decimal, haber: Decimal) -> Decimal:
    return debe - haber if cuenta.naturaleza == "DEUDORA" else haber - debe


def balance_comprobacion(db: Session, desde=None, hasta=None, linea_negocio=None, unidad_id=None) -> dict:
    acumulado: dict[int, dict] = {}
    for linea, _, cuenta in _movimientos(db, desde, hasta, linea_negocio, unidad_id):
        fila = acumulado.setdefault(cuenta.id, {
            "codigo": cuenta.codigo, "nombre": cuenta.nombre, "naturaleza": cuenta.naturaleza,
            "debe": Decimal("0"), "haber": Decimal("0"),
            "monetaria_usd": cuenta.monetaria_usd, "saldo_usd": Decimal("0"), "_cuenta": cuenta,
        })
        fila["debe"] += linea.debe
        fila["haber"] += linea.haber
        if cuenta.monetaria_usd and linea.monto_original is not None:
            signo = 1 if linea.debe > 0 else -1
            if cuenta.naturaleza == "ACREEDORA":
                signo = -signo
            fila["saldo_usd"] += signo * linea.monto_original
    filas = []
    for fila in sorted(acumulado.values(), key=lambda f: f["codigo"]):
        cuenta = fila.pop("_cuenta")
        fila["saldo"] = saldo_natural(cuenta, fila["debe"], fila["haber"])
        if not fila["monetaria_usd"]:
            fila["saldo_usd"] = None
        filas.append(fila)
    total_debe = sum((f["debe"] for f in filas), Decimal("0"))
    total_haber = sum((f["haber"] for f in filas), Decimal("0"))
    filtrado = bool(linea_negocio or unidad_id)
    return {"cuentas": filas, "total_debe": total_debe, "total_haber": total_haber,
            # Un subconjunto por línea o VIN no tiene por qué cuadrar (DoD 5 del Sprint 1).
            "cuadra": None if filtrado else total_debe == total_haber,
            "filtrado": filtrado}


def mayor(db: Session, codigo: str, desde=None, hasta=None, linea_negocio=None, unidad_id=None) -> dict:
    cuenta = db.scalar(select(Cuenta).where(Cuenta.codigo == codigo))
    if cuenta is None:
        raise NoEncontrado(f"La cuenta {codigo} no existe")
    saldo_inicial = Decimal("0")
    if desde:
        for l, _, c in _movimientos(db, None, None, linea_negocio, unidad_id):
            if c.id == cuenta.id and l.partida.fecha < desde:
                saldo_inicial += saldo_natural(cuenta, l.debe, l.haber)
    saldo = saldo_inicial
    movimientos = []
    for linea, partida, c in _movimientos(db, desde, hasta, linea_negocio, unidad_id):
        if c.id != cuenta.id:
            continue
        saldo += saldo_natural(cuenta, linea.debe, linea.haber)
        movimientos.append({
            "fecha": partida.fecha, "partida_id": partida.id, "numero": partida.numero,
            "concepto": partida.concepto, "origen_tipo": partida.origen_tipo, "origen_id": partida.origen_id,
            "debe": linea.debe, "haber": linea.haber, "saldo": saldo,
            "moneda": linea.moneda, "monto_original": linea.monto_original, "tipo_cambio": linea.tipo_cambio,
            "linea_negocio": linea.linea_negocio, "vin": linea.unidad.vin if linea.unidad else None,
        })
    return {"codigo": cuenta.codigo, "nombre": cuenta.nombre, "saldo_inicial": saldo_inicial,
            "movimientos": movimientos, "saldo_final": saldo}


def saldo_cuenta_vin(db: Session, codigo: str, unidad_id: int) -> Decimal:
    return mayor(db, codigo, unidad_id=unidad_id)["saldo_final"]

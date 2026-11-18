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
"""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.modulos.alquileres.models import MODALIDADES, Tarifa
from app.modulos.alquileres.schemas import TarifaEntrada
from app.modulos.unidades import service as unidades

_LIMITE_MONTO = Decimal("1000000000000")


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

"""Reglas del módulo de compras (Sprint 1, equipo B).

HU-4.01 (incluido): alta y consulta de proveedores locales o del exterior, con nombre, rubro,
moneda habitual, días de crédito y datos bancarios; NIT de los locales validado con su dígito
verificador (`comun/nit.py`) y sin repetirse; identificación fiscal y país para los extranjeros;
régimen de IVA del proveedor local (general o pequeño contribuyente), que pide HU-4.09.
HU-4.01 (diferido): si al proveedor local se le retiene IVA o ISR (criterio 2; lo usa HU-4.11).

HU-4.09 (incluido): captura del DTE de un proveedor local (serie, número, autorización, fecha y
líneas con descripción, cuenta, línea de negocio, VIN opcional, base e IVA), en quetzales; el
mismo DTE no se registra dos veces para el mismo proveedor; la factura de un pequeño
contribuyente no da crédito fiscal (su IVA es parte del costo); cada factura abre su cuenta por
pagar al proveedor por el total, con vencimiento según sus días de crédito.
HU-4.09 (diferido): importar el XML del DTE (criterio 3) y el libro de compras (criterio 5, con
HU-2.15).

Pendiente al mezclar HU-1.01 (perfil fiscal, equipo C):
- El perfil fiscal valida su NIT con el mismo `comun/nit.py`; no se duplica la regla.
- Las retenciones diferidas dependen de que la empresa sea agente de retención de IVA o ISR:
  al agregar las retenciones del proveedor, leerlo del service de `configuracion` (nunca de sus
  models) y solo pedir los datos de retención cuando la empresa retiene.
- Rechazar como proveedor el NIT de la propia empresa (se compara contra el perfil vigente).

Pendiente para HU-4.09 cuando salgan las historias de las que depende (ver `registrar_factura`):
- HU-1.02 (catálogo, equipo A): la cuenta de cada línea hoy es texto con forma de código
  ("5.1.02"). Validarla contra el service de `configuracion`: que exista, sea de detalle y esté
  activa; y guardar la referencia a la cuenta en lugar del texto (migración de datos).
- HU-1.04 (dimensiones, equipo A): la línea de negocio ya se valida contra la lista de
  `configuracion`. Falta aplicar lo que defina la cuenta (línea obligatoria o por defecto, y si el
  VIN es obligatorio, opcional o no aplica) con `configuracion.resolver_dimensiones`, que pide la
  cuenta del catálogo (HU-1.02).
- HU-1.05 (unidades): hecho. El VIN se valida con el service de `unidades` (forma y dígito
  verificador) y la unidad debe existir; la línea queda ligada a la unidad por llave foránea.
- HU-2.01/HU-2.03 (motor contable, equipo A): pedir la partida al service de `contabilidad` en la
  misma transacción que la factura (regla 3 de la arquitectura): débito a la cuenta de cada línea
  por su base (más su IVA si es pequeño contribuyente), débito a IVA por cobrar por el crédito
  fiscal y crédito a proveedores por el total. Hoy no se genera partida.
- HU-6.02 (FEL, equipo C): el adaptador puede verificar la autorización del DTE con la SAT.
- HU-1.07: facturas locales en dólares, con el tipo de cambio de la fecha.

Pendiente al mezclar HU-1.09 y HU-1.11: exigir sesión y permiso del auxiliar contable, y que la
auditoría automática registre el alta del proveedor y de la factura (con el VIN de cada línea).
"""

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.comun.nit import NITInvalido, formatear_nit, normalizar_nit
from app.modulos.compras.models import CuentaPorPagar, FacturaCompra, LineaFacturaCompra, Proveedor
from app.modulos.compras.schemas import FacturaCompraEntrada, LineaFacturaEntrada, ProveedorEntrada
from app.modulos.configuracion import service as configuracion
from app.modulos.unidades import service as unidades


def _nit_repetido(nit: str) -> ErrorNegocio:
    return ErrorNegocio(f"Ya existe un proveedor con el NIT {formatear_nit(nit)}", status=409)


def registrar_proveedor(db: Session, datos: ProveedorEntrada) -> Proveedor:
    if not datos.nombre:
        raise ErrorNegocio("El nombre del proveedor es obligatorio")

    nit = identificacion = pais = regimen = None
    if datos.tipo == "local":
        if datos.nit is None:
            raise ErrorNegocio("El NIT es obligatorio para un proveedor local")
        if datos.identificacion_fiscal or datos.pais:
            raise ErrorNegocio("Un proveedor local se identifica solo con su NIT")
        if datos.regimen is None:
            raise ErrorNegocio("Indique el régimen del proveedor local: general o pequeño contribuyente")
        regimen = datos.regimen
        try:
            nit = normalizar_nit(datos.nit)
        except NITInvalido as error:
            raise ErrorNegocio(str(error)) from None
        if db.scalar(select(Proveedor.id).where(Proveedor.nit == nit)) is not None:
            raise _nit_repetido(nit)
    else:
        if datos.nit:
            raise ErrorNegocio("Un proveedor del exterior no lleva NIT; indique su identificación fiscal")
        if datos.regimen:
            raise ErrorNegocio("El régimen de IVA solo aplica a proveedores locales")
        if datos.identificacion_fiscal is None or datos.pais is None:
            raise ErrorNegocio("Un proveedor del exterior requiere identificación fiscal y país")
        pais = datos.pais.upper()
        if len(pais) != 2 or not pais.isalpha() or not pais.isascii():
            raise ErrorNegocio("El país se indica con su código de dos letras, por ejemplo US")
        if pais == "GT":
            raise ErrorNegocio("Un proveedor de Guatemala se registra como local, con su NIT")
        identificacion = datos.identificacion_fiscal

    proveedor = Proveedor(
        tipo=datos.tipo,
        nombre=datos.nombre,
        nit=nit,
        identificacion_fiscal=identificacion,
        pais=pais,
        regimen=regimen,
        rubro=datos.rubro,
        moneda_habitual=datos.moneda_habitual,
        dias_credito=datos.dias_credito,
        banco=datos.banco,
        cuenta_bancaria=datos.cuenta_bancaria,
    )
    db.add(proveedor)
    try:
        db.commit()
    except IntegrityError:
        # Dos altas simultáneas con el mismo NIT: la restricción UNIQUE decide.
        db.rollback()
        if nit is not None:
            raise _nit_repetido(nit) from None
        raise
    db.refresh(proveedor)
    return proveedor


def listar_proveedores(
    db: Session,
    tipo: str | None = None,
    rubro: str | None = None,
    buscar: str | None = None,
) -> list[Proveedor]:
    """Consulta por tipo, rubro o texto (nombre, NIT o identificación fiscal), en orden alfabético."""
    consulta = select(Proveedor).order_by(Proveedor.nombre, Proveedor.id)
    if tipo:
        consulta = consulta.where(Proveedor.tipo == tipo)
    if rubro:
        consulta = consulta.where(Proveedor.rubro == rubro)
    if buscar and buscar.strip():
        texto = buscar.strip()
        patron = _patron_contiene(texto)
        condiciones = [
            Proveedor.nombre.ilike(patron, escape="\\"),
            Proveedor.identificacion_fiscal.ilike(patron, escape="\\"),
        ]
        # El NIT se guarda normalizado: se busca igual, sin guion ni espacios y en mayúsculas, para
        # que "1669394" encuentre 16693949 y "576937-k" encuentre 576937K. Quitar los ceros a la
        # izquierda solo amplía los resultados, y así un NIT completo escrito con ceros también se
        # encuentra.
        nit_buscado = re.sub(r"[\s-]", "", texto).upper().lstrip("0")
        if nit_buscado:
            condiciones.append(Proveedor.nit.ilike(_patron_contiene(nit_buscado), escape="\\"))
        consulta = consulta.where(or_(*condiciones))
    return list(db.scalars(consulta))


def _patron_contiene(texto: str) -> str:
    """Patrón LIKE "contiene" con los comodines del usuario tratados como texto (escape `\\`)."""
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def obtener_proveedor(db: Session, proveedor_id: int) -> Proveedor:
    """Proveedor por id; lo usan la compra (HU-4.02), los gastos (HU-4.04) y las facturas (HU-4.09)."""
    proveedor = db.get(Proveedor, proveedor_id)
    if proveedor is None:
        raise ErrorNegocio(f"No existe el proveedor {proveedor_id}", status=404)
    return proveedor


# ── HU-4.09: facturas de compras y gastos locales ─────────────────────────────

_SERIE = re.compile(r"[A-Z0-9]{1,20}")
_NUMERO = re.compile(r"[0-9]{1,20}")
_AUTORIZACION = re.compile(r"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}")
# Forma de un código del catálogo ("5", "5.1.02", "5-1-02"); HU-1.02 valida que la cuenta exista.
_CUENTA = re.compile(r"[0-9]+([.-][0-9]+)*")
_LIMITE_MONTO = Decimal("1000000000000")  # cabe en NUMERIC(18, 6)


def _monto(texto: str, campo: str, linea: int, permite_cero: bool) -> Decimal:
    """Lee un monto enviado como texto: número finito, con hasta 6 decimales, nunca float."""
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        raise ErrorNegocio(f"Línea {linea}: {campo} no es un número válido") from None
    if not valor.is_finite():
        raise ErrorNegocio(f"Línea {linea}: {campo} no es un número válido")
    if -valor.as_tuple().exponent > 6:  # type: ignore[operator]
        raise ErrorNegocio(f"Línea {linea}: {campo} admite hasta 6 decimales")
    if valor < 0 or (valor == 0 and not permite_cero):
        condicion = "no puede ser negativo" if permite_cero else "debe ser mayor que cero"
        raise ErrorNegocio(f"Línea {linea}: {campo} {condicion}")
    if valor >= _LIMITE_MONTO:
        raise ErrorNegocio(f"Línea {linea}: {campo} excede el máximo permitido")
    return valor


def _linea(db: Session, numero: int, datos: LineaFacturaEntrada) -> LineaFacturaCompra:
    if not datos.descripcion:
        raise ErrorNegocio(f"Línea {numero}: la descripción es obligatoria")
    # Pendiente HU-1.02: la cuenta debe existir en el catálogo, ser de detalle y estar activa.
    if not _CUENTA.fullmatch(datos.cuenta):
        raise ErrorNegocio(f"Línea {numero}: la cuenta debe ser un código del catálogo, por ejemplo 5.1.02")
    # Pendiente HU-1.04 con HU-1.02: la cuenta decide si la línea de negocio y el VIN son obligatorios.
    if datos.linea_negocio not in configuracion.LINEAS_NEGOCIO:
        raise ErrorNegocio(
            f"Línea {numero}: línea de negocio desconocida ({datos.linea_negocio}); "
            f"use una de: {', '.join(configuracion.LINEAS_NEGOCIO)}"
        )
    vin = None
    if datos.vin is not None:
        try:
            vin = unidades.validar_vin(datos.vin)
        except ErrorNegocio as error:
            raise ErrorNegocio(f"Línea {numero}: {error.mensaje}") from None
        if not unidades.existe_vin(db, vin):
            raise ErrorNegocio(f"Línea {numero}: no existe la unidad con VIN {vin}; regístrela antes")
    return LineaFacturaCompra(
        numero_linea=numero,
        descripcion=datos.descripcion,
        cuenta=datos.cuenta,
        linea_negocio=datos.linea_negocio,
        vin=vin,
        base=_monto(datos.base, "la base", numero, permite_cero=False),
        iva=_monto(datos.iva, "el IVA", numero, permite_cero=True),
    )


def _dte_repetido(proveedor: Proveedor, serie: str, numero: str) -> ErrorNegocio:
    return ErrorNegocio(
        f"El DTE serie {serie} número {numero} de {proveedor.nombre} ya está registrado", status=409
    )


def registrar_factura(db: Session, datos: FacturaCompraEntrada) -> FacturaCompra:
    """Registra el DTE con sus líneas y abre su cuenta por pagar, todo en una transacción."""
    proveedor = obtener_proveedor(db, datos.proveedor_id)
    if proveedor.tipo != "local":
        raise ErrorNegocio("Las facturas FEL se registran solo a proveedores locales")

    if not _SERIE.fullmatch(datos.serie):
        raise ErrorNegocio("La serie del DTE lleva solo letras y dígitos, hasta 20")
    if not _NUMERO.fullmatch(datos.numero):
        raise ErrorNegocio("El número del DTE lleva solo dígitos, hasta 20")
    if not _AUTORIZACION.fullmatch(datos.autorizacion):
        raise ErrorNegocio(
            "La autorización del DTE es el UUID que entrega la SAT, "
            "por ejemplo 1A2B3C4D-1234-4ABC-9DEF-0123456789AB"
        )
    if datos.fecha > date.today():
        raise ErrorNegocio("La fecha del DTE no puede ser futura")
    if not datos.lineas:
        raise ErrorNegocio("La factura necesita al menos una línea")

    repetida = db.scalar(
        select(FacturaCompra.id).where(
            FacturaCompra.proveedor_id == proveedor.id,
            or_(
                (FacturaCompra.serie == datos.serie) & (FacturaCompra.numero == datos.numero),
                FacturaCompra.autorizacion == datos.autorizacion,
            ),
        )
    )
    if repetida is not None:
        raise _dte_repetido(proveedor, datos.serie, datos.numero)

    lineas = [_linea(db, numero, linea) for numero, linea in enumerate(datos.lineas, start=1)]
    total_base = sum((linea.base for linea in lineas), Decimal(0))
    total_iva = sum((linea.iva for linea in lineas), Decimal(0))
    total = total_base + total_iva
    # Criterio 4: el IVA de un pequeño contribuyente no es crédito fiscal; queda como costo.
    credito_fiscal = total_iva if proveedor.regimen == "general" else Decimal(0)

    factura = FacturaCompra(
        proveedor_id=proveedor.id,
        serie=datos.serie,
        numero=datos.numero,
        autorizacion=datos.autorizacion,
        fecha=datos.fecha,
        regimen_proveedor=proveedor.regimen,
        total_base=total_base,
        total_iva=total_iva,
        credito_fiscal=credito_fiscal,
        total=total,
        lineas=lineas,
    )
    factura.cuenta_por_pagar = CuentaPorPagar(
        proveedor_id=proveedor.id,
        fecha=datos.fecha,
        fecha_vencimiento=datos.fecha + timedelta(days=proveedor.dias_credito),
        moneda="GTQ",
        monto=total,
        saldo=total,
    )
    db.add(factura)
    # Pendiente HU-2.01/HU-2.03: aquí se pide la partida a `contabilidad` (sin commit propio), para
    # que la factura, su cuenta por pagar y su partida se confirmen juntas.
    try:
        db.commit()
    except IntegrityError:
        # Dos capturas simultáneas del mismo DTE: las restricciones UNIQUE deciden.
        db.rollback()
        raise _dte_repetido(proveedor, datos.serie, datos.numero) from None
    db.refresh(factura)
    return factura


def listar_facturas(db: Session, proveedor_id: int | None = None) -> list[FacturaCompra]:
    """Facturas de la más reciente a la más antigua, opcionalmente de un proveedor."""
    consulta = select(FacturaCompra).order_by(FacturaCompra.fecha.desc(), FacturaCompra.id.desc())
    if proveedor_id is not None:
        consulta = consulta.where(FacturaCompra.proveedor_id == proveedor_id)
    return list(db.scalars(consulta).unique())


def obtener_factura(db: Session, factura_id: int) -> FacturaCompra:
    factura = db.get(FacturaCompra, factura_id)
    if factura is None:
        raise ErrorNegocio(f"No existe la factura {factura_id}", status=404)
    return factura

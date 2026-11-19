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
pagar al proveedor por el total, con vencimiento según sus días de crédito, y su partida (HU-2.03):
débito a la cuenta de cada línea por su base (más su IVA si no da crédito fiscal), débito al IVA
crédito fiscal y crédito a proveedores locales por el total.
HU-4.09 (diferido): importar el XML del DTE (criterio 3) y el libro de compras (criterio 5, con
HU-2.15).

HU-4.04 (incluido): gastos de importación ligados a una unidad registrada (VIN), con un catálogo
de conceptos (flete, seguro de transporte, agente aduanal, almacenaje, DAI, IVA de importación,
IPRIMA, placas y otros) que da a cada uno su cuenta y su tratamiento; el IVA de importación es
crédito fiscal y no suma al costo de la unidad; cada gasto tiene proveedor (HU-4.01), puede ser
en GTQ o USD (con el tipo de cambio de la fecha, HU-1.06/HU-1.07, y su equivalente en quetzales)
y abre su cuenta por pagar en la moneda del documento, como la factura de HU-4.09, con su partida
(HU-2.03): débito a la cuenta del concepto por el equivalente en quetzales, con el VIN, y crédito
a proveedores en la moneda del documento. La ficha de la unidad muestra el total que suma al costo
(`resumen_gastos_unidad`).
HU-4.04 (diferido): ligar el gasto a un expediente (criterio 2) y prorratear los compartidos
(HU-4.05); la DUCA (HU-4.06), que cuadrará DAI e IVA contra estos gastos; el IVA de los servicios
locales con FEL como crédito fiscal (criterio 5; hoy esa factura se captura en HU-4.09); un tipo
de cambio personalizado con justificación.

HU-4.02 (incluido): compra de una unidad en EE. UU. a un proveedor del exterior, en USD, con
fecha, número de lote o factura, VIN y ficha del vehículo, precio y cargos de la subasta
(comisión, documentación y arrastre interno). En una sola transacción: crea la unidad en estado
"en tránsito" con el service de `unidades` (HU-1.05), registra la compra con el tipo de cambio de
la fecha y su equivalente en quetzales (HU-1.06/HU-1.07), abre la cuenta por pagar en USD al
proveedor y pide a `contabilidad` la partida (HU-2.03): débito a vehículos en tránsito
(1.1.04.01, la cuenta de "unidades en proceso" del catálogo semilla) con el VIN y crédito a
proveedores del exterior (2.1.01.01) en USD. Las cuentas salen de las reglas de contabilización
de `contabilidad` (`cuenta_regla`), que el contador puede cambiar. Si el VIN ya existe, falta el
tipo de cambio o la partida falla, no se crea nada. El total en quetzales suma al costo de la
unidad junto con los gastos de importación (`resumen_gastos_unidad`).
HU-4.02 (diferido): adjuntar la factura, el título y el bill of sale (criterio 4); comprar una
unidad ya registrada; la compra a particulares en Guatemala (pendiente de la historia).

HU-4.08 (incluido, versión delgada): hoja de costo de la unidad (`hoja_de_costo`) agrupada en
compra (USD, tipo de cambio y quetzales), importación por concepto (moneda original, tipo de cambio
y quetzales; el IVA de importación se muestra aparte y no es costo) y reacondicionamiento: la mano
de obra de las órdenes cerradas (`taller`) y las líneas de facturas locales cargadas a unidades en
proceso con el VIN (con el IVA de un pequeño contribuyente). El total cuadra con el saldo de
unidades en proceso del VIN en el mayor (criterio 3). `costos_de_unidades` y
`resumen_gastos_unidad` usan la misma regla.
HU-4.08 (diferido): exportar a PDF y Excel (criterio 4, Sprint 5 con HU-7.09); el expediente y los
gastos compartidos prorrateados (HU-4.03/HU-4.05, Sprint 5).

HU-4.13 (incluido): programación de pagos. Quien propone (auxiliar contable, contador o gerente
financiero) elige cuentas por pagar con saldo, vencidas o por vencer, de facturas, gastos de
importación y compras en EE. UU. (`cuentas_por_pagar_pendientes`, por moneda, vencimiento o
proveedor) y para cada una la cuenta bancaria (HU-1.08) y el monto en la moneda del documento;
menos que el saldo es un pago parcial. Una cuenta por pagar está en un solo pago propuesto o
aprobado a la vez. `detalle_programacion` da los totales que salen en Q y en USD y, por cuenta
bancaria, el saldo en libros, lo comprometido en pagos aprobados de otras programaciones, el
disponible y si alcanza; lo que sale de un banco en otra moneda se estima con el último tipo de
cambio cargado. El gerente financiero aprueba, modifica (aprueba con otro monto o cuenta bancaria)
o rechaza con motivo cada pago; quien propuso no decide sus pagos (403, como HU-1.10). Solo un
pago aprobado se ejecuta (HU-4.14).
HU-4.13 (diferido): límites de aprobación por monto; programaciones recurrentes; avisar al
proveedor.

HU-4.14 (incluido): pago a un proveedor desde una cuenta bancaria activa, por cheque o
transferencia, con número de cheque o referencia y fecha, que ejecuta pagos aprobados de un mismo
proveedor y cuenta bancaria (`pagos_por_ejecutar`); cada uno cancela su documento total o
parcialmente. El pago va en la moneda del banco y puede cancelar documentos en otra: aplica el tipo
de cambio de la fecha, salda los documentos en USD a su tipo de cambio en libros y registra el
diferencial realizado (HU-2.09). Pide su partida a `contabilidad` en la misma transacción.
Anularlo revierte la partida (HU-2.05), reabre los documentos y deja anulados sus pagos
programados. Un número de cheque no se repite en la misma cuenta bancaria. El comprobante de pago
se imprime desde la pantalla (`detalle_pago`).
HU-4.14 (diferido): imprimir el cheque (criterio 3) y avanzar la numeración de la chequera
(HU-1.08); retenciones de IVA e ISR (HU-4.11, HU-4.12).

Pendiente al mezclar HU-1.01 (perfil fiscal, equipo C):
- El perfil fiscal valida su NIT con el mismo `comun/nit.py`; no se duplica la regla.
- Las retenciones diferidas dependen de que la empresa sea agente de retención de IVA o ISR:
  al agregar las retenciones del proveedor, leerlo del service de `configuracion` (nunca de sus
  models) y solo pedir los datos de retención cuando la empresa retiene.
- Rechazar como proveedor el NIT de la propia empresa (se compara contra el perfil vigente).

Pendiente para HU-4.09:
- La cuenta de cada línea se guarda como código (texto) y se valida contra el catálogo (existe y
  es de detalle); las dimensiones (línea de negocio y VIN) las valida el motor contable al crear
  la partida. Falta rechazar cuentas inactivas cuando el catálogo permita inactivarlas (Sprint 5).
- HU-6.02 (FEL, equipo C): el adaptador puede verificar la autorización del DTE con la SAT.
- HU-1.07: facturas locales en dólares, con el tipo de cambio de la fecha.

Pendiente para HU-4.04:
- HU-4.05/HU-4.06: el expediente y la DUCA; el gasto podrá ligarse al expediente en vez del VIN.
"""

import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.dinero import convertir, redondear
from app.comun.errores import ErrorNegocio
from app.comun.nit import NITInvalido, formatear_nit, normalizar_nit
from app.modulos.compras.models import (
    AplicacionPago,
    CompraUnidad,
    ConceptoGastoImportacion,
    CuentaPorPagar,
    FacturaCompra,
    GastoImportacion,
    LineaFacturaCompra,
    PagoProgramado,
    PagoProveedor,
    ProgramacionPago,
    Proveedor,
)
from app.modulos.compras.schemas import (
    AnulacionPagoEntrada,
    CompraUnidadEntrada,
    DecisionPagoEntrada,
    FacturaCompraEntrada,
    GastoImportacionEntrada,
    LineaFacturaEntrada,
    PagoProveedorEntrada,
    ProgramacionPagoEntrada,
    ProveedorEntrada,
)
from app.modulos.configuracion import service as configuracion
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaAutomatica, LineaEntrada
from app.modulos.taller import service as taller
from app.modulos.unidades import service as unidades
from app.modulos.unidades.schemas import UnidadEntrada


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


DOCUMENTO_FACTURA = "factura_compra"  # tipos de documento de las partidas (HU-2.03)
DOCUMENTO_GASTO = "gasto_importacion"


def _monto(texto: str, campo: str, permite_cero: bool, prefijo: str = "") -> Decimal:
    """Lee un monto enviado como texto: número finito, con hasta 6 decimales, nunca float.

    `prefijo` ubica el error ("Línea 2: "); `campo` es el sujeto del mensaje ("la base").
    """
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        raise ErrorNegocio(f"{prefijo}{campo} no es un número válido") from None
    if not valor.is_finite():
        raise ErrorNegocio(f"{prefijo}{campo} no es un número válido")
    if -valor.as_tuple().exponent > 6:  # type: ignore[operator]
        raise ErrorNegocio(f"{prefijo}{campo} admite hasta 6 decimales")
    if valor < 0 or (valor == 0 and not permite_cero):
        condicion = "no puede ser negativo" if permite_cero else "debe ser mayor que cero"
        raise ErrorNegocio(f"{prefijo}{campo} {condicion}")
    if valor >= _LIMITE_MONTO:
        raise ErrorNegocio(f"{prefijo}{campo} excede el máximo permitido")
    return valor


def _linea(db: Session, numero: int, datos: LineaFacturaEntrada) -> LineaFacturaCompra:
    if not datos.descripcion:
        raise ErrorNegocio(f"Línea {numero}: la descripción es obligatoria")
    if not _CUENTA.fullmatch(datos.cuenta):
        raise ErrorNegocio(f"Línea {numero}: la cuenta debe ser un código del catálogo, por ejemplo 6.1.02")
    cuenta = configuracion.buscar_cuenta(db, datos.cuenta)
    if cuenta is None or not cuenta.es_detalle:
        raise ErrorNegocio(
            f"Línea {numero}: la cuenta {datos.cuenta} no es una cuenta de detalle del catálogo"
        )
    # Si la cuenta exige línea de negocio o VIN lo decide el motor contable al crear la partida.
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
        base=_monto(datos.base, "la base", permite_cero=False, prefijo=f"Línea {numero}: "),
        iva=_monto(datos.iva, "el IVA", permite_cero=True, prefijo=f"Línea {numero}: "),
    )


def _dte_repetido(proveedor: Proveedor, serie: str, numero: str) -> ErrorNegocio:
    return ErrorNegocio(
        f"El DTE serie {serie} número {numero} de {proveedor.nombre} ya está registrado", status=409
    )


def registrar_factura(
    db: Session, datos: FacturaCompraEntrada, usuario_id: int | None = None
) -> FacturaCompra:
    """Registra el DTE con sus líneas, su cuenta por pagar y su partida en una transacción, o nada."""
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
    # Sin crédito fiscal (pequeño contribuyente) el IVA de cada línea va a su misma cuenta.
    debitos = [
        LineaEntrada(
            cuenta_id=configuracion.buscar_cuenta(db, linea.cuenta).id,
            lado="debe",
            monto=f"{linea.base + (linea.iva if not credito_fiscal else 0):.6f}",
            linea_negocio=linea.linea_negocio,
            vin=linea.vin,
        )
        for linea in lineas
    ]
    if credito_fiscal:
        debitos.append(
            LineaEntrada(
                cuenta_id=contabilidad.cuenta_regla(db, DOCUMENTO_FACTURA, "iva_credito_fiscal"),
                lado="debe",
                monto=f"{credito_fiscal:.6f}",
            )
        )
    por_pagar = contabilidad.cuenta_regla(db, DOCUMENTO_FACTURA, "por_pagar_gtq")
    db.add(factura)
    try:
        db.flush()  # el id de la factura liga su partida
        contabilidad.registrar_automatica(
            db,
            fecha=datos.fecha,
            concepto=f"Factura {datos.serie}-{datos.numero} de {proveedor.nombre}"[:300],
            lineas=[*debitos, LineaEntrada(cuenta_id=por_pagar, lado="haber", monto=f"{total:.6f}")],
            documento_tipo=DOCUMENTO_FACTURA,
            documento_id=factura.id,
            usuario_id=usuario_id,
        )
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
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


# ── HU-4.04: gastos de importación ────────────────────────────────────────────

_DECIMALES_MONTO = 6


def listar_conceptos(db: Session) -> list[ConceptoGastoImportacion]:
    """Catálogo de conceptos (criterio 1), en el orden en que se sembró."""
    return list(db.scalars(select(ConceptoGastoImportacion).order_by(ConceptoGastoImportacion.orden)))


def registrar_gasto_importacion(
    db: Session, datos: GastoImportacionEntrada, usuario_id: int | None = None
) -> GastoImportacion:
    """Registra el gasto de la unidad, su cuenta por pagar y su partida en una transacción, o nada."""
    vin = unidades.validar_vin(datos.vin)
    if not unidades.existe_vin(db, vin):
        raise ErrorNegocio(f"No existe la unidad con VIN {vin}; regístrela antes")
    linea_negocio = unidades.obtener_por_vin(db, vin).linea_negocio
    concepto = db.scalar(
        select(ConceptoGastoImportacion).where(ConceptoGastoImportacion.codigo == datos.concepto)
    )
    if concepto is None:
        raise ErrorNegocio(f"Concepto de gasto de importación desconocido: {datos.concepto}")
    proveedor = obtener_proveedor(db, datos.proveedor_id)
    if datos.fecha > date.today():
        raise ErrorNegocio("La fecha del gasto no puede ser futura")
    if not datos.documento:
        raise ErrorNegocio("Indique el documento del gasto: factura, recibo, DUCA…")
    monto = _monto(datos.monto, "El monto", permite_cero=False)

    # Criterio 4: en dólares se convierte con el tipo de cambio de la fecha (HU-1.06); si no está
    # cargado, `configuracion` rechaza el registro.
    tipo_cambio = None
    monto_gtq = monto
    if datos.moneda == "USD":
        tipo_cambio = configuracion.tipo_cambio_de(db, datos.fecha)
        monto_gtq = redondear(convertir(monto, tipo_cambio), _DECIMALES_MONTO)

    gasto = GastoImportacion(
        vin=vin,
        concepto=concepto.codigo,
        proveedor_id=proveedor.id,
        fecha=datos.fecha,
        documento=datos.documento,
        descripcion=datos.descripcion,
        moneda=datos.moneda,
        monto=monto,
        tipo_cambio=tipo_cambio,
        monto_gtq=monto_gtq,
        # Criterio 3: el tratamiento del concepto decide si suma al costo o es crédito fiscal.
        cuenta=concepto.cuenta,
        tratamiento=concepto.tratamiento,
    )
    # La deuda queda en la moneda del documento: un gasto en dólares se le debe en dólares.
    gasto.cuenta_por_pagar = CuentaPorPagar(
        proveedor_id=proveedor.id,
        fecha=datos.fecha,
        fecha_vencimiento=datos.fecha + timedelta(days=proveedor.dias_credito),
        moneda=datos.moneda,
        monto=monto,
        saldo=monto,
    )
    cuenta_gasto = configuracion.buscar_cuenta(db, concepto.cuenta)
    if cuenta_gasto is None:
        raise ErrorNegocio(
            f"El catálogo de cuentas no tiene {concepto.cuenta} ({concepto.nombre}); cárguelo antes", 409
        )
    por_pagar = contabilidad.cuenta_regla(db, DOCUMENTO_GASTO, f"por_pagar_{datos.moneda.lower()}")
    db.add(gasto)
    try:
        db.flush()  # el id del gasto liga su partida
        contabilidad.registrar_automatica(
            db,
            fecha=datos.fecha,
            concepto=f"{concepto.nombre} de la unidad {vin}, {proveedor.nombre}, {datos.documento}"[:300],
            lineas=[
                # La cuenta del concepto no es monetaria en USD: se carga el equivalente en quetzales,
                # el mismo que obtiene el motor al convertir la línea del proveedor.
                LineaEntrada(
                    cuenta_id=cuenta_gasto.id,
                    lado="debe",
                    monto=f"{monto_gtq:.6f}",
                    linea_negocio=linea_negocio,
                    vin=vin,
                ),
                LineaEntrada(
                    cuenta_id=por_pagar,
                    lado="haber",
                    monto=f"{monto:.6f}",
                    moneda=datos.moneda,
                    linea_negocio=linea_negocio,
                    vin=vin,
                ),
            ],
            documento_tipo=DOCUMENTO_GASTO,
            documento_id=gasto.id,
            usuario_id=usuario_id,
        )
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    db.refresh(gasto)
    return gasto


def listar_gastos_importacion(
    db: Session, vin: str | None = None, proveedor_id: int | None = None
) -> list[GastoImportacion]:
    """Gastos del más reciente al más antiguo, opcionalmente de una unidad o de un proveedor."""
    consulta = select(GastoImportacion).order_by(GastoImportacion.fecha.desc(), GastoImportacion.id.desc())
    if vin and vin.strip():
        consulta = consulta.where(GastoImportacion.vin == vin.strip().upper())
    if proveedor_id is not None:
        consulta = consulta.where(GastoImportacion.proveedor_id == proveedor_id)
    return list(db.scalars(consulta).unique())


def obtener_gasto_importacion(db: Session, gasto_id: int) -> GastoImportacion:
    gasto = db.get(GastoImportacion, gasto_id)
    if gasto is None:
        raise ErrorNegocio(f"No existe el gasto de importación {gasto_id}", status=404)
    return gasto


def resumen_gastos_unidad(db: Session, vin: str) -> dict:
    """Costo de una unidad en quetzales: la compra (HU-4.02), los gastos que suman al costo y el
    reacondicionamiento, con la regla de la hoja de costo (HU-4.08); aparte lo que es crédito
    fiscal (el IVA de importación). Lo muestra la ficha de la unidad."""
    unidad = unidades.obtener_por_vin(db, vin)
    filas = db.execute(
        select(
            GastoImportacion.tratamiento,
            func.count(GastoImportacion.id),
            func.sum(GastoImportacion.monto_gtq),
        )
        .where(GastoImportacion.vin == unidad.vin)
        .group_by(GastoImportacion.tratamiento)
    ).all()
    totales = {tratamiento: total for tratamiento, _, total in filas}
    compra_gtq = db.scalar(select(CompraUnidad.total_gtq).where(CompraUnidad.vin == unidad.vin))
    return {
        "vin": unidad.vin,
        "gastos": sum(cantidad for _, cantidad, _ in filas),
        "total_costo_gtq": totales.get("costo", Decimal(0)),
        "total_credito_fiscal_gtq": totales.get("credito_fiscal", Decimal(0)),
        "compra_gtq": compra_gtq if compra_gtq is not None else Decimal(0),
        "costo_total_gtq": costos_de_unidades(db, [unidad.vin])[unidad.vin],
    }


def costos_de_unidades(db: Session, vins: list[str]) -> dict[str, Decimal]:
    """Costo acumulado en quetzales de varias unidades a la vez, con la regla de la hoja de costo
    (HU-4.08): la compra, los gastos que suman al costo (sin el IVA de importación), la mano de
    obra de las órdenes cerradas y las líneas de facturas locales cargadas a unidades en proceso
    con el VIN. Lo piden `unidades` (etapas, HU-4.07; alta, HU-3.01) y `reportes`; un VIN sin
    nada cuesta cero."""
    costos = dict.fromkeys(vins, Decimal(0))
    if not vins:
        return costos
    compras = db.execute(
        select(CompraUnidad.vin, CompraUnidad.total_gtq).where(CompraUnidad.vin.in_(vins))
    ).all()
    gastos = db.execute(
        select(GastoImportacion.vin, func.sum(GastoImportacion.monto_gtq))
        .where(GastoImportacion.vin.in_(vins), GastoImportacion.tratamiento == "costo")
        .group_by(GastoImportacion.vin)
    ).all()
    lineas = [(linea.vin, _costo_linea(linea, regimen)) for linea, regimen in _lineas_en_proceso(db, vins)]
    for vin, monto in (*compras, *gastos, *lineas):
        costos[vin] += monto
    # shortcut: una consulta por VIN a `taller`; agregar una versión por lote si el listado crece.
    for vin in vins:
        costos[vin] += taller.costo_taller_de_unidad(db, vin)
    return costos


# ── HU-4.08: hoja de costo de una unidad ──────────────────────────────────────


def _cuenta_en_proceso(db: Session) -> int:
    """Unidades en proceso: la cuenta que carga la compra de la unidad (regla de `contabilidad`)."""
    return contabilidad.cuenta_regla(db, DOCUMENTO_COMPRA, "unidad_en_transito")


def _lineas_en_proceso(db: Session, vins: list[str]) -> list[tuple[LineaFacturaCompra, str]]:
    """Líneas de facturas locales (HU-4.09) con VIN cargadas a unidades en proceso: repuestos y
    subcontratos comprados para la unidad, con el régimen del proveedor de su factura."""
    try:
        codigo = configuracion.obtener_cuenta(db, _cuenta_en_proceso(db)).codigo
    except ErrorNegocio:
        return []  # sin la regla ni el catálogo no puede haber líneas validadas contra él
    filas = db.execute(
        select(LineaFacturaCompra, FacturaCompra.regimen_proveedor)
        .join(FacturaCompra, FacturaCompra.id == LineaFacturaCompra.factura_id)
        .where(LineaFacturaCompra.vin.in_(vins), LineaFacturaCompra.cuenta == codigo)
        .order_by(FacturaCompra.fecha, LineaFacturaCompra.id)
    ).all()
    return [(linea, regimen) for linea, regimen in filas]


def _costo_linea(linea: LineaFacturaCompra, regimen: str) -> Decimal:
    """Lo que `registrar_factura` carga a la cuenta de la línea: la base, más su IVA cuando el
    proveedor es pequeño contribuyente (no da crédito fiscal)."""
    return linea.base + (linea.iva if regimen != "general" else 0)


def hoja_de_costo(db: Session, vin: str) -> dict:
    """Costo de la unidad agrupado en compra, importación y reacondicionamiento, y su cuadre con el
    mayor (criterio 3).

    Mientras la unidad está en proceso, el total se compara con el saldo de unidades en proceso
    para su VIN. Al darla de alta en la flota (HU-3.01) ese saldo vuelve a cero: entonces se compara
    con el saldo más el costo trasladado en el alta, que es todo lo que se cargó a la cuenta.
    """
    unidad = unidades.obtener_por_vin(db, vin)
    compra = db.scalar(select(CompraUnidad).where(CompraUnidad.vin == unidad.vin))
    orden_concepto = {c.codigo: (c.orden, c.nombre) for c in listar_conceptos(db)}
    gastos = sorted(
        listar_gastos_importacion(db, vin=unidad.vin),
        key=lambda g: (orden_concepto[g.concepto][0], g.fecha, g.id),
    )
    importacion = [
        {
            "concepto": g.concepto,
            "nombre": orden_concepto[g.concepto][1],
            "fecha": g.fecha,
            "documento": g.documento,
            "moneda": g.moneda,
            "monto": g.monto,
            "tipo_cambio": g.tipo_cambio,
            "monto_gtq": g.monto_gtq,
            "suma_al_costo": g.tratamiento == "costo",
        }
        for g in gastos
    ]
    mano_obra = [
        {"numero": o.numero, "fecha_cierre": o.fecha_cierre, "costo_gtq": o.costo_total}
        for o in taller.ordenes_de_unidad(db, unidad.vin)
        if o.estado == "cerrada" and o.tipo == "reacondicionamiento"
    ]
    repuestos = [
        {
            "documento": f"{linea.factura.serie}-{linea.factura.numero}",
            "proveedor": linea.factura.proveedor.nombre,
            "fecha": linea.factura.fecha,
            "descripcion": linea.descripcion,
            "monto_gtq": _costo_linea(linea, regimen),
        }
        for linea, regimen in _lineas_en_proceso(db, [unidad.vin])
    ]
    compra_gtq = compra.total_gtq if compra else Decimal(0)
    importacion_gtq = sum((g["monto_gtq"] for g in importacion if g["suma_al_costo"]), Decimal(0))
    reacondicionamiento_gtq = sum((x["costo_gtq"] for x in mano_obra), Decimal(0)) + sum(
        (x["monto_gtq"] for x in repuestos), Decimal(0)
    )
    total = compra_gtq + importacion_gtq + reacondicionamiento_gtq

    costo_alta = unidades.costo_de_alta(db, unidad.vin)
    saldo = contabilidad.saldo_cuenta(db, _cuenta_en_proceso(db), vin=unidad.vin)
    saldo_mayor = saldo + (costo_alta or 0)
    return {
        "vin": unidad.vin,
        "marca": unidad.marca,
        "linea": unidad.linea,
        "modelo": unidad.modelo,
        "estado": unidad.estado,
        "compra": None
        if compra is None
        else {
            "fecha": compra.fecha,
            "documento": compra.documento,
            "proveedor": compra.proveedor.nombre,
            "total_usd": compra.total_usd,
            "tipo_cambio": compra.tipo_cambio,
            "total_gtq": compra.total_gtq,
        },
        "importacion": importacion,
        "mano_obra": mano_obra,
        "repuestos": repuestos,
        "compra_gtq": compra_gtq,
        "importacion_gtq": importacion_gtq,
        "credito_fiscal_gtq": sum(
            (g["monto_gtq"] for g in importacion if not g["suma_al_costo"]), Decimal(0)
        ),
        "reacondicionamiento_gtq": reacondicionamiento_gtq,
        "total_gtq": total,
        "saldo_mayor_gtq": saldo_mayor,
        "costo_alta_gtq": costo_alta,
        "diferencia_gtq": total - saldo_mayor,
        "cuadra": total == saldo_mayor,
    }


# ── HU-4.02: compra de la unidad en EE. UU. ───────────────────────────────────

DOCUMENTO_COMPRA = "compra_unidad"  # tipo de documento de la partida (HU-2.03)


def registrar_compra_unidad(
    db: Session, datos: CompraUnidadEntrada, usuario_id: int | None = None
) -> CompraUnidad:
    """Crea la unidad, la compra, su cuenta por pagar y su partida en una transacción, o nada."""
    proveedor = obtener_proveedor(db, datos.proveedor_id)
    if proveedor.tipo != "exterior":
        raise ErrorNegocio("La compra en EE. UU. se registra a un proveedor del exterior")
    if datos.fecha > date.today():
        raise ErrorNegocio("La fecha de la compra no puede ser futura")
    if not datos.documento:
        raise ErrorNegocio("Indique el número de lote o de factura de la compra")
    precio = _monto(datos.precio_usd, "El precio", permite_cero=False)
    comision = _monto(datos.comision_usd, "La comisión", permite_cero=True)
    documentacion = _monto(datos.documentacion_usd, "El cargo de documentación", permite_cero=True)
    arrastre = _monto(datos.arrastre_usd, "El arrastre", permite_cero=True)
    total_usd = precio + comision + documentacion + arrastre
    if total_usd >= _LIMITE_MONTO:
        raise ErrorNegocio("El total de la compra excede el máximo permitido")
    # Sin tipo de cambio de la fecha, `configuracion` rechaza la compra antes de crear nada.
    tipo_cambio = configuracion.tipo_cambio_de(db, datos.fecha)
    total_gtq = redondear(convertir(total_usd, tipo_cambio), _DECIMALES_MONTO)
    if total_gtq >= _LIMITE_MONTO:
        raise ErrorNegocio("El equivalente en quetzales excede el máximo permitido")
    # Vehículos en tránsito (las unidades en proceso, con su VIN) y proveedores del exterior, en USD.
    cuenta_transito = contabilidad.cuenta_regla(db, DOCUMENTO_COMPRA, "unidad_en_transito")
    cuenta_proveedores = contabilidad.cuenta_regla(db, DOCUMENTO_COMPRA, "por_pagar_usd")

    try:
        unidad = unidades.registrar_unidad(
            db,
            UnidadEntrada(
                vin=datos.vin,
                marca=datos.marca,
                linea=datos.linea,
                modelo=datos.modelo,
                color=datos.color,
                tipo_vehiculo=datos.tipo_vehiculo,
                linea_negocio=datos.linea_negocio,
                estado="en_transito",
                documento=f"Compra {datos.documento} a {proveedor.nombre}"[:200],
            ),
            usuario_id=usuario_id,
            confirmar=False,
        )
        # El id se reserva antes: la partida se liga a la compra y la compra a su partida.
        compra_id = db.scalar(select(func.nextval("compra_unidad_id_seq")))
        partida = contabilidad.registrar_automatica(
            db,
            fecha=datos.fecha,
            concepto=f"Compra de la unidad {unidad.vin} a {proveedor.nombre}, {datos.documento}"[:300],
            lineas=[
                # Vehículos en tránsito no es cuenta monetaria en USD: se carga el equivalente en
                # quetzales, el mismo que obtiene el motor al convertir la línea del proveedor.
                LineaEntrada(
                    cuenta_id=cuenta_transito,
                    lado="debe",
                    monto=f"{total_gtq:.6f}",
                    linea_negocio=datos.linea_negocio,
                    vin=unidad.vin,
                ),
                LineaEntrada(
                    cuenta_id=cuenta_proveedores,
                    lado="haber",
                    monto=f"{total_usd:.6f}",
                    moneda="USD",
                    linea_negocio=datos.linea_negocio,
                    vin=unidad.vin,
                ),
            ],
            documento_tipo=DOCUMENTO_COMPRA,
            documento_id=compra_id,
            usuario_id=usuario_id,
        )
        compra = CompraUnidad(
            id=compra_id,
            vin=unidad.vin,
            proveedor_id=proveedor.id,
            fecha=datos.fecha,
            documento=datos.documento,
            precio_usd=precio,
            comision_usd=comision,
            documentacion_usd=documentacion,
            arrastre_usd=arrastre,
            total_usd=total_usd,
            tipo_cambio=tipo_cambio,
            total_gtq=total_gtq,
            partida_id=partida.id,
        )
        # La deuda queda en dólares, como la factura del proveedor.
        compra.cuenta_por_pagar = CuentaPorPagar(
            proveedor_id=proveedor.id,
            fecha=datos.fecha,
            fecha_vencimiento=datos.fecha + timedelta(days=proveedor.dias_credito),
            moneda="USD",
            monto=total_usd,
            saldo=total_usd,
        )
        db.add(compra)
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    except IntegrityError as error:
        # Dos compras simultáneas del mismo VIN: las restricciones UNIQUE deciden.
        db.rollback()
        restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if restriccion in ("unidad_vin_key", "uq_compra_unidad_vin"):
            raise ErrorNegocio(f"Ya existe una unidad con el VIN {datos.vin}", status=409) from None
        raise
    db.refresh(compra)
    return compra


def listar_compras_unidad(
    db: Session, vin: str | None = None, proveedor_id: int | None = None
) -> list[CompraUnidad]:
    """Compras de la más reciente a la más antigua, opcionalmente de una unidad o de un proveedor."""
    consulta = select(CompraUnidad).order_by(CompraUnidad.fecha.desc(), CompraUnidad.id.desc())
    if vin and vin.strip():
        consulta = consulta.where(CompraUnidad.vin == vin.strip().upper())
    if proveedor_id is not None:
        consulta = consulta.where(CompraUnidad.proveedor_id == proveedor_id)
    return list(db.scalars(consulta).unique())


def obtener_compra_unidad(db: Session, compra_id: int) -> CompraUnidad:
    compra = db.get(CompraUnidad, compra_id)
    if compra is None:
        raise ErrorNegocio(f"No existe la compra {compra_id}", status=404)
    return compra


# ── HU-4.13: programación y aprobación de pagos ───────────────────────────────

_PAGO_ACTIVO = ("propuesto", "aprobado")  # una cuenta por pagar está en uno solo a la vez


def _origen(cuenta: CuentaPorPagar) -> tuple[str, str, str | None]:
    """Tipo de documento que abrió la cuenta por pagar, su descripción corta y su VIN."""
    if cuenta.factura is not None:
        return "factura", f"Factura {cuenta.factura.serie}-{cuenta.factura.numero}", None
    if cuenta.gasto_importacion is not None:
        gasto = cuenta.gasto_importacion
        return "gasto_importacion", f"{gasto.concepto_nombre} {gasto.documento}", gasto.vin
    compra = cuenta.compra_unidad
    return "compra_unidad", f"Compra en EE. UU. {compra.documento}", compra.vin


def _programado_por_cuenta(db: Session, ids: list[int]) -> dict[int, Decimal]:
    """Monto en pagos propuestos o aprobados, aún sin ejecutar, de cada cuenta por pagar."""
    if not ids:
        return {}
    filas = db.execute(
        select(PagoProgramado.cuenta_por_pagar_id, func.sum(PagoProgramado.monto))
        .where(PagoProgramado.cuenta_por_pagar_id.in_(ids), PagoProgramado.estado.in_(_PAGO_ACTIVO))
        .group_by(PagoProgramado.cuenta_por_pagar_id)
    ).all()
    return dict(filas)


def cuentas_por_pagar_pendientes(
    db: Session,
    moneda: str | None = None,
    vence_hasta: date | None = None,
    proveedor_id: int | None = None,
) -> list[dict]:
    """Cuentas por pagar con saldo (criterio 1), de la que vence primero a la última: las vencidas
    y las que vencen hasta `vence_hasta`, de una moneda o de un proveedor."""
    consulta = (
        select(CuentaPorPagar)
        .where(CuentaPorPagar.saldo > 0)
        .order_by(CuentaPorPagar.fecha_vencimiento, CuentaPorPagar.id)
    )
    if moneda:
        consulta = consulta.where(CuentaPorPagar.moneda == moneda)
    if vence_hasta is not None:
        consulta = consulta.where(CuentaPorPagar.fecha_vencimiento <= vence_hasta)
    if proveedor_id is not None:
        consulta = consulta.where(CuentaPorPagar.proveedor_id == proveedor_id)
    cuentas = list(db.scalars(consulta).unique())
    programado = _programado_por_cuenta(db, [c.id for c in cuentas])
    hoy = date.today()
    resultado = []
    for cuenta in cuentas:
        origen, documento, vin = _origen(cuenta)
        resultado.append(
            {
                "id": cuenta.id,
                "proveedor_id": cuenta.proveedor_id,
                "proveedor": cuenta.proveedor.nombre,
                "origen": origen,
                "documento": documento,
                "vin": vin,
                "fecha": cuenta.fecha,
                "fecha_vencimiento": cuenta.fecha_vencimiento,
                "dias_vencida": (hoy - cuenta.fecha_vencimiento).days,
                "moneda": cuenta.moneda,
                "monto": cuenta.monto,
                "saldo": cuenta.saldo,
                "programado": programado.get(cuenta.id, Decimal(0)),
            }
        )
    return resultado


def _banco_activo(db: Session, cuenta_bancaria_id: int, prefijo: str = ""):
    banco = configuracion.obtener_cuenta_bancaria(db, cuenta_bancaria_id)
    if not banco.activa:
        raise ErrorNegocio(f"{prefijo}La cuenta bancaria {banco.banco} {banco.numero} está inactiva")
    return banco


def _a_moneda(monto: Decimal, de: str, a: str, tipo_cambio: Decimal | None) -> Decimal:
    """`monto` de la moneda `de` en la moneda `a`, redondeado como los montos (6 decimales)."""
    if de == a:
        return monto
    if a == "GTQ":
        return redondear(convertir(monto, tipo_cambio), _DECIMALES_MONTO)
    return redondear(monto / tipo_cambio, _DECIMALES_MONTO)


def _tipo_cambio_estimado(db: Session) -> Decimal | None:
    """El último tipo de cambio cargado, para estimar lo que sale de un banco en otra moneda."""
    cargados = configuracion.listar(db, hasta=date.today())
    return cargados[0].valor if cargados else None


def _saldo_banco(db: Session, banco) -> Decimal:
    """Saldo en libros de la cuenta bancaria, en su moneda (el mayor, HU-2.16)."""
    if banco.moneda == "USD":
        return contabilidad.saldo_cuenta_usd(db, banco.cuenta_id)
    return contabilidad.saldo_cuenta(db, banco.cuenta_id)


def _monto_banco(pago: PagoProgramado, banco, tipo_cambio: Decimal | None) -> Decimal | None:
    moneda = pago.cuenta_por_pagar.moneda
    if moneda != banco.moneda and tipo_cambio is None:
        return None
    return _a_moneda(pago.monto, moneda, banco.moneda, tipo_cambio)


def proponer_pagos(db: Session, datos: ProgramacionPagoEntrada, usuario_id: int) -> ProgramacionPago:
    """Crea la propuesta con sus pagos en estado propuesto (criterio 1), o nada."""
    if not datos.pagos:
        raise ErrorNegocio("Elija al menos una cuenta por pagar para la propuesta")
    if datos.fecha < date.today():
        raise ErrorNegocio("La fecha prevista de pago no puede ser pasada")
    ids = [pago.cuenta_por_pagar_id for pago in datos.pagos]
    if len(set(ids)) != len(ids):
        raise ErrorNegocio("Una cuenta por pagar aparece dos veces en la propuesta")
    # Bloqueadas hasta el commit: dos propuestas simultáneas no programan la misma cuenta.
    cuentas = {
        c.id: c
        for c in db.scalars(
            select(CuentaPorPagar).where(CuentaPorPagar.id.in_(ids)).with_for_update(of=CuentaPorPagar)
        ).unique()
    }
    programado = _programado_por_cuenta(db, ids)
    programacion = ProgramacionPago(
        fecha=datos.fecha, descripcion=datos.descripcion, propuesta_por=usuario_id
    )
    for numero, entrada in enumerate(datos.pagos, start=1):
        prefijo = f"Pago {numero}: "
        cuenta = cuentas.get(entrada.cuenta_por_pagar_id)
        if cuenta is None:
            raise ErrorNegocio(f"{prefijo}no existe la cuenta por pagar {entrada.cuenta_por_pagar_id}", 404)
        documento = _origen(cuenta)[1]
        if cuenta.saldo <= 0:
            raise ErrorNegocio(f"{prefijo}{documento} de {cuenta.proveedor.nombre} ya está pagado", 409)
        if programado.get(cuenta.id):
            raise ErrorNegocio(
                f"{prefijo}{documento} de {cuenta.proveedor.nombre} ya está en otra programación "
                "pendiente de ejecutar",
                409,
            )
        monto = _monto(entrada.monto, "el monto", permite_cero=False, prefijo=prefijo)
        if monto > cuenta.saldo:
            raise ErrorNegocio(f"{prefijo}el monto excede el saldo ({cuenta.saldo:.2f} {cuenta.moneda})")
        _banco_activo(db, entrada.cuenta_bancaria_id, prefijo)
        programacion.pagos.append(
            PagoProgramado(
                cuenta_por_pagar_id=cuenta.id,
                cuenta_bancaria_id=entrada.cuenta_bancaria_id,
                monto_propuesto=monto,
                monto=monto,
                estado="propuesto",
            )
        )
    db.add(programacion)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # el índice parcial decide entre dos propuestas simultáneas
        raise ErrorNegocio(
            "Una de las cuentas por pagar ya está en otra programación pendiente de ejecutar", 409
        ) from None
    db.refresh(programacion)
    return programacion


def listar_programaciones(db: Session) -> list[ProgramacionPago]:
    return list(
        db.scalars(
            select(ProgramacionPago).order_by(ProgramacionPago.fecha.desc(), ProgramacionPago.id.desc())
        )
    )


def obtener_programacion(db: Session, programacion_id: int) -> ProgramacionPago:
    programacion = db.get(ProgramacionPago, programacion_id)
    if programacion is None:
        raise ErrorNegocio(f"No existe la programación de pagos {programacion_id}", 404)
    return programacion


def _comprometido(db: Session, banco, excluir: int, tipo_cambio: Decimal | None) -> Decimal:
    """Pagos aprobados de otras programaciones que aún no salen de la cuenta bancaria."""
    pagos = db.scalars(
        select(PagoProgramado).where(
            PagoProgramado.cuenta_bancaria_id == banco.id,
            PagoProgramado.estado == "aprobado",
            PagoProgramado.programacion_id != excluir,
        )
    ).unique()
    montos = (_monto_banco(pago, banco, tipo_cambio) for pago in pagos)
    return sum((monto for monto in montos if monto is not None), Decimal(0))


def _pago_programado(pago: PagoProgramado, banco, monto_banco: Decimal | None) -> dict:
    cuenta = pago.cuenta_por_pagar
    _, documento, vin = _origen(cuenta)
    return {
        "id": pago.id,
        "programacion_id": pago.programacion_id,
        "cuenta_por_pagar_id": cuenta.id,
        "proveedor_id": cuenta.proveedor_id,
        "proveedor": cuenta.proveedor.nombre,
        "documento": documento,
        "vin": vin,
        "fecha_vencimiento": cuenta.fecha_vencimiento,
        "moneda": cuenta.moneda,
        "saldo": cuenta.saldo,
        "cuenta_bancaria_id": banco.id,
        "banco": f"{banco.banco} {banco.numero}",
        "moneda_banco": banco.moneda,
        "monto_propuesto": pago.monto_propuesto,
        "monto": pago.monto,
        "monto_banco": monto_banco,
        "estado": pago.estado,
        "decidido_por": pago.decidido_por,
        "decidido_en": pago.decidido_en,
        "comentario": pago.comentario,
    }


def detalle_programacion(db: Session, programacion: ProgramacionPago) -> dict:
    """La propuesta con sus pagos, los totales que salen en Q y en USD y, por cuenta bancaria, el
    saldo disponible frente a lo programado (criterio 2). Lo que sale de un banco en otra moneda
    que la del documento se estima con el último tipo de cambio cargado; el pago (HU-4.14) usa el
    de su fecha."""
    tipo_cambio = _tipo_cambio_estimado(db)
    bancos: dict = {}
    programado_banco: dict[int, Decimal] = {}
    totales = {"GTQ": Decimal(0), "USD": Decimal(0)}
    pagos = []
    for pago in programacion.pagos:
        if pago.cuenta_bancaria_id not in bancos:
            bancos[pago.cuenta_bancaria_id] = configuracion.obtener_cuenta_bancaria(
                db, pago.cuenta_bancaria_id
            )
            programado_banco[pago.cuenta_bancaria_id] = Decimal(0)
        banco = bancos[pago.cuenta_bancaria_id]
        monto_banco = _monto_banco(pago, banco, tipo_cambio)
        if monto_banco is not None and pago.estado not in ("rechazado", "anulado"):
            totales[banco.moneda] += monto_banco
        if monto_banco is not None and pago.estado in _PAGO_ACTIVO:
            programado_banco[banco.id] += monto_banco
        pagos.append(_pago_programado(pago, banco, monto_banco))
    saldos = []
    for banco in bancos.values():
        saldo = _saldo_banco(db, banco)
        comprometido = _comprometido(db, banco, programacion.id, tipo_cambio)
        programado = programado_banco[banco.id]
        saldos.append(
            {
                "cuenta_bancaria_id": banco.id,
                "banco": f"{banco.banco} {banco.numero}",
                "moneda": banco.moneda,
                "saldo_libros": saldo,
                "comprometido": comprometido,
                "disponible": saldo - comprometido,
                "programado": programado,
                "alcanza": programado <= saldo - comprometido,
            }
        )
    return {
        "id": programacion.id,
        "fecha": programacion.fecha,
        "descripcion": programacion.descripcion,
        "propuesta_por": programacion.propuesta_por,
        "creado_en": programacion.creado_en,
        "estado": "pendiente" if any(p.estado == "propuesto" for p in programacion.pagos) else "revisada",
        "pagos": pagos,
        "totales": totales,
        "tipo_cambio_estimado": tipo_cambio,
        "bancos": saldos,
    }


def decidir_pago(
    db: Session, programacion_id: int, pago_id: int, datos: DecisionPagoEntrada, usuario_id: int
) -> ProgramacionPago:
    """El gerente financiero aprueba, modifica (aprueba con otro monto o cuenta bancaria) o rechaza
    un pago propuesto (criterio 3). Quien propuso la programación no decide sus pagos (criterio 4,
    como HU-1.10 en las partidas)."""
    pago = db.scalar(
        select(PagoProgramado)
        .where(PagoProgramado.id == pago_id)
        .with_for_update(of=PagoProgramado)
        .execution_options(populate_existing=True)  # tras el candado: otra decisión pudo cambiarlo
    )
    if pago is None or pago.programacion_id != programacion_id:
        raise ErrorNegocio(f"La programación {programacion_id} no tiene el pago {pago_id}", 404)
    programacion = pago.programacion
    if programacion.propuesta_por == usuario_id:
        raise ErrorNegocio("No puedes aprobar ni rechazar un pago que propusiste tú", 403)
    if pago.estado != "propuesto":
        raise ErrorNegocio(f"El pago ya está {pago.estado}", 409)

    if datos.accion == "rechazar":
        if datos.monto is not None or datos.cuenta_bancaria_id is not None:
            raise ErrorNegocio("Un pago rechazado no cambia de monto ni de cuenta bancaria")
        if not datos.comentario:
            raise ErrorNegocio("Indique el motivo del rechazo")
        pago.estado = "rechazado"
    else:
        cuenta = pago.cuenta_por_pagar
        if datos.monto is not None:
            pago.monto = _monto(datos.monto, "El monto", permite_cero=False)
        if pago.monto > cuenta.saldo:
            raise ErrorNegocio(f"El monto excede el saldo ({cuenta.saldo:.2f} {cuenta.moneda})")
        if datos.cuenta_bancaria_id is not None:
            _banco_activo(db, datos.cuenta_bancaria_id)
            pago.cuenta_bancaria_id = datos.cuenta_bancaria_id
        pago.estado = "aprobado"
    pago.decidido_por = usuario_id
    pago.decidido_en = datetime.now(UTC)
    pago.comentario = datos.comentario
    db.commit()
    db.refresh(programacion)
    return programacion


# ── HU-4.14: pago a un proveedor ──────────────────────────────────────────────

DOCUMENTO_PAGO = "pago_proveedor"  # tipo de documento de la partida (HU-2.03)


def pagos_por_ejecutar(db: Session) -> list[dict]:
    """Pagos programados y aprobados que aún no se ejecutan, del que vence primero al último."""
    tipo_cambio = _tipo_cambio_estimado(db)
    programados = db.scalars(
        select(PagoProgramado)
        .join(CuentaPorPagar, CuentaPorPagar.id == PagoProgramado.cuenta_por_pagar_id)
        .where(PagoProgramado.estado == "aprobado")
        .order_by(CuentaPorPagar.fecha_vencimiento, PagoProgramado.id)
    ).unique()
    bancos: dict = {}
    resultado = []
    for programado in programados:
        if programado.cuenta_bancaria_id not in bancos:
            bancos[programado.cuenta_bancaria_id] = configuracion.obtener_cuenta_bancaria(
                db, programado.cuenta_bancaria_id
            )
        banco = bancos[programado.cuenta_bancaria_id]
        resultado.append(_pago_programado(programado, banco, _monto_banco(programado, banco, tipo_cambio)))
    return resultado


def _linea_proveedor(db: Session, cuenta: CuentaPorPagar):
    """La línea de la partida del documento que abrió la deuda (el crédito al proveedor): de ella
    salen la cuenta, la línea de negocio, el VIN y, en USD, el tipo de cambio del documento. Así el
    pago salda la misma cuenta aunque la regla de contabilización haya cambiado después."""
    if cuenta.factura_compra_id is not None:
        documento = (DOCUMENTO_FACTURA, cuenta.factura_compra_id)
    elif cuenta.gasto_importacion_id is not None:
        documento = (DOCUMENTO_GASTO, cuenta.gasto_importacion_id)
    else:
        documento = (DOCUMENTO_COMPRA, cuenta.compra_unidad_id)
    partida = contabilidad.partida_de_documento(db, *documento)
    return next(linea for linea in partida.lineas if linea.haber > 0)


def _bloqueados(db: Session, modelo, ids: list[int]) -> dict:
    """Filas por id, bloqueadas hasta el commit y leídas de nuevo tras el candado."""
    filas = db.scalars(
        select(modelo)
        .where(modelo.id.in_(ids))
        .with_for_update(of=modelo)
        .execution_options(populate_existing=True)
    ).unique()
    return {fila.id: fila for fila in filas}


def registrar_pago(db: Session, datos: PagoProveedorEntrada, usuario_id: int | None = None) -> PagoProveedor:
    """Ejecuta pagos aprobados (HU-4.13) de un proveedor desde una cuenta bancaria: baja el saldo de
    cada documento (total o parcial) y pide su partida, en una transacción, o nada.

    Partida: débito a la cuenta del proveedor de cada documento (la de su partida de origen) y
    crédito al banco por lo que sale. Un documento en USD se salda a su tipo de cambio en libros
    (`tipo_cambio_en_libros`, que considera las revaluaciones mantenidas) y el banco sale al tipo de
    cambio de la fecha; la diferencia es el diferencial realizado (`diferencial_cambiario`). Un
    documento en quetzales pagado desde un banco en USD sale por su equivalente en dólares; la
    fracción de centavo que deja el redondeo va a las mismas cuentas de diferencial."""
    if datos.fecha > date.today():
        raise ErrorNegocio("La fecha del pago no puede ser futura")
    contabilidad.exigir_periodo_abierto(db, datos.fecha)
    if not datos.referencia:
        que = "el número de cheque" if datos.forma_pago == "cheque" else "la referencia de la transferencia"
        raise ErrorNegocio(f"Indique {que}")
    ids = datos.pagos_programados
    if not ids:
        raise ErrorNegocio("Elija al menos un pago aprobado para ejecutar")
    if len(set(ids)) != len(ids):
        raise ErrorNegocio("Un pago programado aparece dos veces")
    banco = _banco_activo(db, datos.cuenta_bancaria_id)
    programados = _bloqueados(db, PagoProgramado, ids)
    faltan = [str(i) for i in ids if i not in programados]
    if faltan:
        raise ErrorNegocio(f"No existe el pago programado {', '.join(faltan)}", 404)
    cuentas = _bloqueados(db, CuentaPorPagar, [p.cuenta_por_pagar_id for p in programados.values()])
    for programado_id in ids:
        programado = programados[programado_id]
        cuenta = cuentas[programado.cuenta_por_pagar_id]
        documento = _origen(cuenta)[1]
        if programado.estado != "aprobado":
            raise ErrorNegocio(
                f"{documento}: solo se ejecuta un pago aprobado y este está {programado.estado}", 409
            )
        if programado.cuenta_bancaria_id != banco.id:
            raise ErrorNegocio(f"{documento}: el pago se aprobó desde otra cuenta bancaria")
        if programado.monto > cuenta.saldo:
            raise ErrorNegocio(f"{documento}: el monto aprobado excede el saldo ({cuenta.saldo:.2f})", 409)
    proveedores = {cuenta.proveedor_id for cuenta in cuentas.values()}
    if len(proveedores) != 1:
        raise ErrorNegocio("Un pago cancela documentos de un solo proveedor")
    proveedor = next(iter(cuentas.values())).proveedor
    usa_usd = banco.moneda == "USD" or any(c.moneda == "USD" for c in cuentas.values())
    # Sin el tipo de cambio de la fecha, `configuracion` rechaza el pago antes de tocar nada.
    tipo_cambio = configuracion.tipo_cambio_de(db, datos.fecha) if usa_usd else None

    pago = PagoProveedor(
        proveedor_id=proveedor.id,
        cuenta_bancaria_id=banco.id,
        moneda=banco.moneda,
        forma_pago=datos.forma_pago,
        referencia=datos.referencia,
        fecha=datos.fecha,
        tipo_cambio=tipo_cambio,
        estado="registrado",
        usuario_id=usuario_id,
    )
    lineas: list[LineaEntrada] = []
    for programado_id in ids:
        programado = programados[programado_id]
        cuenta = cuentas[programado.cuenta_por_pagar_id]
        monto = programado.monto
        origen = _linea_proveedor(db, cuenta)
        libros = None
        diferencial = Decimal(0)
        if cuenta.moneda == "USD":
            libros = contabilidad.tipo_cambio_en_libros(db, cuenta.fecha, origen.tipo_cambio, datos.fecha)
            lineas.append(
                LineaAutomatica(
                    cuenta_id=origen.cuenta_id,
                    lado="debe",
                    monto=f"{monto:f}",
                    moneda="USD",
                    linea_negocio=origen.linea_negocio,
                    vin=origen.vin,
                    tipo_cambio=libros,
                )
            )
            diferencial, linea_diferencial = contabilidad.diferencial_cambiario(
                db, monto, libros, tipo_cambio, "por_pagar"
            )
            if linea_diferencial is not None:
                lineas.append(linea_diferencial)
        else:
            lineas.append(
                LineaEntrada(
                    cuenta_id=origen.cuenta_id,
                    lado="debe",
                    monto=f"{monto:f}",
                    linea_negocio=origen.linea_negocio,
                    vin=origen.vin,
                )
            )
        monto_pago = _a_moneda(monto, cuenta.moneda, banco.moneda, tipo_cambio)
        if monto_pago <= 0:
            raise ErrorNegocio(
                f"El monto de {_origen(cuenta)[1]} es demasiado pequeño para pagarlo en {banco.moneda}"
            )
        lineas.append(
            LineaEntrada(
                cuenta_id=banco.cuenta_id, lado="haber", monto=f"{monto_pago:f}", moneda=banco.moneda
            )
        )
        if cuenta.moneda == "GTQ" and banco.moneda == "USD":
            ajuste = monto - redondear(convertir(monto_pago, tipo_cambio), _DECIMALES_MONTO)
            if ajuste:
                concepto, lado = ("ganancia", "haber") if ajuste > 0 else ("perdida", "debe")
                cuenta_ajuste = contabilidad.cuenta_regla(db, "diferencial_cambiario", concepto)
                lineas.append(LineaEntrada(cuenta_id=cuenta_ajuste, lado=lado, monto=f"{abs(ajuste):f}"))
                diferencial = ajuste
        pago.aplicaciones.append(
            AplicacionPago(
                cuenta_por_pagar_id=cuenta.id,
                pago_programado_id=programado.id,
                moneda_documento=cuenta.moneda,
                monto_documento=monto,
                monto_pago=monto_pago,
                tipo_cambio_libros=libros,
                diferencial=diferencial,
            )
        )
        cuenta.saldo -= monto
    pago.monto = sum((a.monto_pago for a in pago.aplicaciones), Decimal(0))
    pago.diferencial = sum((a.diferencial for a in pago.aplicaciones), Decimal(0))
    if pago.monto >= _LIMITE_MONTO:
        raise ErrorNegocio("El total del pago excede el máximo permitido")

    db.add(pago)
    try:
        db.flush()  # el id del pago liga su partida y los pagos programados que ejecuta
        for programado_id in ids:
            programados[programado_id].estado = "ejecutado"
            programados[programado_id].pago_id = pago.id
        forma = "Cheque" if datos.forma_pago == "cheque" else "Transferencia"
        contabilidad.registrar_automatica(
            db,
            fecha=datos.fecha,
            concepto=f"{forma} {datos.referencia} a {proveedor.nombre}"[:300],
            lineas=lineas,
            documento_tipo=DOCUMENTO_PAGO,
            documento_id=pago.id,
            usuario_id=usuario_id,
        )
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if restriccion == "uq_pago_proveedor_cheque":
            raise ErrorNegocio(
                f"El cheque {datos.referencia} de la cuenta {banco.banco} {banco.numero} ya está registrado",
                409,
            ) from None
        raise
    db.refresh(pago)
    return pago


def anular_pago(
    db: Session, pago_id: int, datos: AnulacionPagoEntrada, usuario_id: int | None = None
) -> PagoProveedor:
    """Anula el pago: revierte su partida (HU-2.05) con la fecha y el motivo dados, devuelve el saldo
    a cada documento y deja anulados sus pagos programados (volver a pagar pide otra aprobación)."""
    pago = _bloqueados(db, PagoProveedor, [pago_id]).get(pago_id)
    if pago is None:
        raise ErrorNegocio(f"No existe el pago {pago_id}", 404)
    if pago.estado == "anulado":
        raise ErrorNegocio("El pago ya está anulado", 409)
    if not datos.motivo:
        raise ErrorNegocio("Indique el motivo de la anulación")
    try:
        # Valida la fecha (no futura, no antes del pago, mes abierto) antes de tocar los documentos.
        contabilidad.revertir_automatica(db, DOCUMENTO_PAGO, pago.id, datos.fecha, datos.motivo, usuario_id)
        cuentas = _bloqueados(db, CuentaPorPagar, [a.cuenta_por_pagar_id for a in pago.aplicaciones])
        programados = _bloqueados(db, PagoProgramado, [a.pago_programado_id for a in pago.aplicaciones])
        for aplicacion in pago.aplicaciones:
            cuentas[aplicacion.cuenta_por_pagar_id].saldo += aplicacion.monto_documento
            programados[aplicacion.pago_programado_id].estado = "anulado"
        pago.estado = "anulado"
        pago.anulado_por = usuario_id
        pago.fecha_anulacion = datos.fecha
        pago.motivo_anulacion = datos.motivo
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    db.refresh(pago)
    return pago


def listar_pagos(db: Session, proveedor_id: int | None = None) -> list[PagoProveedor]:
    """Pagos del más reciente al más antiguo, opcionalmente de un proveedor."""
    consulta = select(PagoProveedor).order_by(PagoProveedor.fecha.desc(), PagoProveedor.id.desc())
    if proveedor_id is not None:
        consulta = consulta.where(PagoProveedor.proveedor_id == proveedor_id)
    return list(db.scalars(consulta).unique())


def obtener_pago(db: Session, pago_id: int) -> PagoProveedor:
    pago = db.get(PagoProveedor, pago_id)
    if pago is None:
        raise ErrorNegocio(f"No existe el pago {pago_id}", 404)
    return pago


def detalle_pago(db: Session, pago: PagoProveedor) -> dict:
    """El pago con lo que cancela de cada documento y los números de su partida y su reversión,
    para el comprobante."""
    banco = configuracion.obtener_cuenta_bancaria(db, pago.cuenta_bancaria_id)
    partida = contabilidad.partida_de_documento(db, DOCUMENTO_PAGO, pago.id)
    aplicaciones = []
    for aplicacion in pago.aplicaciones:
        cuenta = aplicacion.cuenta_por_pagar
        _, documento, vin = _origen(cuenta)
        aplicaciones.append(
            {
                "cuenta_por_pagar_id": cuenta.id,
                "documento": documento,
                "vin": vin,
                "moneda_documento": aplicacion.moneda_documento,
                "monto_documento": aplicacion.monto_documento,
                "monto_pago": aplicacion.monto_pago,
                "tipo_cambio_libros": aplicacion.tipo_cambio_libros,
                "diferencial": aplicacion.diferencial,
                "saldo_documento": cuenta.saldo,
            }
        )
    return {
        "id": pago.id,
        "proveedor_id": pago.proveedor_id,
        "proveedor": pago.proveedor.nombre,
        "cuenta_bancaria_id": banco.id,
        "banco": f"{banco.banco} {banco.numero}",
        "moneda": pago.moneda,
        "forma_pago": pago.forma_pago,
        "referencia": pago.referencia,
        "fecha": pago.fecha,
        "tipo_cambio": pago.tipo_cambio,
        "monto": pago.monto,
        "diferencial": pago.diferencial,
        "estado": pago.estado,
        "usuario_id": pago.usuario_id,
        "anulado_por": pago.anulado_por,
        "fecha_anulacion": pago.fecha_anulacion,
        "motivo_anulacion": pago.motivo_anulacion,
        "partida_numero": partida.numero,
        "reversion_numero": partida.reversion.numero if partida.reversion is not None else None,
        "creado_en": pago.creado_en,
        "aplicaciones": aplicaciones,
    }

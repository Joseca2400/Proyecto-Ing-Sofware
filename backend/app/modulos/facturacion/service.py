"""Reglas del módulo de facturación y cuentas por cobrar.

HU-6.01 (incluido): clientes individuales o empresas, identificados por NIT (con su verificador),
CUI o pasaporte con país; dirección, teléfono, correo y si son agentes de retención de IVA o ISR;
sin duplicados por identificación (también con altas simultáneas, por la restricción UNIQUE);
consulta por nombre o identificación.
HU-6.01 (diferido): consultar el nombre registrado en la SAT a través del certificador (criterio 2,
llega con FEL, HU-6.02); estado de cuenta integrado del cliente (criterio 4, Sprint 3). Del CUI
solo se exige que tenga 13 dígitos; su verificador no se calcula.

HU-6.02 parte 1 (incluido): factura con cliente o Consumidor Final, fecha, moneda, líneas (precio con
IVA, línea de negocio y VIN) y documento de origen; se certifica con el certificador configurado
(`comun/fel.py`, hoy el simulado). Certificada: guarda serie, número, autorización y XML, y crea su
cuenta por cobrar y su partida. Rechazada: guarda el motivo, sin partida ni cuenta por cobrar. En USD
guarda el tipo de cambio de la fecha y se contabiliza en quetzales. A Consumidor Final no se factura
por encima de `config.UMBRAL_CONSUMIDOR_FINAL` en quetzales.
Pendiente: certificador real y PDF certificado (HU-6.02 parte 2, Sprint 3); reintentar una factura que
quedó `pendiente` o certificada sin partida (Sprint 3); anulación (HU-6.05); notas de crédito
(HU-6.03); cobros (HU-6.07).

Para otros módulos: `obtener_cliente` y `listar_clientes` (contratos de alquiler, ventas, facturas);
`emitir_factura` (facturar un contrato cerrado con `origen_tipo="contrato"`) y `facturas_de_origen`.
"""

import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.comun import config, fel
from app.comun.dinero import a_decimal, convertir, redondear
from app.comun.errores import ErrorNegocio
from app.comun.nit import NITInvalido, formatear_nit, normalizar_nit
from app.modulos.configuracion import service as configuracion
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaEntrada
from app.modulos.facturacion.models import Cliente, CuentaPorCobrar, Factura, LineaFactura
from app.modulos.facturacion.schemas import ClienteEntrada, FacturaEntrada, LineaFacturaFelEntrada
from app.modulos.unidades import service as unidades

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ETIQUETA = {"nit": "el NIT", "cui": "el CUI", "pasaporte": "el pasaporte"}


def _repetido(tipo: str, identificacion: str) -> ErrorNegocio:
    valor = formatear_nit(identificacion) if tipo == "nit" else identificacion
    return ErrorNegocio(f"Ya existe un cliente con {_ETIQUETA[tipo]} {valor}", status=409)


def registrar_cliente(db: Session, datos: ClienteEntrada) -> Cliente:
    if not datos.nombre:
        raise ErrorNegocio("El nombre del cliente es obligatorio")
    if not datos.identificacion:
        raise ErrorNegocio("La identificación del cliente es obligatoria")
    if datos.tipo == "empresa" and datos.tipo_identificacion != "nit":
        raise ErrorNegocio("Una empresa se identifica con su NIT")
    if datos.correo and not _CORREO.match(datos.correo):
        raise ErrorNegocio("El correo no tiene un formato válido")

    tipo_id = datos.tipo_identificacion
    pais = None
    if tipo_id == "nit":
        try:
            identificacion = normalizar_nit(datos.identificacion)
        except NITInvalido as error:
            raise ErrorNegocio(str(error)) from None
    elif tipo_id == "cui":
        identificacion = re.sub(r"\s", "", datos.identificacion)
        if not re.fullmatch(r"\d{13}", identificacion):
            raise ErrorNegocio("El CUI debe tener 13 dígitos")
    else:
        identificacion = datos.identificacion.upper()
        pais = (datos.pais or "").upper()
        if not (len(pais) == 2 and pais.isalpha() and pais.isascii()):
            raise ErrorNegocio("Un pasaporte requiere el país, con su código de dos letras, por ejemplo US")
    if tipo_id != "pasaporte" and datos.pais:
        raise ErrorNegocio("El país solo se indica cuando el cliente se identifica con pasaporte")

    existente = select(Cliente.id).where(
        Cliente.tipo_identificacion == tipo_id, Cliente.identificacion == identificacion
    )
    if db.scalar(existente) is not None:
        raise _repetido(tipo_id, identificacion)

    cliente = Cliente(
        tipo=datos.tipo,
        nombre=datos.nombre,
        tipo_identificacion=tipo_id,
        identificacion=identificacion,
        pais=pais,
        direccion=datos.direccion,
        telefono=datos.telefono,
        correo=datos.correo,
        agente_retencion_iva=datos.agente_retencion_iva,
        agente_retencion_isr=datos.agente_retencion_isr,
    )
    db.add(cliente)
    try:
        db.commit()
    except IntegrityError:
        # Dos altas simultáneas con la misma identificación: la restricción UNIQUE decide.
        db.rollback()
        raise _repetido(tipo_id, identificacion) from None
    db.refresh(cliente)
    return cliente


def _patron_contiene(texto: str) -> str:
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def listar_clientes(db: Session, buscar: str | None = None) -> list[Cliente]:
    """Clientes en orden alfabético, con búsqueda por nombre o identificación."""
    consulta = select(Cliente).order_by(Cliente.nombre, Cliente.id)
    if buscar and buscar.strip():
        texto = buscar.strip()
        # La identificación se guarda normalizada (NIT sin guion, en mayúsculas): se busca igual.
        limpio = re.sub(r"[\s-]", "", texto).upper()
        condiciones = [Cliente.nombre.ilike(_patron_contiene(texto), escape="\\")]
        if limpio:
            condiciones.append(Cliente.identificacion.ilike(_patron_contiene(limpio), escape="\\"))
        consulta = consulta.where(or_(*condiciones))
    return list(db.scalars(consulta))


def obtener_cliente(db: Session, cliente_id: int) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise ErrorNegocio("El cliente no existe", status=404)
    return cliente


# ── HU-6.02: facturas FEL ──────────────────────────────────────────────────────

DOCUMENTO = "factura"
TASA_IVA = Decimal("0.12")  # IVA general de Guatemala; el precio de cada línea lo incluye
CONSUMIDOR_FINAL = "Consumidor Final"
_DECIMALES = 6
_LIMITE = Decimal("1000000000000")  # cabe en NUMERIC(18, 6)


def _numero(texto: str, que: str, numero: int) -> Decimal:
    try:
        valor = a_decimal(texto)
    except (InvalidOperation, ValueError):
        raise ErrorNegocio(f"Línea {numero}: {que} no es un número válido") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio(f"Línea {numero}: {que} debe ser mayor que cero")
    if -valor.as_tuple().exponent > _DECIMALES or valor >= _LIMITE:  # type: ignore[operator]
        raise ErrorNegocio(f"Línea {numero}: {que} admite hasta {_DECIMALES} decimales y menos de un billón")
    return valor


def _linea(db: Session, numero: int, datos: LineaFacturaFelEntrada) -> LineaFactura:
    if not datos.descripcion:
        raise ErrorNegocio(f"Línea {numero}: la descripción es obligatoria")
    cantidad = _numero(datos.cantidad, "la cantidad", numero)
    precio = _numero(datos.precio_unitario, "el precio unitario", numero)
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
    total = redondear(cantidad * precio)
    if total <= 0 or total >= _LIMITE:
        raise ErrorNegocio(f"Línea {numero}: el total de la línea debe ser mayor que cero")
    # El precio incluye IVA: la base sale del total y el IVA es la diferencia, así base + IVA = total.
    base = redondear(total / (1 + TASA_IVA))
    return LineaFactura(
        numero_linea=numero,
        descripcion=datos.descripcion,
        cantidad=cantidad,
        precio_unitario=precio,
        total=total,
        base=base,
        iva=total - base,
        linea_negocio=datos.linea_negocio,
        vin=vin,
    )


def _dimensiones(db: Session, cuenta_id: int, linea: str | None, vin: str | None, prefijo: str) -> None:
    try:
        configuracion.resolver_dimensiones(db, cuenta_id, linea, vin)
    except ErrorNegocio as error:
        raise ErrorNegocio(f"{prefijo}{error.mensaje}", error.status) from None


def _asiento(
    db: Session, moneda: str, tipo_cambio: Decimal | None, lineas: list[LineaFactura]
) -> tuple[list[LineaEntrada], Decimal]:
    """Líneas de la partida y total en quetzales, validadas contra las reglas y las cuentas.

    Debe: cuenta por cobrar por el total, una línea por línea de negocio (la cuenta la exige), en la
    moneda de la factura. Haber: ingreso de cada línea por su base, con su línea de negocio y VIN, e
    IVA débito fiscal. En USD el motor convierte cada cargo con el tipo de cambio y redondea a 6
    decimales; los ingresos se convierten igual y el IVA en quetzales es la diferencia, para que la
    partida cuadre exacta.
    """
    por_cobrar = contabilidad.cuenta_regla(db, DOCUMENTO, f"por_cobrar_{moneda.lower()}")
    iva_debito = contabilidad.cuenta_regla(db, DOCUMENTO, "iva_debito")
    if moneda == "USD" and not configuracion.obtener_cuenta(db, por_cobrar).monetaria_usd:
        raise ErrorNegocio(
            "La cuenta de la regla «factura · por_cobrar_usd» no admite montos en dólares", 409
        )

    def en_quetzales(monto: Decimal) -> Decimal:
        return monto if tipo_cambio is None else redondear(convertir(monto, tipo_cambio), _DECIMALES)

    cargos: dict[str, Decimal] = defaultdict(Decimal)
    ingresos = []
    for linea in lineas:
        cuenta = contabilidad.cuenta_regla(db, DOCUMENTO, f"ingreso_{linea.linea_negocio}")
        _dimensiones(db, cuenta, linea.linea_negocio, linea.vin, f"Línea {linea.numero_linea}: ")
        ingresos.append(
            LineaEntrada(
                cuenta_id=cuenta,
                lado="haber",
                monto=f"{en_quetzales(linea.base):.6f}",
                linea_negocio=linea.linea_negocio,
                vin=linea.vin,
            )
        )
        cargos[linea.linea_negocio] += linea.total
    debitos = []
    for linea_negocio, total in cargos.items():
        _dimensiones(db, por_cobrar, linea_negocio, None, "Cuenta por cobrar: ")
        debitos.append(
            LineaEntrada(
                cuenta_id=por_cobrar,
                lado="debe",
                monto=f"{total:.6f}",
                moneda=moneda,
                linea_negocio=linea_negocio,
            )
        )
    total_gtq = sum((en_quetzales(total) for total in cargos.values()), Decimal(0))
    iva_gtq = total_gtq - sum((en_quetzales(linea.base) for linea in lineas), Decimal(0))
    _dimensiones(db, iva_debito, None, None, "IVA débito fiscal: ")
    iva = [LineaEntrada(cuenta_id=iva_debito, lado="haber", monto=f"{iva_gtq:.6f}")] if iva_gtq > 0 else []
    return [*debitos, *ingresos, *iva], total_gtq


def _documento_fel(factura: Factura, receptor_tipo: str) -> fel.DocumentoFEL:
    return fel.DocumentoFEL(
        referencia=str(factura.id),
        emisor_nit=factura.emisor_nit,
        emisor_nombre=factura.emisor_nombre,
        receptor_id=factura.receptor_id,
        receptor_tipo=receptor_tipo,
        receptor_nombre=factura.receptor_nombre,
        fecha=factura.fecha,
        moneda=factura.moneda,
        tipo_cambio=factura.tipo_cambio,
        lineas=tuple(
            fel.LineaFEL(linea.descripcion, linea.cantidad, linea.precio_unitario, linea.total, linea.iva)
            for linea in factura.lineas
        ),
        total=factura.total,
        iva=factura.iva,
    )


def _guardar_certificacion(factura: Factura, certificacion: fel.Certificacion) -> None:
    factura.estado = "certificada"
    factura.serie = certificacion.serie
    factura.numero = certificacion.numero
    factura.autorizacion = certificacion.autorizacion
    factura.certificada_en = certificacion.certificada_en
    factura.xml = certificacion.xml


def emitir_factura(db: Session, datos: FacturaEntrada, usuario_id: int | None = None) -> Factura:
    """Emite la factura: la valida, la certifica y, si se certifica, la contabiliza.

    Devuelve la factura `certificada` (con su cuenta por cobrar y su partida) o `rechazada` (con el
    motivo, sin efecto contable); el llamador revisa `estado`. Confirma la transacción por su cuenta:
    no debe llamarse con cambios pendientes de otro documento en la misma sesión.

    Orden, para no perder un documento certificado ni contabilizar uno rechazado:
    1. Se valida todo lo que podría impedir la partida (perfil fiscal, cliente, líneas, VIN, tipo de
       cambio, reglas y dimensiones de las cuentas, umbral de Consumidor Final) antes de certificar.
    2. Se guarda la factura `pendiente` y se confirma: queda constancia del intento antes de salir al
       certificador, y su id es la referencia del documento ante él.
    3. Rechazo: se guarda el motivo y se confirma; nunca se llega a la partida.
    4. Certificación: datos FEL, cuenta por cobrar y partida en una sola transacción. Si ese paso
       falla, se revierte y se guardan solo los datos FEL (certificada, sin partida) para no perder
       el documento que ya existe ante la SAT, y se informa el error.
    """
    if datos.fecha > date.today():
        raise ErrorNegocio("La fecha de la factura no puede ser futura")
    if (datos.origen_tipo is None) != (datos.origen_id is None):
        raise ErrorNegocio("Indique el tipo y el número del documento de origen, o ninguno de los dos")
    if not datos.lineas:
        raise ErrorNegocio("La factura necesita al menos una línea")
    emisor = configuracion.perfil_fiscal_vigente(db, datos.fecha)
    if emisor is None:
        raise ErrorNegocio(
            f"No hay perfil fiscal de la empresa vigente al {datos.fecha:%d/%m/%Y}; "
            "regístrelo antes de facturar",
            409,
        )
    cliente = obtener_cliente(db, datos.cliente_id) if datos.cliente_id is not None else None
    lineas = [_linea(db, numero, linea) for numero, linea in enumerate(datos.lineas, start=1)]
    tipo_cambio = configuracion.tipo_cambio_de(db, datos.fecha) if datos.moneda == "USD" else None
    asiento, total_gtq = _asiento(db, datos.moneda, tipo_cambio, lineas)
    if cliente is None and total_gtq > config.UMBRAL_CONSUMIDOR_FINAL:
        raise ErrorNegocio(
            f"Una factura de más de Q{config.UMBRAL_CONSUMIDOR_FINAL:,.2f} no puede emitirse a Consumidor "
            "Final: indique un cliente con NIT o CUI"
        )

    base = sum((linea.base for linea in lineas), Decimal(0))
    iva = sum((linea.iva for linea in lineas), Decimal(0))
    factura = Factura(
        cliente_id=cliente.id if cliente else None,
        fecha=datos.fecha,
        moneda=datos.moneda,
        tipo_cambio=tipo_cambio,
        origen_tipo=datos.origen_tipo,
        origen_id=datos.origen_id,
        dias_credito=datos.dias_credito,
        emisor_nit=emisor.nit,
        emisor_nombre=emisor.razon_social,
        receptor_id=cliente.identificacion if cliente else fel.CONSUMIDOR_FINAL,
        receptor_nombre=cliente.nombre if cliente else CONSUMIDOR_FINAL,
        base=base,
        iva=iva,
        total=base + iva,
        total_gtq=total_gtq,
        estado="pendiente",
        creado_por=usuario_id,
        lineas=lineas,
    )
    db.add(factura)
    db.commit()

    try:
        certificacion = fel.certificador().certificar(
            _documento_fel(factura, cliente.tipo_identificacion if cliente else "cf")
        )
    except fel.RechazoFEL as rechazo:
        factura.estado = "rechazada"
        factura.motivo_rechazo = rechazo.motivo[:500]
        db.commit()
        db.refresh(factura)
        return factura

    _guardar_certificacion(factura, certificacion)
    factura.cuenta_por_cobrar = CuentaPorCobrar(
        cliente_id=factura.cliente_id,
        fecha=factura.fecha,
        fecha_vencimiento=factura.fecha + timedelta(days=factura.dias_credito),
        moneda=factura.moneda,
        monto=factura.total,
        saldo=factura.total,
    )
    try:
        partida = contabilidad.registrar_automatica(
            db,
            fecha=factura.fecha,
            concepto=f"Factura {certificacion.serie}-{certificacion.numero} a {factura.receptor_nombre}"[
                :300
            ],
            lineas=asiento,
            documento_tipo=DOCUMENTO,
            documento_id=factura.id,
            usuario_id=usuario_id,
        )
        factura.partida_id = partida.id
        db.commit()
    except (ErrorNegocio, SQLAlchemyError) as error:
        db.rollback()
        _guardar_certificacion(factura, certificacion)
        db.commit()
        motivo = error.mensaje if isinstance(error, ErrorNegocio) else "error de la base de datos"
        raise ErrorNegocio(
            f"La factura {certificacion.serie}-{certificacion.numero} quedó certificada, pero no se pudo "
            f"contabilizar: {motivo}",
            409,
        ) from error
    db.refresh(factura)
    return factura


def listar_facturas(db: Session) -> list[Factura]:
    return list(db.scalars(select(Factura).order_by(Factura.fecha.desc(), Factura.id.desc())))


def obtener_factura(db: Session, factura_id: int) -> Factura:
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise ErrorNegocio("La factura no existe", status=404)
    return factura


def facturas_de_origen(db: Session, origen_tipo: str, origen_id: int) -> list[Factura]:
    """Facturas (de cualquier estado) emitidas para un contrato, una venta o una orden."""
    return list(
        db.scalars(
            select(Factura)
            .where(Factura.origen_tipo == origen_tipo, Factura.origen_id == origen_id)
            .order_by(Factura.id)
        )
    )

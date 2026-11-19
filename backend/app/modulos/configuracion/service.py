"""Reglas del módulo de configuración.

Equipo A — catálogo de cuentas y dimensiones analíticas (HU-1.02, HU-1.04).
`resolver_dimensiones` es lo que el motor contable llama por cada línea de una partida.

Equipo B — tipo de cambio y transacciones en USD (Sprint 1):
HU-1.06 (incluido): carga manual del tipo de cambio positivo por fecha; bloqueo cuando falta.
HU-1.06 (diferido): consulta automática al Banguat (adaptador en `comun/`) y corrección con
aprobación del gerente financiero.
HU-1.07 (incluido): registro de transacciones en USD con monto original, tipo de cambio aplicado
y equivalente en quetzales; tipo personalizado positivo con justificación obligatoria.
HU-1.07 (diferido): reportes de saldos en USD.

Equipo C — perfil fiscal de la empresa (HU-1.01, Sprint 1):
Datos de la empresa con NIT validado, régimen de ISR y calidad de agente de retención, en
versiones con fecha de vigencia que no se modifican; y las tasas impositivas, también con
vigencia. Los demás módulos leen `perfil_vigente` y `tasa_vigente` para la fecha de su
documento; los cálculos (provisión de ISR, retenciones, IVA de intereses) son de sus historias.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.dinero import a_decimal, convertir, redondear
from app.comun.errores import ErrorNegocio
from app.comun.nit import NITInvalido, normalizar_nit
from app.modulos.configuracion.models import (
    REGIMENES_ISR,
    TIPOS_TASA,
    Cuenta,
    PerfilFiscal,
    TasaImpositiva,
    TipoCambio,
    TransaccionUSD,
)

# ── HU-1.02 y HU-1.04: catálogo de cuentas y dimensiones ──────────────────────

TIPOS = ("activo", "pasivo", "patrimonio", "ingreso", "costo", "gasto")
NATURALEZAS = ("deudora", "acreedora")
LINEAS_NEGOCIO = ("alquiler", "venta", "taller", "financiamiento", "administracion")
VIN_OBLIGATORIO, VIN_OPCIONAL, VIN_NO_APLICA = "obligatorio", "opcional", "no_aplica"
MODOS_VIN = (VIN_OBLIGATORIO, VIN_OPCIONAL, VIN_NO_APLICA)


def listar_cuentas(db: Session, solo_detalle: bool = False) -> list[Cuenta]:
    """Ordenadas por código: con el nivel de cada una basta para dibujar el árbol."""
    consulta = select(Cuenta).order_by(Cuenta.codigo)
    if solo_detalle:
        consulta = consulta.where(Cuenta.es_detalle)
    return list(db.scalars(consulta))


def _cuenta(db: Session, cuenta_id: int) -> Cuenta:
    cuenta = db.get(Cuenta, cuenta_id)
    if cuenta is None:
        raise ErrorNegocio("La cuenta no existe", 404)
    return cuenta


def _fijar_dimensiones(cuenta: Cuenta, linea_obligatoria: bool, vin: str, linea_defecto: str | None) -> None:
    if vin not in MODOS_VIN:
        raise ErrorNegocio(f"VIN debe ser uno de: {', '.join(MODOS_VIN)}")
    if linea_defecto is not None and linea_defecto not in LINEAS_NEGOCIO:
        raise ErrorNegocio(f"Línea de negocio desconocida: {linea_defecto}")
    if not cuenta.es_detalle and (linea_obligatoria or vin != VIN_NO_APLICA or linea_defecto):
        raise ErrorNegocio("Las dimensiones solo se definen en cuentas de detalle")
    cuenta.linea_obligatoria, cuenta.vin, cuenta.linea_defecto = linea_obligatoria, vin, linea_defecto


def crear_cuenta(
    db: Session,
    codigo: str,
    nombre: str,
    tipo: str,
    naturaleza: str,
    padre_id: int | None = None,
    es_detalle: bool = True,
    monetaria_usd: bool = False,
    linea_obligatoria: bool = False,
    vin: str = VIN_NO_APLICA,
    linea_defecto: str | None = None,
) -> Cuenta:
    codigo = codigo.strip()
    nombre = nombre.strip()
    if not codigo or not nombre:
        raise ErrorNegocio("El código y el nombre son obligatorios")
    if len(codigo) > 30 or len(nombre) > 200:
        raise ErrorNegocio("El código admite hasta 30 caracteres y el nombre hasta 200", 422)
    if tipo not in TIPOS or naturaleza not in NATURALEZAS:
        raise ErrorNegocio("Tipo o naturaleza desconocidos")
    if db.scalar(select(Cuenta.id).where(Cuenta.codigo == codigo)) is not None:
        raise ErrorNegocio(f"Ya existe la cuenta {codigo}", 409)
    nivel = 1
    if padre_id is not None:
        padre = _cuenta(db, padre_id)
        if padre.es_detalle:
            raise ErrorNegocio("Una cuenta de detalle no puede tener cuentas hijas")
        if padre.tipo != tipo:
            raise ErrorNegocio(f"La cuenta hija debe ser del mismo tipo que la cuenta padre ({padre.tipo})")
        nivel = padre.nivel + 1
    cuenta = Cuenta(
        codigo=codigo, nombre=nombre.strip(), tipo=tipo, naturaleza=naturaleza, nivel=nivel,
        padre_id=padre_id, es_detalle=es_detalle, monetaria_usd=monetaria_usd,
    )  # fmt: skip
    _fijar_dimensiones(cuenta, linea_obligatoria, vin, linea_defecto)
    db.add(cuenta)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if (
            getattr(exc.orig, "sqlstate", None) == "23505"
            and getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "cuentas_codigo_key"
        ):
            raise ErrorNegocio(f"Ya existe la cuenta {codigo}", 409) from exc
        raise
    return cuenta


def definir_dimensiones(
    db: Session, cuenta_id: int, linea_obligatoria: bool, vin: str, linea_defecto: str | None
) -> Cuenta:
    cuenta = _cuenta(db, cuenta_id)
    _fijar_dimensiones(cuenta, linea_obligatoria, vin, linea_defecto)
    db.commit()
    return cuenta


def resolver_dimensiones(db: Session, cuenta_id: int, linea: str | None, vin: str | None) -> str | None:
    """Valida una línea de partida contra su cuenta y devuelve la línea de negocio a guardar.

    Usa la línea por defecto de la cuenta si no se indicó una. Rechaza lo que la cuenta no admite.
    """
    cuenta = _cuenta(db, cuenta_id)
    if not cuenta.es_detalle:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} es de agrupación y no recibe movimientos")
    linea = linea or cuenta.linea_defecto
    if linea is not None and linea not in LINEAS_NEGOCIO:
        raise ErrorNegocio(f"Línea de negocio desconocida: {linea}")
    if linea is None and cuenta.linea_obligatoria:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} exige línea de negocio")
    vin = (vin or "").strip()
    if not vin and cuenta.vin == VIN_OBLIGATORIO:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} exige el VIN de la unidad")
    if vin and cuenta.vin == VIN_NO_APLICA:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} no admite VIN")
    return linea


# ── HU-1.06: tipo de cambio ────────────────────────────────────────────────────

DECIMALES_TIPO_CAMBIO = 8


def _validar_valor(texto: str) -> Decimal:
    try:
        valor = a_decimal(texto.strip())
    except (InvalidOperation, ValueError):
        raise ErrorNegocio("El tipo de cambio debe ser un número, por ejemplo 7.75") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio("El tipo de cambio debe ser mayor que cero")
    if -valor.as_tuple().exponent > DECIMALES_TIPO_CAMBIO:
        raise ErrorNegocio(f"El tipo de cambio admite como máximo {DECIMALES_TIPO_CAMBIO} decimales")
    if valor >= Decimal("10000000000"):
        raise ErrorNegocio("El tipo de cambio es demasiado grande")
    return valor


def registrar_manual(db: Session, fecha: date, valor: str) -> TipoCambio:
    """Carga manual del tipo de cambio de una fecha. No reemplaza uno ya cargado."""
    if fecha > date.today():
        raise ErrorNegocio("No se puede cargar el tipo de cambio de una fecha futura")
    valor_decimal = _validar_valor(valor)
    if db.scalar(select(TipoCambio.id).where(TipoCambio.fecha == fecha)) is not None:
        raise ErrorNegocio(
            f"Ya existe el tipo de cambio del {fecha:%d/%m/%Y}; corregirlo requiere aprobación",
            status=409,
        )
    tipo = TipoCambio(fecha=fecha, valor=valor_decimal, origen="manual")
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


def listar(db: Session, desde: date | None = None, hasta: date | None = None) -> list[TipoCambio]:
    consulta = select(TipoCambio).order_by(TipoCambio.fecha.desc())
    if desde:
        consulta = consulta.where(TipoCambio.fecha >= desde)
    if hasta:
        consulta = consulta.where(TipoCambio.fecha <= hasta)
    return list(db.scalars(consulta))


def buscar(db: Session, fecha: date) -> TipoCambio | None:
    return db.scalar(select(TipoCambio).where(TipoCambio.fecha == fecha))


def tipo_cambio_de(db: Session, fecha: date) -> Decimal:
    """Valor para convertir una transacción en USD de esa fecha (lo usa HU-1.07).

    Si no existe, rechaza la operación: la transacción no se guarda hasta que se cargue.
    """
    tipo = buscar(db, fecha)
    if tipo is None:
        raise ErrorNegocio(
            f"No existe tipo de cambio para el {fecha:%d/%m/%Y}; cárguelo antes de registrar "
            "la transacción en dólares",
            status=409,
        )
    return tipo.valor


# ── HU-1.07: transacciones en USD ─────────────────────────────────────────────

_MAX_DECIMALES_MONTO = 6


def _validar_monto_usd(texto: str) -> Decimal:
    try:
        valor = a_decimal(texto.strip())
    except (InvalidOperation, ValueError):
        raise ErrorNegocio("El monto en USD debe ser un número, por ejemplo 8500.00") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio("El monto en USD debe ser mayor que cero")
    if -valor.as_tuple().exponent > _MAX_DECIMALES_MONTO:
        raise ErrorNegocio(f"El monto en USD admite como máximo {_MAX_DECIMALES_MONTO} decimales")
    return valor


def registrar_transaccion_usd(
    db: Session,
    fecha: date,
    monto_usd_texto: str,
    tipo_cambio_personalizado: str | None = None,
    justificacion: str | None = None,
) -> TransaccionUSD:
    """Registra una transacción en USD y calcula su equivalente en quetzales.

    Por defecto usa el tipo de cambio del Banguat de la fecha. Si se indica un tipo personalizado,
    debe ser positivo y la justificación es obligatoria (criterio 4 de HU-1.07).
    """
    monto_usd = _validar_monto_usd(monto_usd_texto)

    if tipo_cambio_personalizado is not None:
        tc = _validar_valor(tipo_cambio_personalizado)
        if not justificacion or not justificacion.strip():
            raise ErrorNegocio("El tipo de cambio personalizado requiere justificación")
        justificacion = justificacion.strip()
    else:
        tc = tipo_cambio_de(db, fecha)
        justificacion = None

    monto_gtq = redondear(convertir(monto_usd, tc), _MAX_DECIMALES_MONTO)

    transaccion = TransaccionUSD(
        fecha=fecha,
        monto_usd=monto_usd,
        tipo_cambio_aplicado=tc,
        monto_gtq=monto_gtq,
        justificacion=justificacion,
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion


def listar_transacciones_usd(
    db: Session,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[TransaccionUSD]:
    consulta = select(TransaccionUSD).order_by(TransaccionUSD.fecha.desc(), TransaccionUSD.id.desc())
    if desde:
        consulta = consulta.where(TransaccionUSD.fecha >= desde)
    if hasta:
        consulta = consulta.where(TransaccionUSD.fecha <= hasta)
    return list(db.scalars(consulta))


# ── HU-1.01: perfil fiscal de la empresa ──────────────────────────────────────

# Tasas que usa cada régimen de ISR, además del IVA y del umbral de Consumidor Final. El ISO
# solo aplica en el régimen sobre utilidades.
TASAS_POR_REGIMEN = {
    "opcional_simplificado": ("IVA_GENERAL", "ISR_SIMPLIFICADO_1", "ISR_SIMPLIFICADO_2", "UMBRAL_CF"),
    "sobre_utilidades": ("IVA_GENERAL", "ISR_UTILIDADES", "ISO", "UMBRAL_CF"),
}

# Qué lleva cada tipo: porcentaje, monto límite o ambos (el primer tramo del ISR simplificado).
_LLEVA_PORCENTAJE = {t for t in TIPOS_TASA if t != "UMBRAL_CF"}
_LLEVA_MONTO = {"ISR_SIMPLIFICADO_1", "UMBRAL_CF"}


def _texto_obligatorio(valor: str, campo: str, maximo: int) -> str:
    valor = (valor or "").strip()
    if not valor:
        raise ErrorNegocio(f"{campo} es obligatorio")
    if len(valor) > maximo:
        raise ErrorNegocio(f"{campo} admite hasta {maximo} caracteres", 422)
    return valor


def registrar_perfil(
    db: Session,
    vigente_desde: date,
    razon_social: str,
    nombre_comercial: str,
    nit: str,
    direccion_fiscal: str,
    establecimiento_sat: int,
    regimen_isr: str,
    agente_retencion_iva: bool = False,
    agente_retencion_isr: bool = False,
) -> PerfilFiscal:
    """Agrega una versión del perfil fiscal. Las anteriores no se tocan (criterio 4)."""
    razon_social = _texto_obligatorio(razon_social, "La razón social", 200)
    nombre_comercial = _texto_obligatorio(nombre_comercial, "El nombre comercial", 200)
    direccion_fiscal = _texto_obligatorio(direccion_fiscal, "La dirección fiscal", 300)
    try:
        nit = normalizar_nit(nit)
    except NITInvalido as error:
        raise ErrorNegocio(str(error)) from None
    if establecimiento_sat is None or establecimiento_sat < 1:
        raise ErrorNegocio("Indique el número de establecimiento registrado ante la SAT")
    if regimen_isr not in REGIMENES_ISR:
        raise ErrorNegocio("El régimen de ISR debe ser opcional simplificado o sobre utilidades")

    # Un cambio con fecha anterior o igual a la última versión reescribiría el perfil de
    # transacciones que ya lo usaron; solo se aceptan fechas posteriores.
    ultima = db.scalar(select(func.max(PerfilFiscal.vigente_desde)))
    if ultima is not None and vigente_desde <= ultima:
        raise ErrorNegocio(
            f"La vigencia debe ser posterior a la del perfil actual ({ultima:%d/%m/%Y}): "
            "un cambio no altera las fechas que ya cubre otra versión"
        )

    perfil = PerfilFiscal(
        vigente_desde=vigente_desde,
        razon_social=razon_social,
        nombre_comercial=nombre_comercial,
        nit=nit,
        direccion_fiscal=direccion_fiscal,
        establecimiento_sat=establecimiento_sat,
        regimen_isr=regimen_isr,
        agente_retencion_iva=agente_retencion_iva,
        agente_retencion_isr=agente_retencion_isr,
    )
    db.add(perfil)
    try:
        db.commit()
    except IntegrityError:
        # Dos cambios simultáneos con la misma fecha: la restricción UNIQUE decide.
        db.rollback()
        raise ErrorNegocio(
            f"Ya existe una versión del perfil vigente desde el {vigente_desde:%d/%m/%Y}"
        ) from None
    db.refresh(perfil)
    return perfil


def historial_perfil(db: Session) -> list[PerfilFiscal]:
    """Todas las versiones, de la más reciente a la más antigua."""
    return list(db.scalars(select(PerfilFiscal).order_by(PerfilFiscal.vigente_desde.desc())))


def perfil_vigente(db: Session, fecha: date) -> PerfilFiscal:
    """Perfil que aplica a un documento de esa fecha: la última versión vigente a esa fecha."""
    perfil = db.scalar(
        select(PerfilFiscal)
        .where(PerfilFiscal.vigente_desde <= fecha)
        .order_by(PerfilFiscal.vigente_desde.desc())
        .limit(1)
    )
    if perfil is None:
        raise ErrorNegocio(f"No hay perfil fiscal vigente al {fecha:%d/%m/%Y}", status=404)
    return perfil


def _decimal_positivo(texto: str, campo: str, decimales: int, maximo: Decimal) -> Decimal:
    try:
        valor = a_decimal(texto.strip())
    except (InvalidOperation, ValueError):
        raise ErrorNegocio(f"{campo} debe ser un número, por ejemplo 12") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio(f"{campo} debe ser mayor que cero")
    if -valor.as_tuple().exponent > decimales:
        raise ErrorNegocio(f"{campo} admite como máximo {decimales} decimales")
    if valor > maximo:
        raise ErrorNegocio(f"{campo} no puede ser mayor que {maximo}")
    return valor


def registrar_tasa(
    db: Session,
    tipo: str,
    vigente_desde: date,
    porcentaje: str | None = None,
    monto_limite: str | None = None,
) -> TasaImpositiva:
    """Agrega una tasa con su vigencia. El porcentaje llega como texto ("12") y se guarda como
    fracción exacta (0.12); las tasas anteriores no se modifican."""
    if tipo not in TIPOS_TASA:
        raise ErrorNegocio(f"Tipo de impuesto desconocido: {tipo}")
    tasa = limite = None
    if tipo in _LLEVA_PORCENTAJE:
        if not porcentaje:
            raise ErrorNegocio(f"Indique el porcentaje de {tipo}")
        tasa = _decimal_positivo(porcentaje, "El porcentaje", 4, Decimal(100)) / 100
    elif porcentaje:
        raise ErrorNegocio(f"{tipo} es un monto, no lleva porcentaje")
    if tipo in _LLEVA_MONTO:
        if not monto_limite:
            raise ErrorNegocio(f"Indique el monto límite de {tipo}")
        limite = _decimal_positivo(monto_limite, "El monto límite", 2, Decimal("1000000000000"))
    elif monto_limite:
        raise ErrorNegocio(f"{tipo} no lleva monto límite")

    ultima = db.scalar(select(func.max(TasaImpositiva.vigente_desde)).where(TasaImpositiva.tipo == tipo))
    if ultima is not None and vigente_desde <= ultima:
        raise ErrorNegocio(
            f"La vigencia debe ser posterior a la de la tasa actual de {tipo} ({ultima:%d/%m/%Y})"
        )

    registro = TasaImpositiva(tipo=tipo, tasa=tasa, monto_limite=limite, vigente_desde=vigente_desde)
    db.add(registro)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorNegocio(
            f"Ya existe una tasa de {tipo} vigente desde el {vigente_desde:%d/%m/%Y}"
        ) from None
    db.refresh(registro)
    return registro


def listar_tasas(db: Session) -> list[TasaImpositiva]:
    """Historial completo, por tipo y de la más reciente a la más antigua."""
    return list(
        db.scalars(select(TasaImpositiva).order_by(TasaImpositiva.tipo, TasaImpositiva.vigente_desde.desc()))
    )


def tasas_vigentes(db: Session, fecha: date) -> list[TasaImpositiva]:
    """La tasa de cada tipo vigente a esa fecha (una por tipo)."""
    return list(
        db.scalars(
            select(TasaImpositiva)
            .where(TasaImpositiva.vigente_desde <= fecha)
            .order_by(TasaImpositiva.tipo, TasaImpositiva.vigente_desde.desc())
            .ext(distinct_on(TasaImpositiva.tipo))
        )
    )


def tasa_vigente(db: Session, tipo: str, fecha: date) -> TasaImpositiva:
    """Lo que leen facturación, financiamiento y el cierre: la tasa de `tipo` a la fecha del documento."""
    registro = db.scalar(
        select(TasaImpositiva)
        .where(TasaImpositiva.tipo == tipo, TasaImpositiva.vigente_desde <= fecha)
        .order_by(TasaImpositiva.vigente_desde.desc())
        .limit(1)
    )
    if registro is None:
        raise ErrorNegocio(f"No hay tasa de {tipo} vigente al {fecha:%d/%m/%Y}", status=404)
    return registro

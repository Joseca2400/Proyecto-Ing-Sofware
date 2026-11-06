"""Reglas del módulo de compras (Sprint 1, equipo B).

HU-4.01 (incluido): alta y consulta de proveedores locales o del exterior, con nombre, rubro,
moneda habitual, días de crédito y datos bancarios; NIT de los locales validado con su dígito
verificador (`comun/nit.py`) y sin repetirse; identificación fiscal y país para los extranjeros.
HU-4.01 (diferido): régimen del proveedor local (general o pequeño contribuyente) y si se le
retiene IVA o ISR (criterio 2; lo usan HU-4.09 y HU-4.11).

Pendiente al mezclar HU-1.01 (perfil fiscal, equipo C):
- El perfil fiscal valida su NIT con el mismo `comun/nit.py`; no se duplica la regla.
- Las retenciones diferidas dependen de que la empresa sea agente de retención de IVA o ISR:
  al agregar el régimen y las retenciones del proveedor, leerlo del service de `configuracion`
  (nunca de sus models) y solo pedir los datos de retención cuando la empresa retiene.
- Rechazar como proveedor el NIT de la propia empresa (se compara contra el perfil vigente).

Pendiente al mezclar HU-1.09 y HU-1.11: exigir sesión y permiso del auxiliar contable, y que la
auditoría automática registre el alta.
"""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.comun.nit import NITInvalido, formatear_nit, normalizar_nit
from app.modulos.compras.models import Proveedor
from app.modulos.compras.schemas import ProveedorEntrada


def _nit_repetido(nit: str) -> ErrorNegocio:
    return ErrorNegocio(f"Ya existe un proveedor con el NIT {formatear_nit(nit)}", status=409)


def registrar_proveedor(db: Session, datos: ProveedorEntrada) -> Proveedor:
    if not datos.nombre:
        raise ErrorNegocio("El nombre del proveedor es obligatorio")

    nit = identificacion = pais = None
    if datos.tipo == "local":
        if datos.nit is None:
            raise ErrorNegocio("El NIT es obligatorio para un proveedor local")
        if datos.identificacion_fiscal or datos.pais:
            raise ErrorNegocio("Un proveedor local se identifica solo con su NIT")
        try:
            nit = normalizar_nit(datos.nit)
        except NITInvalido as error:
            raise ErrorNegocio(str(error)) from None
        if db.scalar(select(Proveedor.id).where(Proveedor.nit == nit)) is not None:
            raise _nit_repetido(nit)
    else:
        if datos.nit:
            raise ErrorNegocio("Un proveedor del exterior no lleva NIT; indique su identificación fiscal")
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
        escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        patron = f"%{escapado}%"
        nit_buscado = texto.replace("-", "").replace(" ", "").upper().lstrip("0")
        condiciones = [
            Proveedor.nombre.ilike(patron, escape="\\"),
            Proveedor.identificacion_fiscal.ilike(patron, escape="\\"),
        ]
        if nit_buscado:
            condiciones.append(Proveedor.nit == nit_buscado)
        consulta = consulta.where(or_(*condiciones))
    return list(db.scalars(consulta))


def obtener_proveedor(db: Session, proveedor_id: int) -> Proveedor:
    """Proveedor por id; lo usan la compra (HU-4.02), los gastos (HU-4.04) y las facturas (HU-4.09)."""
    proveedor = db.get(Proveedor, proveedor_id)
    if proveedor is None:
        raise ErrorNegocio(f"No existe el proveedor {proveedor_id}", status=404)
    return proveedor

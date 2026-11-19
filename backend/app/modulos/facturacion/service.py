"""Reglas del módulo de facturación (equipo C).

HU-6.01 (Sprint 1): alta y consulta de clientes individuales o empresas, identificados con NIT o
CUI, o con pasaporte y país si son extranjeros. El NIT se valida con su dígito verificador y no
se repiten clientes por NIT, CUI ni pasaporte. Un cliente puede marcarse exento de IVA (con su
motivo) para que la factura FEL (HU-6.02) no le aplique el IVA del perfil fiscal.

Diferido: consultar el nombre registrado en la SAT mediante el certificador (criterio 2) y el
estado de cuenta que integra alquileres, ventas y créditos (criterio 4, Sprint 3).
"""

import re

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.comun.nit import NITInvalido, formatear_nit, normalizar_nit
from app.modulos.facturacion.models import Cliente
from app.modulos.facturacion.schemas import ClienteEntrada

_CUI = re.compile(r"\d{13}")
_CORREO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _normalizar_cui(texto: str) -> str:
    """El CUI del DPI son 13 dígitos; se acepta con espacios o guiones ("2584 12345 0101")."""
    cui = re.sub(r"[\s-]", "", texto)
    if not _CUI.fullmatch(cui):
        raise ErrorNegocio("El CUI debe tener 13 dígitos, como aparece en el DPI")
    return cui


def _duplicado(db: Session, nit: str | None, cui: str | None, pasaporte: str | None, pais: str | None):
    if nit and db.scalar(select(Cliente.id).where(Cliente.nit == nit)) is not None:
        return ErrorNegocio(f"Ya existe un cliente con el NIT {formatear_nit(nit)}", status=409)
    if cui and db.scalar(select(Cliente.id).where(Cliente.cui == cui)) is not None:
        return ErrorNegocio(f"Ya existe un cliente con el CUI {cui}", status=409)
    if pasaporte:
        existe = db.scalar(select(Cliente.id).where(Cliente.pasaporte == pasaporte, Cliente.pais == pais))
        if existe is not None:
            return ErrorNegocio(f"Ya existe un cliente con el pasaporte {pasaporte} de {pais}", status=409)
    return None


def registrar_cliente(db: Session, datos: ClienteEntrada) -> Cliente:
    if not datos.nombre:
        raise ErrorNegocio("El nombre del cliente es obligatorio")

    nit = cui = pasaporte = pais = None
    if datos.nit is not None:
        try:
            nit = normalizar_nit(datos.nit)
        except NITInvalido as error:
            raise ErrorNegocio(str(error)) from None

    if datos.tipo == "empresa":
        if nit is None:
            raise ErrorNegocio("Una empresa se identifica con su NIT")
        if datos.cui or datos.pasaporte or datos.pais:
            raise ErrorNegocio("Una empresa se identifica solo con su NIT, sin CUI ni pasaporte")
    else:
        if datos.cui is not None:
            cui = _normalizar_cui(datos.cui)
        if (datos.pasaporte is None) != (datos.pais is None):
            raise ErrorNegocio("Un cliente extranjero requiere pasaporte y país")
        if datos.pasaporte is not None:
            if cui is not None:
                raise ErrorNegocio("Un cliente con CUI no necesita pasaporte")
            pais = datos.pais.upper()
            if len(pais) != 2 or not pais.isalpha() or not pais.isascii():
                raise ErrorNegocio("El país se indica con su código de dos letras, por ejemplo US")
            if pais == "GT":
                raise ErrorNegocio("Un cliente guatemalteco se identifica con su CUI o su NIT")
            pasaporte = datos.pasaporte.upper()
        if nit is None and cui is None and pasaporte is None:
            raise ErrorNegocio("Indique el NIT o el CUI del cliente, o su pasaporte y país si es extranjero")

    if datos.correo is not None and not _CORREO.fullmatch(datos.correo):
        raise ErrorNegocio("El correo no tiene una forma válida, por ejemplo nombre@dominio.com")

    if datos.exento_iva and datos.motivo_exencion is None:
        raise ErrorNegocio("Indique el motivo de la exención: diplomático, ONG, Estado u otro")
    if not datos.exento_iva and datos.motivo_exencion is not None:
        raise ErrorNegocio("El motivo de exención solo aplica a un cliente exento de IVA")

    if error := _duplicado(db, nit, cui, pasaporte, pais):
        raise error

    cliente = Cliente(
        tipo=datos.tipo,
        nombre=datos.nombre,
        nit=nit,
        cui=cui,
        pasaporte=pasaporte,
        pais=pais,
        direccion=datos.direccion,
        telefono=datos.telefono,
        correo=datos.correo.lower() if datos.correo else None,
        agente_retencion_iva=datos.agente_retencion_iva,
        agente_retencion_isr=datos.agente_retencion_isr,
        exento_iva=datos.exento_iva,
        motivo_exencion=datos.motivo_exencion,
    )
    db.add(cliente)
    try:
        db.commit()
    except IntegrityError:
        # Dos altas simultáneas con la misma identificación: las restricciones UNIQUE deciden.
        db.rollback()
        if error := _duplicado(db, nit, cui, pasaporte, pais):
            raise error from None
        raise
    db.refresh(cliente)
    return cliente


def listar_clientes(db: Session, tipo: str | None = None, buscar: str | None = None) -> list[Cliente]:
    """Consulta por tipo o texto (nombre, NIT, CUI o pasaporte), en orden alfabético."""
    consulta = select(Cliente).order_by(Cliente.nombre, Cliente.id)
    if tipo:
        consulta = consulta.where(Cliente.tipo == tipo)
    if buscar and buscar.strip():
        texto = buscar.strip()
        condiciones = [
            Cliente.nombre.ilike(_patron_contiene(texto), escape="\\"),
            Cliente.pasaporte.ilike(_patron_contiene(texto), escape="\\"),
        ]
        # NIT y CUI se guardan sin guion ni espacios: se busca igual (ver compras.listar_proveedores).
        limpio = re.sub(r"[\s-]", "", texto).upper()
        if limpio:
            condiciones.append(Cliente.cui.ilike(_patron_contiene(limpio), escape="\\"))
            nit_buscado = limpio.lstrip("0")
            if nit_buscado:
                condiciones.append(Cliente.nit.ilike(_patron_contiene(nit_buscado), escape="\\"))
        consulta = consulta.where(or_(*condiciones))
    return list(db.scalars(consulta))


def _patron_contiene(texto: str) -> str:
    """Patrón LIKE "contiene" con los comodines del usuario tratados como texto (escape `\\`)."""
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def obtener_cliente(db: Session, cliente_id: int) -> Cliente:
    """Cliente por id; lo usarán la factura FEL (HU-6.02), el contrato de alquiler y la venta."""
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise ErrorNegocio(f"No existe el cliente {cliente_id}", status=404)
    return cliente

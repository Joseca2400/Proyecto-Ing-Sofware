"""Reglas del módulo de facturación y cuentas por cobrar.

HU-6.01 (incluido): clientes individuales o empresas, identificados por NIT (con su verificador),
CUI o pasaporte con país; dirección, teléfono, correo y si son agentes de retención de IVA o ISR;
sin duplicados por identificación (también con altas simultáneas, por la restricción UNIQUE);
consulta por nombre o identificación.
HU-6.01 (diferido): consultar el nombre registrado en la SAT a través del certificador (criterio 2,
llega con FEL, HU-6.02); estado de cuenta integrado del cliente (criterio 4, Sprint 3). Del CUI
solo se exige que tenga 13 dígitos; su verificador no se calcula.

Para otros módulos: `obtener_cliente` y `listar_clientes` (contratos de alquiler, ventas, facturas).
"""

import re

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.comun.nit import NITInvalido, formatear_nit, normalizar_nit
from app.modulos.facturacion.models import Cliente
from app.modulos.facturacion.schemas import ClienteEntrada

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

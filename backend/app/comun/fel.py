"""Adaptador del certificador FEL (factura electrónica en línea de la SAT).

El módulo de facturación arma un `DocumentoFEL` y se lo entrega al certificador que devuelve
`certificador()`; recibe una `Certificacion` o la excepción `RechazoFEL` con el motivo. No depende
de ningún módulo ni de la base de datos.

Sprint 2 (parte 1): solo existe `CertificadorSimulado`, sin red. El certificador real y el PDF
certificado llegan en el Sprint 3 (parte 2): basta agregar una clase con el método `certificar`
y su nombre en `_CERTIFICADORES`, y elegirla con la variable de entorno `FEL_CERTIFICADOR`.
"""

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol

from app.comun import config
from app.comun.nit import es_nit_valido

CONSUMIDOR_FINAL = "CF"


@dataclass(frozen=True)
class LineaFEL:
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal  # con IVA, como lo expresa el documento FEL
    total: Decimal
    iva: Decimal


@dataclass(frozen=True)
class DocumentoFEL:
    """Factura lista para certificar. `referencia` identifica el intento en el sistema (id de la
    factura): el mismo intento da siempre la misma certificación."""

    referencia: str
    emisor_nit: str
    emisor_nombre: str
    receptor_id: str  # NIT normalizado, CUI, pasaporte o "CF"
    receptor_tipo: str  # nit, cui, pasaporte o cf
    receptor_nombre: str
    fecha: date
    moneda: str
    tipo_cambio: Decimal | None
    lineas: tuple[LineaFEL, ...]
    total: Decimal
    iva: Decimal


@dataclass(frozen=True)
class Certificacion:
    serie: str
    numero: str
    autorizacion: str  # UUID
    certificada_en: datetime
    xml: str


class RechazoFEL(Exception):
    """El certificador no aceptó el documento. El mensaje es el motivo, listo para mostrarse."""

    def __init__(self, motivo: str):
        super().__init__(motivo)
        self.motivo = motivo


class Certificador(Protocol):
    def certificar(self, documento: DocumentoFEL) -> Certificacion: ...


class CertificadorSimulado:
    """Certificador de prueba: determinista y sin red.

    La autorización es un UUID v5 calculado del emisor y la referencia; como en FEL, la serie son
    sus primeros 8 caracteres hexadecimales y el número, los 8 siguientes en decimal.

    Rechaza (para probar y demostrar el flujo de rechazo):
    - un receptor con NIT cuyo verificador no corresponde;
    - un documento sin líneas o con total menor o igual que cero;
    - un documento con alguna línea cuya descripción empiece con "RECHAZAR" (disparador explícito;
      el resto de la descripción, si lo hay, se usa como motivo).
    """

    _ESPACIO = uuid.UUID("6f1c2b4e-5d3a-4e8f-9a7b-0c1d2e3f4a5b")

    def certificar(self, documento: DocumentoFEL) -> Certificacion:
        if documento.receptor_tipo == "nit" and not es_nit_valido(documento.receptor_id):
            raise RechazoFEL(f"El NIT del receptor {documento.receptor_id} no es válido")
        if not documento.lineas or documento.total <= 0:
            raise RechazoFEL("El documento no tiene líneas o su total no es mayor que cero")
        for linea in documento.lineas:
            if linea.descripcion.upper().startswith("RECHAZAR"):
                motivo = linea.descripcion[len("RECHAZAR") :].strip(" :-")
                raise RechazoFEL(motivo or "Rechazo simulado por el certificador")

        autorizacion = uuid.uuid5(self._ESPACIO, f"{documento.emisor_nit}|{documento.referencia}")
        hexa = autorizacion.hex.upper()
        serie, numero = hexa[:8], str(int(hexa[8:16], 16))
        certificada_en = datetime.now(UTC)
        return Certificacion(
            serie=serie,
            numero=numero,
            autorizacion=str(autorizacion).upper(),
            certificada_en=certificada_en,
            xml=_xml(documento, serie, numero, str(autorizacion).upper(), certificada_en),
        )


def _xml(documento: DocumentoFEL, serie: str, numero: str, autorizacion: str, cuando: datetime) -> str:
    raiz = ET.Element("DTE", Tipo="FACT", Simulado="true")
    ET.SubElement(
        raiz,
        "Certificacion",
        Serie=serie,
        Numero=numero,
        NumeroAutorizacion=autorizacion,
        FechaHoraCertificacion=cuando.isoformat(timespec="seconds"),
    )
    generales = {"FechaEmision": documento.fecha.isoformat(), "CodigoMoneda": documento.moneda}
    if documento.tipo_cambio is not None:
        generales["TipoCambio"] = str(documento.tipo_cambio)
    ET.SubElement(raiz, "DatosGenerales", generales)
    ET.SubElement(raiz, "Emisor", NITEmisor=documento.emisor_nit, NombreEmisor=documento.emisor_nombre)
    ET.SubElement(
        raiz, "Receptor", IDReceptor=documento.receptor_id, NombreReceptor=documento.receptor_nombre
    )
    items = ET.SubElement(raiz, "Items")
    for numero_linea, linea in enumerate(documento.lineas, start=1):
        ET.SubElement(
            items,
            "Item",
            NumeroLinea=str(numero_linea),
            Descripcion=linea.descripcion,
            Cantidad=str(linea.cantidad),
            PrecioUnitario=str(linea.precio_unitario),
            Total=str(linea.total),
            IVA=str(linea.iva),
        )
    ET.SubElement(raiz, "Totales", GranTotal=str(documento.total), TotalIVA=str(documento.iva))
    return ET.tostring(raiz, encoding="unicode")


_CERTIFICADORES: dict[str, type] = {"simulado": CertificadorSimulado}


def certificador() -> Certificador:
    """El certificador configurado en `FEL_CERTIFICADOR` (por defecto, el simulado)."""
    clase = _CERTIFICADORES.get(config.FEL_CERTIFICADOR)
    if clase is None:
        raise RuntimeError(f"Certificador FEL desconocido: {config.FEL_CERTIFICADOR}")
    return clase()

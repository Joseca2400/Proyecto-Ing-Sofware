from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.seguridad.service import (
    AUXILIAR_CONTABLE,
    CONTADOR,
    GERENCIA,
    GERENTE_FINANCIERO,
    Usuario,
    requiere_rol,
    usuario_actual,
)
from app.modulos.unidades import service
from app.modulos.unidades.schemas import (
    AlertaFinVida,
    AltaFlotaEntrada,
    AltaFlotaSalida,
    CambioEstadoEntrada,
    CambioEstadoSalida,
    CandidataAltaFlota,
    Catalogos,
    DepreciacionTipoEntrada,
    DepreciacionTipoSalida,
    Estado,
    Etapa,
    EtapasImportacion,
    FinVidaUtil,
    ParametroDepreciacionEntrada,
    ParametroDepreciacionSalida,
    ReglaFinVidaEntrada,
    ReglaFinVidaSalida,
    UnidadEntrada,
    UnidadSalida,
    ValorEnLibros,
)

# HU-1.09: todas las rutas exigen sesión. El gerente financiero sigue las etapas de importación
# (HU-4.07), por eso también cambia el estado.
ALTA = requiere_rol(AUXILIAR_CONTABLE, CONTADOR)
CAMBIO_ESTADO = requiere_rol(AUXILIAR_CONTABLE, CONTADOR, GERENTE_FINANCIERO)
ETAPAS = requiere_rol(GERENTE_FINANCIERO, CONTADOR, GERENCIA)
# HU-3.01: solo el contador registra el alta en flota (la aprobación del auxiliar, Sprint 5).
CONTADOR_ = requiere_rol(CONTADOR)

router = APIRouter(prefix="/unidades", tags=["Unidades"], dependencies=[Depends(usuario_actual)])


@router.get("/catalogos", response_model=Catalogos)
def catalogos() -> Catalogos:
    return Catalogos(**service.catalogos())


@router.get("/etapas-importacion", response_model=EtapasImportacion)
def etapas_importacion(
    etapa: Etapa | None = None, _: Usuario = Depends(ETAPAS), db: Session = Depends(get_db)
) -> EtapasImportacion:
    """HU-4.07: unidades por etapa con los días en su etapa actual y su costo acumulado."""
    return EtapasImportacion(**service.etapas_importacion(db, etapa))


@router.get("/alta-flota/candidatas", response_model=list[CandidataAltaFlota])
def candidatas_alta(_: Usuario = Depends(ETAPAS), db: Session = Depends(get_db)) -> list[CandidataAltaFlota]:
    """HU-3.01: unidades listas con el costo de su hoja de costo y su cuadre con el mayor."""
    return [CandidataAltaFlota(**c) for c in service.candidatas_alta(db)]


@router.get("/depreciacion/tipos", response_model=list[DepreciacionTipoSalida])
def listar_depreciacion_tipos(db: Session = Depends(get_db)) -> list[DepreciacionTipoSalida]:
    """HU-3.02: valores de depreciación por defecto de cada tipo de vehículo."""
    return [DepreciacionTipoSalida.model_validate(t) for t in service.listar_depreciacion_tipos(db)]


@router.put("/depreciacion/tipos/{tipo_vehiculo}", response_model=DepreciacionTipoSalida)
def definir_depreciacion_tipo(
    tipo_vehiculo: str,
    datos: DepreciacionTipoEntrada,
    usuario: Usuario = Depends(CONTADOR_),
    db: Session = Depends(get_db),
) -> DepreciacionTipoSalida:
    tipo = service.definir_depreciacion_tipo(
        db,
        tipo_vehiculo,
        datos.vida_util_meses,
        datos.porcentaje_residual,
        datos.porcentaje_fiscal,
        usuario.id,
    )
    return DepreciacionTipoSalida.model_validate(tipo)


# HU-3.14: el gerente financiero, la gerencia y el contador ven la alerta; la regla la fijan el
# gerente financiero o el contador.
REGLA_FIN_VIDA = requiere_rol(GERENTE_FINANCIERO, CONTADOR)


@router.get("/fin-vida-util", response_model=FinVidaUtil)
def fin_vida_util(_: Usuario = Depends(ETAPAS), db: Session = Depends(get_db)) -> FinVidaUtil:
    """HU-3.14: unidades de la flota que alcanzaron o están por alcanzar el fin de su vida útil."""
    regla = service.regla_fin_vida(db)
    return FinVidaUtil(
        regla=ReglaFinVidaSalida.model_validate(regla) if regla else None,
        unidades=[AlertaFinVida(**a) for a in service.alertas_fin_vida(db)],
    )


@router.put("/fin-vida-util/regla", response_model=ReglaFinVidaSalida)
def definir_regla_fin_vida(
    datos: ReglaFinVidaEntrada, usuario: Usuario = Depends(REGLA_FIN_VIDA), db: Session = Depends(get_db)
) -> ReglaFinVidaSalida:
    regla = service.definir_regla_fin_vida(
        db, datos.kilometraje_limite, datos.meses_limite, datos.porcentaje_aviso, usuario.id
    )
    return ReglaFinVidaSalida.model_validate(regla)


@router.get("", response_model=list[UnidadSalida])
def listar_unidades(
    estado: Estado | None = None, buscar: str | None = None, db: Session = Depends(get_db)
) -> list[UnidadSalida]:
    return [UnidadSalida.model_validate(u) for u in service.listar_unidades(db, estado, buscar)]


@router.post("", response_model=UnidadSalida, status_code=201)
def registrar_unidad(
    datos: UnidadEntrada, usuario: Usuario = Depends(ALTA), db: Session = Depends(get_db)
) -> UnidadSalida:
    return UnidadSalida.model_validate(service.registrar_unidad(db, datos, usuario.id))


@router.get("/{vin}", response_model=UnidadSalida)
def consultar_unidad(vin: str, db: Session = Depends(get_db)) -> UnidadSalida:
    return UnidadSalida.model_validate(service.obtener_por_vin(db, vin))


@router.post("/{vin}/estado", response_model=UnidadSalida)
def cambiar_estado(
    vin: str,
    datos: CambioEstadoEntrada,
    usuario: Usuario = Depends(CAMBIO_ESTADO),
    db: Session = Depends(get_db),
) -> UnidadSalida:
    return UnidadSalida.model_validate(
        service.cambiar_estado(db, vin, datos.estado, datos.documento, usuario.id)
    )


@router.get("/{vin}/historial", response_model=list[CambioEstadoSalida])
def historial(vin: str, db: Session = Depends(get_db)) -> list[CambioEstadoSalida]:
    return [CambioEstadoSalida.model_validate(c) for c in service.historial(db, vin)]


@router.post("/{vin}/alta-flota", response_model=AltaFlotaSalida, status_code=201)
def dar_de_alta(
    vin: str, datos: AltaFlotaEntrada, usuario: Usuario = Depends(CONTADOR_), db: Session = Depends(get_db)
) -> AltaFlotaSalida:
    alta = service.dar_de_alta(
        db, vin, datos.fecha, usuario.id, datos.vida_util_meses, datos.valor_residual, datos.porcentaje_fiscal
    )
    return AltaFlotaSalida.model_validate(alta)


# ── HU-3.02: depreciación ─────────────────────────────────────────────────────


@router.get("/{vin}/parametros-depreciacion", response_model=list[ParametroDepreciacionSalida])
def parametros_depreciacion(vin: str, db: Session = Depends(get_db)) -> list[ParametroDepreciacionSalida]:
    return [ParametroDepreciacionSalida.model_validate(p) for p in service.parametros_depreciacion(db, vin)]


@router.post("/{vin}/parametros-depreciacion", response_model=ParametroDepreciacionSalida, status_code=201)
def cambiar_parametros(
    vin: str,
    datos: ParametroDepreciacionEntrada,
    usuario: Usuario = Depends(CONTADOR_),
    db: Session = Depends(get_db),
) -> ParametroDepreciacionSalida:
    version = service.cambiar_parametros(
        db,
        vin,
        datos.vigente_desde,
        datos.vida_util_meses,
        datos.valor_residual,
        datos.porcentaje_fiscal,
        usuario.id,
    )
    return ParametroDepreciacionSalida.model_validate(version)


@router.get("/{vin}/valor-libros", response_model=ValorEnLibros)
def valor_en_libros(vin: str, fecha: date | None = None, db: Session = Depends(get_db)) -> ValorEnLibros:
    """Depreciación acumulada y valor en libros, financiero y fiscal, a la fecha (hoy si no se indica)."""
    return ValorEnLibros(**service.valor_en_libros(db, vin, fecha or date.today()))

// Contrato de GET /api/v1/sistema/estado (backend/app/modulos/sistema/schemas.py).
export interface EstadoSistema {
  aplicacion: string;
  version: string;
  mensaje: string;
  base_datos: {
    conectada: boolean;
    motor: string | null;
    revision_esquema: string | null;
  };
}

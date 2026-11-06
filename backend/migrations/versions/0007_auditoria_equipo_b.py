"""HU-1.11: triggers de auditoría para las tablas del equipo B (HU-1.06, HU-1.07, HU-4.01, HU-4.09).

Igual que `d5f18a6e0c47` para `usuarios` y `cuentas`: cada trigger invoca
`public.registrar_cambio` con la lista explícita de columnas que se copian a la bitácora.
En `linea_factura_compra` se incluye `vin`, que sí es el VIN de la unidad. Sin sesión (las
rutas del equipo B aún no la exigen) el actor queda vacío y el registro se guarda igual.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-06
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = {
    "tipo_cambio": ("id", "fecha", "valor", "origen", "creado_en"),
    "transaccion_usd": (
        "id", "fecha", "monto_usd", "tipo_cambio_aplicado", "monto_gtq", "justificacion", "creado_en",
    ),
    "proveedor": (
        "id", "tipo", "nombre", "nit", "identificacion_fiscal", "pais", "regimen", "rubro",
        "moneda_habitual", "dias_credito", "banco", "cuenta_bancaria", "creado_en",
    ),
    "factura_compra": (
        "id", "proveedor_id", "serie", "numero", "autorizacion", "fecha", "regimen_proveedor",
        "total_base", "total_iva", "credito_fiscal", "total", "creado_en",
    ),
    "linea_factura_compra": (
        "id", "factura_id", "numero_linea", "descripcion", "cuenta", "linea_negocio", "vin",
        "base", "iva",
    ),
    "cuenta_por_pagar": (
        "id", "proveedor_id", "factura_compra_id", "fecha", "fecha_vencimiento", "moneda", "monto",
        "saldo", "creado_en",
    ),
}  # fmt: skip


def upgrade() -> None:
    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)


def downgrade() -> None:
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")

"""HU-1.05: unidades por VIN con su historial de estados; compras se liga a la unidad.

- `unidad` (VIN único, ficha mínima y estado vigente) y `cambio_estado_unidad` (historial), las
  dos con trigger de auditoría (HU-1.11) como en `0007`. En `unidad` se copia `vin`, así la
  bitácora queda filtrable por VIN; el historial se liga por `unidad_id`.
- `linea_factura_compra.vin` pasa a ser llave foránea a `unidad.vin`. Se crea `NOT VALID` para no
  fallar en bases de desarrollo con líneas capturadas antes de que existieran las unidades; las
  filas nuevas sí se revisan. Para validar las viejas, registrar sus unidades y ejecutar
  `ALTER TABLE linea_factura_compra VALIDATE CONSTRAINT fk_linea_factura_compra_vin_unidad`.
- Se quita `ck_linea_factura_compra_linea_negocio`: la lista de líneas de negocio es la de
  `configuracion` (HU-1.04) y la valida el service de compras; no se mantiene una segunda copia.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ESTADOS = "'en_transito', 'en_aduana', 'en_taller', 'lista', 'en_flota', 'en_venta', 'vendida', 'recuperada'"
LINEAS_NEGOCIO = "'alquiler', 'venta', 'taller', 'financiamiento', 'administracion'"

COLUMNAS = {
    "unidad": (
        "id", "vin", "marca", "linea", "modelo", "color", "tipo_vehiculo", "linea_negocio", "estado",
        "creado_en",
    ),
    "cambio_estado_unidad": (
        "id", "unidad_id", "estado_anterior", "estado_nuevo", "documento", "usuario_id", "fecha",
    ),
}  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "unidad",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vin", sa.String(17), nullable=False),
        sa.Column("marca", sa.String(50), nullable=False),
        sa.Column("linea", sa.String(50), nullable=False),
        sa.Column("modelo", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(30), nullable=False),
        sa.Column("tipo_vehiculo", sa.String(20), nullable=False),
        sa.Column("linea_negocio", sa.String(20), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vin", name="unidad_vin_key"),
        sa.CheckConstraint("vin ~ '^[A-HJ-NPR-Z0-9]{17}$'", name="ck_unidad_vin"),
        sa.CheckConstraint(f"estado IN ({ESTADOS})", name="ck_unidad_estado"),
        sa.CheckConstraint("modelo BETWEEN 1900 AND 2100", name="ck_unidad_modelo"),
    )
    op.create_index("ix_unidad_marca", "unidad", ["marca"])
    op.create_index("ix_unidad_estado", "unidad", ["estado"])

    op.create_table(
        "cambio_estado_unidad",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unidad_id", sa.Integer(), sa.ForeignKey("unidad.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estado_anterior", sa.String(20), nullable=True),
        sa.Column("estado_nuevo", sa.String(20), nullable=False),
        sa.Column("documento", sa.String(200), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(f"estado_nuevo IN ({ESTADOS})", name="ck_cambio_estado_unidad_nuevo"),
        sa.CheckConstraint(
            f"estado_anterior IS NULL OR (estado_anterior IN ({ESTADOS}) AND estado_anterior <> estado_nuevo)",
            name="ck_cambio_estado_unidad_anterior",
        ),
    )
    op.create_index("ix_cambio_estado_unidad_unidad_id", "cambio_estado_unidad", ["unidad_id"])

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    op.create_foreign_key(
        "fk_linea_factura_compra_vin_unidad",
        "linea_factura_compra",
        "unidad",
        ["vin"],
        ["vin"],
        postgresql_not_valid=True,
    )
    op.drop_constraint("ck_linea_factura_compra_linea_negocio", "linea_factura_compra", type_="check")


def downgrade() -> None:
    op.create_check_constraint(
        "ck_linea_factura_compra_linea_negocio",
        "linea_factura_compra",
        f"linea_negocio IN ({LINEAS_NEGOCIO})",
    )
    op.drop_constraint("fk_linea_factura_compra_vin_unidad", "linea_factura_compra", type_="foreignkey")
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
    op.drop_table("cambio_estado_unidad")
    op.drop_table("unidad")

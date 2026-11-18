"""HU-6.02: facturas FEL emitidas, sus líneas y su cuenta por cobrar (módulo de facturación).

- `factura`: intento de emisión (pendiente, certificada o rechazada) con los datos de certificación
  o el motivo del rechazo; ligada a su partida por llave foránea.
- `linea_factura`: descripción, cantidad, precio con IVA, base, IVA, línea de negocio y VIN.
- `cuenta_por_cobrar`: saldo del cliente que nace de la factura certificada.
- Reglas de contabilización del documento `factura`.
- Bitácora (HU-1.11) en las tablas nuevas; el XML de la factura no se copia a la bitácora.

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

REGLAS = (
    ("factura", "por_cobrar_gtq", "Cuenta por cobrar al cliente en quetzales", "1.1.02.01"),
    ("factura", "por_cobrar_usd", "Cuenta por cobrar al cliente en dólares", "1.1.02.02"),
    ("factura", "iva_debito", "IVA débito fiscal de la factura emitida", "2.1.02.01"),
    ("factura", "ingreso_alquiler", "Ingreso de una línea de alquiler", "4.1"),
    ("factura", "ingreso_venta", "Ingreso de una línea de venta de vehículos", "4.2"),
    ("factura", "ingreso_taller", "Ingreso de una línea de servicios de taller", "4.3"),
)

FACTURA = (
    "id", "cliente_id", "fecha", "moneda", "tipo_cambio", "origen_tipo", "origen_id", "dias_credito",
    "emisor_nit", "emisor_nombre", "receptor_id", "receptor_nombre", "base", "iva", "total", "total_gtq",
    "estado", "serie", "numero", "autorizacion", "certificada_en", "motivo_rechazo", "partida_id",
    "creado_por", "creado_en",
)  # fmt: skip
LINEA_FACTURA = (
    "id", "factura_id", "numero_linea", "descripcion", "cantidad", "precio_unitario", "total", "base",
    "iva", "linea_negocio", "vin",
)  # fmt: skip
CUENTA_POR_COBRAR = (
    "id", "factura_id", "cliente_id", "fecha", "fecha_vencimiento", "moneda", "monto", "saldo", "creado_en",
)  # fmt: skip
TABLAS = {"factura": FACTURA, "linea_factura": LINEA_FACTURA, "cuenta_por_cobrar": CUENTA_POR_COBRAR}


def upgrade() -> None:
    op.create_table(
        "factura",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("cliente.id"), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("tipo_cambio", sa.Numeric(18, 8), nullable=True),
        sa.Column("origen_tipo", sa.String(20), nullable=True),
        sa.Column("origen_id", sa.Integer(), nullable=True),
        sa.Column("dias_credito", sa.Integer(), nullable=False),
        sa.Column("emisor_nit", sa.String(13), nullable=False),
        sa.Column("emisor_nombre", sa.String(200), nullable=False),
        sa.Column("receptor_id", sa.String(30), nullable=False),
        sa.Column("receptor_nombre", sa.String(200), nullable=False),
        sa.Column("base", MONTO, nullable=False),
        sa.Column("iva", MONTO, nullable=False),
        sa.Column("total", MONTO, nullable=False),
        sa.Column("total_gtq", MONTO, nullable=False),
        sa.Column("estado", sa.String(12), nullable=False),
        sa.Column("serie", sa.String(20), nullable=True),
        sa.Column("numero", sa.String(20), nullable=True),
        sa.Column("autorizacion", sa.String(36), nullable=True),
        sa.Column("certificada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("xml", sa.Text(), nullable=True),
        sa.Column("motivo_rechazo", sa.String(500), nullable=True),
        sa.Column(
            "partida_id", sa.Integer(), sa.ForeignKey("partida.id", name="fk_factura_partida"), nullable=True
        ),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("partida_id", name="uq_factura_partida"),
        sa.CheckConstraint("estado IN ('pendiente', 'certificada', 'rechazada')", name="ck_factura_estado"),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_factura_moneda"),
        sa.CheckConstraint(
            "(moneda = 'USD' AND tipo_cambio > 0) OR (moneda = 'GTQ' AND tipo_cambio IS NULL)",
            name="ck_factura_tipo_cambio",
        ),
        sa.CheckConstraint("total > 0 AND total = base + iva", name="ck_factura_total"),
        sa.CheckConstraint("(origen_tipo IS NULL) = (origen_id IS NULL)", name="ck_factura_origen"),
        sa.CheckConstraint("partida_id IS NULL OR estado = 'certificada'", name="ck_factura_partida"),
    )
    op.create_index("ix_factura_cliente_id", "factura", ["cliente_id"])
    op.create_index("ix_factura_fecha", "factura", ["fecha"])
    op.create_table(
        "linea_factura",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("factura_id", sa.Integer(), sa.ForeignKey("factura.id"), nullable=False),
        sa.Column("numero_linea", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(300), nullable=False),
        sa.Column("cantidad", MONTO, nullable=False),
        sa.Column("precio_unitario", MONTO, nullable=False),
        sa.Column("total", MONTO, nullable=False),
        sa.Column("base", MONTO, nullable=False),
        sa.Column("iva", MONTO, nullable=False),
        sa.Column("linea_negocio", sa.String(20), nullable=False),
        sa.Column("vin", sa.String(17), nullable=True),
        sa.UniqueConstraint("factura_id", "numero_linea", name="uq_linea_factura_numero"),
        sa.CheckConstraint("cantidad > 0 AND precio_unitario > 0", name="ck_linea_factura_cantidad"),
        sa.CheckConstraint("total = base + iva", name="ck_linea_factura_total"),
    )
    op.create_index("ix_linea_factura_factura_id", "linea_factura", ["factura_id"])
    op.create_table(
        "cuenta_por_cobrar",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("factura_id", sa.Integer(), sa.ForeignKey("factura.id"), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("cliente.id"), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("saldo", MONTO, nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("factura_id", name="uq_cuenta_por_cobrar_factura"),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_cuenta_por_cobrar_moneda"),
        sa.CheckConstraint("monto > 0", name="ck_cuenta_por_cobrar_monto"),
        sa.CheckConstraint("saldo >= 0 AND saldo <= monto", name="ck_cuenta_por_cobrar_saldo"),
        sa.CheckConstraint("fecha_vencimiento >= fecha", name="ck_cuenta_por_cobrar_vencimiento"),
    )
    op.create_index("ix_cuenta_por_cobrar_cliente_id", "cuenta_por_cobrar", ["cliente_id"])
    op.create_index("ix_cuenta_por_cobrar_fecha_vencimiento", "cuenta_por_cobrar", ["fecha_vencimiento"])

    for tabla, columnas in TABLAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    reglas = sa.table(
        "regla_contabilizacion",
        sa.column("documento_tipo", sa.String),
        sa.column("concepto", sa.String),
        sa.column("descripcion", sa.String),
        sa.column("cuenta_codigo", sa.String),
    )
    op.bulk_insert(
        reglas,
        [
            {
                "documento_tipo": tipo,
                "concepto": concepto,
                "descripcion": descripcion,
                "cuenta_codigo": cuenta,
            }
            for tipo, concepto, descripcion, cuenta in REGLAS
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM regla_contabilizacion WHERE documento_tipo = 'factura'")
    for tabla in reversed(TABLAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
    op.drop_table("cuenta_por_cobrar")
    op.drop_table("linea_factura")
    op.drop_table("factura")

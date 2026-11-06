"""HU-2.01, HU-2.02 y HU-2.03: partidas de diario y sus líneas.

La base protege lo que el servicio promete: una partida solo pasa a contabilizada si cuadra y,
una vez contabilizada, ni ella ni sus líneas se modifican ni se borran (se revierten, HU-2.05).
También se audita (HU-1.11) con la lista explícita de columnas.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)
TIPO_CAMBIO = sa.Numeric(18, 8)

COLUMNAS = {
    "partida": (
        "id", "numero", "fecha", "concepto", "documento_soporte", "estado", "origen",
        "documento_tipo", "documento_id", "comentario", "creado_por", "contabilizada_por",
        "contabilizada_en",
    ),
    "linea_partida": (
        "id", "partida_id", "numero_linea", "cuenta_id", "debe", "haber", "moneda", "monto_usd",
        "tipo_cambio", "linea_negocio", "vin",
    ),
}  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "partida",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero", sa.Integer(), nullable=True, unique=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("concepto", sa.String(300), nullable=False),
        sa.Column("documento_soporte", sa.String(100), nullable=True),
        sa.Column("estado", sa.String(15), nullable=False),
        sa.Column("origen", sa.String(10), nullable=False),
        sa.Column("documento_tipo", sa.String(30), nullable=True),
        sa.Column("documento_id", sa.String(50), nullable=True),
        sa.Column("comentario", sa.String(300), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("contabilizada_por", sa.Integer(), nullable=True),
        sa.Column("contabilizada_en", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("documento_tipo", "documento_id", name="uq_partida_documento"),
        sa.CheckConstraint(
            "estado IN ('borrador', 'en_revision', 'contabilizada', 'devuelta')", name="ck_partida_estado"
        ),
        sa.CheckConstraint("origen IN ('manual', 'automatica')", name="ck_partida_origen"),
        sa.CheckConstraint("(estado = 'contabilizada') = (numero IS NOT NULL)", name="ck_partida_numero"),
        sa.CheckConstraint(
            "(origen = 'automatica') = (documento_tipo IS NOT NULL AND documento_id IS NOT NULL)",
            name="ck_partida_documento",
        ),
    )
    op.create_index("ix_partida_fecha", "partida", ["fecha"])
    op.create_index("ix_partida_estado", "partida", ["estado"])

    op.create_table(
        "linea_partida",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "partida_id", sa.Integer(), sa.ForeignKey("partida.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("numero_linea", sa.Integer(), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas.id"), nullable=False),
        sa.Column("debe", MONTO, nullable=False),
        sa.Column("haber", MONTO, nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("monto_usd", MONTO, nullable=True),
        sa.Column("tipo_cambio", TIPO_CAMBIO, nullable=True),
        sa.Column("linea_negocio", sa.String(20), nullable=True),
        sa.Column("vin", sa.String(17), nullable=True),
        sa.UniqueConstraint("partida_id", "numero_linea", name="uq_linea_partida_numero"),
        sa.CheckConstraint(
            "(debe > 0 AND haber = 0) OR (haber > 0 AND debe = 0)", name="ck_linea_partida_un_lado"
        ),
        sa.CheckConstraint(
            "(moneda = 'GTQ' AND monto_usd IS NULL AND tipo_cambio IS NULL)"
            " OR (moneda = 'USD' AND monto_usd > 0 AND tipo_cambio > 0)",
            name="ck_linea_partida_moneda",
        ),
        sa.CheckConstraint("vin IS NULL OR length(vin) = 17", name="ck_linea_partida_vin"),
    )
    op.create_index("ix_linea_partida_cuenta_id", "linea_partida", ["cuenta_id"])
    op.create_index("ix_linea_partida_vin", "linea_partida", ["vin"])

    op.execute("""
        CREATE FUNCTION public.proteger_partida() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            debe numeric;
            haber numeric;
        BEGIN
            IF TG_TABLE_NAME = 'partida' THEN
                IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.estado = 'contabilizada' THEN
                    RAISE EXCEPTION 'Una partida contabilizada no se modifica ni se borra';
                END IF;
                IF TG_OP = 'UPDATE' AND NEW.estado = 'contabilizada' THEN
                    SELECT coalesce(sum(l.debe), 0), coalesce(sum(l.haber), 0) INTO debe, haber
                    FROM linea_partida l WHERE l.partida_id = NEW.id;
                    IF debe <> haber OR debe = 0 THEN
                        RAISE EXCEPTION 'La partida % no cuadra: débitos %, créditos %', NEW.id, debe, haber;
                    END IF;
                END IF;
            ELSIF EXISTS (
                SELECT 1 FROM partida p
                WHERE p.id = coalesce(OLD.partida_id, NEW.partida_id) AND p.estado = 'contabilizada'
            ) THEN
                RAISE EXCEPTION 'Las líneas de una partida contabilizada no se modifican';
            END IF;
            RETURN coalesce(NEW, OLD);
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER proteger_partida BEFORE UPDATE OR DELETE ON partida
        FOR EACH ROW EXECUTE FUNCTION public.proteger_partida()
    """)
    op.execute("""
        CREATE TRIGGER proteger_linea_partida BEFORE INSERT OR UPDATE OR DELETE ON linea_partida
        FOR EACH ROW EXECUTE FUNCTION public.proteger_partida()
    """)

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)


def downgrade() -> None:
    op.drop_table("linea_partida")
    op.drop_table("partida")
    op.execute("DROP FUNCTION public.proteger_partida()")

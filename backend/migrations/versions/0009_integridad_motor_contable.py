"""HU-2.01 y HU-2.02: cerrar vías de alteración y serializar cambios de líneas.

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_linea_partida_moneda", "linea_partida")
    op.create_check_constraint(
        "ck_linea_partida_moneda",
        "linea_partida",
        "(moneda = 'GTQ' AND monto_usd IS NULL AND tipo_cambio IS NULL)"
        " OR (moneda = 'USD' AND monto_usd IS NOT NULL AND tipo_cambio IS NOT NULL"
        " AND monto_usd > 0 AND tipo_cambio > 0)",
    )
    op.execute("""
        CREATE OR REPLACE FUNCTION public.proteger_partida() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            debe numeric;
            haber numeric;
            origen_id integer;
            destino_id integer;
            cabecera record;
        BEGIN
            IF TG_TABLE_NAME = 'partida' THEN
                IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.estado = 'contabilizada' THEN
                    RAISE EXCEPTION 'Una partida contabilizada no se modifica ni se borra';
                END IF;
                IF TG_OP IN ('INSERT', 'UPDATE') AND NEW.estado = 'contabilizada' THEN
                    SELECT coalesce(sum(l.debe), 0), coalesce(sum(l.haber), 0) INTO debe, haber
                    FROM linea_partida l WHERE l.partida_id = NEW.id;
                    IF debe <> haber OR debe = 0 THEN
                        RAISE EXCEPTION 'La partida % no cuadra: débitos %, créditos %', NEW.id, debe, haber;
                    END IF;
                END IF;
            ELSE
                IF TG_OP IN ('UPDATE', 'DELETE') THEN
                    origen_id := OLD.partida_id;
                END IF;
                IF TG_OP IN ('INSERT', 'UPDATE') THEN
                    destino_id := NEW.partida_id;
                END IF;
                -- Un traslado debe comprobar ambas cabeceras. El candado compartido con
                -- la contabilización evita validar el estado y escribir con datos viejos.
                FOR cabecera IN
                    SELECT p.estado FROM partida p
                    WHERE p.id IN (origen_id, destino_id)
                    ORDER BY p.id FOR NO KEY UPDATE
                LOOP
                    IF cabecera.estado = 'contabilizada' THEN
                        RAISE EXCEPTION 'Las líneas de una partida contabilizada no se modifican';
                    END IF;
                END LOOP;
            END IF;
            RETURN coalesce(NEW, OLD);
        END;
        $$
    """)
    op.execute("DROP TRIGGER proteger_partida ON partida")
    op.execute("""
        CREATE TRIGGER proteger_partida BEFORE INSERT OR UPDATE OR DELETE ON partida
        FOR EACH ROW EXECUTE FUNCTION public.proteger_partida()
    """)


def downgrade() -> None:
    op.drop_constraint("ck_linea_partida_moneda", "linea_partida")
    op.create_check_constraint(
        "ck_linea_partida_moneda",
        "linea_partida",
        "(moneda = 'GTQ' AND monto_usd IS NULL AND tipo_cambio IS NULL)"
        " OR (moneda = 'USD' AND monto_usd > 0 AND tipo_cambio > 0)",
    )
    op.execute("DROP TRIGGER proteger_partida ON partida")
    op.execute("""
        CREATE TRIGGER proteger_partida BEFORE UPDATE OR DELETE ON partida
        FOR EACH ROW EXECUTE FUNCTION public.proteger_partida()
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION public.proteger_partida() RETURNS trigger
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

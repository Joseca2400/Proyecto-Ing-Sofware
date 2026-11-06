"""HU-1.11: bitácora transaccional para usuarios y cuentas, sin secretos.

Revision ID: d5f18a6e0c47
Revises: c0a7e41d9b32
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d5f18a6e0c47"
down_revision = "c0a7e41d9b32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bitacora",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("entidad", sa.String(100), nullable=False),
        sa.Column("registro_id", sa.String(100), nullable=False),
        sa.Column("accion", sa.String(20), nullable=False),
        sa.Column("vin", sa.String(17), nullable=True),
        sa.Column("anteriores", postgresql.JSONB(), nullable=True),
        sa.Column("nuevos", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_bitacora_usuario_id", "bitacora", ["usuario_id"])
    op.create_index("ix_bitacora_entidad", "bitacora", ["entidad"])
    op.create_index("ix_bitacora_vin", "bitacora", ["vin"])
    op.execute("""
        CREATE FUNCTION public.registrar_cambio() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            anteriores jsonb;
            nuevos jsonb;
            documento jsonb;
            vin_unidad text;
        BEGIN
            IF TG_OP = 'UPDATE' AND OLD IS NOT DISTINCT FROM NEW THEN
                RETURN NEW;
            END IF;
            -- Lista explícita de columnas permitidas por entidad: nunca copiar secretos.
            IF TG_OP <> 'INSERT' THEN
                SELECT jsonb_object_agg(clave, valor) INTO anteriores
                FROM jsonb_each(to_jsonb(OLD)) AS dato(clave, valor)
                WHERE clave = ANY(TG_ARGV);
            END IF;
            IF TG_OP <> 'DELETE' THEN
                SELECT jsonb_object_agg(clave, valor) INTO nuevos
                FROM jsonb_each(to_jsonb(NEW)) AS dato(clave, valor)
                WHERE clave = ANY(TG_ARGV);
            END IF;
            documento := coalesce(nuevos, anteriores);
            vin_unidad := upper(trim(documento ->> 'vin'));
            -- cuentas.vin contiene una política, no el VIN de un vehículo.
            IF vin_unidad !~ '^[A-HJ-NPR-Z0-9]{17}$' THEN
                vin_unidad := NULL;
            END IF;
            INSERT INTO public.bitacora
                (usuario_id, entidad, registro_id, accion, vin, anteriores, nuevos)
            VALUES (
                nullif(current_setting('app.usuario_id', true), '')::integer,
                TG_TABLE_NAME, documento ->> 'id',
                CASE TG_OP WHEN 'INSERT' THEN 'crear' WHEN 'UPDATE' THEN 'modificar' ELSE 'eliminar' END,
                vin_unidad, anteriores, nuevos
            );
            RETURN NULL;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER auditar_usuarios AFTER INSERT OR UPDATE OR DELETE ON usuarios
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio(
            'id', 'correo', 'nombre', 'rol', 'activo', 'creado_en'
        )
    """)
    op.execute("""
        CREATE TRIGGER auditar_cuentas AFTER INSERT OR UPDATE OR DELETE ON cuentas
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio(
            'id', 'codigo', 'nombre', 'tipo', 'naturaleza', 'nivel', 'padre_id',
            'es_detalle', 'monetaria_usd', 'linea_obligatoria', 'vin', 'linea_defecto'
        )
    """)
    op.execute("""
        CREATE FUNCTION public.proteger_bitacora() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'La bitácora no permite modificación ni borrado';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER bitacora_inmutable BEFORE UPDATE OR DELETE ON bitacora
        FOR EACH ROW EXECUTE FUNCTION public.proteger_bitacora()
    """)
    op.execute("""
        CREATE TRIGGER bitacora_sin_truncate BEFORE TRUNCATE ON bitacora
        FOR EACH STATEMENT EXECUTE FUNCTION public.proteger_bitacora()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_cuentas ON cuentas")
    op.execute("DROP TRIGGER auditar_usuarios ON usuarios")
    op.drop_table("bitacora")
    op.execute("DROP FUNCTION public.proteger_bitacora()")
    op.execute("DROP FUNCTION public.registrar_cambio()")

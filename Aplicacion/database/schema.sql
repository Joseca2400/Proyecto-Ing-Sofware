-- Esquema PostgreSQL del Sprint 0 / Sprint 1 (corte transversal: de la compra al alta en flota).
-- Equivale a los modelos de proyecto-vehiculos/backend/app/models.py (épicas 1 a 5).
-- Es idempotente: se puede ejecutar varias veces (npm run db:init).
-- Montos: NUMERIC(18,6), nunca FLOAT (acuerdo 2 de K1).

-- ============================================================ E1 · Seguridad

CREATE TABLE IF NOT EXISTS usuarios (
  id            SERIAL PRIMARY KEY,
  usuario       VARCHAR(40)  NOT NULL UNIQUE,
  nombre        VARCHAR(120) NOT NULL,
  rol           VARCHAR(30)  NOT NULL
                CHECK (rol IN ('AUXILIAR', 'CONTADOR', 'GERENTE_FINANCIERO', 'GERENCIA')),
  activo        BOOLEAN      NOT NULL DEFAULT TRUE,
  password_hash VARCHAR(200) NOT NULL          -- nunca se audita ni se expone
);

-- Se guarda el hash del token, no el token.
CREATE TABLE IF NOT EXISTS sesiones (
  id         SERIAL PRIMARY KEY,
  usuario_id INTEGER     NOT NULL REFERENCES usuarios (id),
  token_hash CHAR(64)    NOT NULL UNIQUE,
  creada_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
  expira_en  TIMESTAMPTZ NOT NULL,
  cerrada    BOOLEAN     NOT NULL DEFAULT FALSE
);

-- HU-1.11: registro inmutable, alimentado por triggers (ver más abajo).
CREATE TABLE IF NOT EXISTS bitacora (
  id                 SERIAL PRIMARY KEY,
  fecha              TIMESTAMPTZ NOT NULL DEFAULT now(),
  usuario            VARCHAR(40) NOT NULL,
  accion             VARCHAR(10) NOT NULL,       -- INSERT / UPDATE / DELETE
  entidad            VARCHAR(40) NOT NULL,
  entidad_id         INTEGER,
  vin                VARCHAR(17),
  valores_anteriores JSONB,
  valores_nuevos     JSONB
);
CREATE INDEX IF NOT EXISTS ix_bitacora_vin ON bitacora (vin);
CREATE INDEX IF NOT EXISTS ix_bitacora_entidad ON bitacora (entidad, entidad_id);

-- ============================================================ E1 · Catálogo y multimoneda

-- HU-1.02 y HU-1.04: cuenta contable y su exigencia de VIN.
CREATE TABLE IF NOT EXISTS cuentas (
  id             SERIAL PRIMARY KEY,
  codigo         VARCHAR(20)  NOT NULL UNIQUE,
  nombre         VARCHAR(120) NOT NULL,
  tipo           VARCHAR(20)  NOT NULL
                 CHECK (tipo IN ('ACTIVO', 'PASIVO', 'PATRIMONIO', 'INGRESO', 'COSTO', 'GASTO')),
  naturaleza     VARCHAR(10)  NOT NULL CHECK (naturaleza IN ('DEUDORA', 'ACREEDORA')),
  es_detalle     BOOLEAN      NOT NULL DEFAULT TRUE,
  monetaria_usd  BOOLEAN      NOT NULL DEFAULT FALSE,
  exige_vin      VARCHAR(15)  NOT NULL DEFAULT 'NO_APLICA'
                 CHECK (exige_vin IN ('OBLIGATORIO', 'OPCIONAL', 'NO_APLICA')),
  linea_defecto  VARCHAR(20),
  activa         BOOLEAN      NOT NULL DEFAULT TRUE
);

-- HU-1.06: tipo de cambio de referencia por fecha (Q por USD). Siempre positivo.
CREATE TABLE IF NOT EXISTS tipos_cambio (
  id             SERIAL PRIMARY KEY,
  fecha          DATE          NOT NULL UNIQUE,
  valor          NUMERIC(18,6) NOT NULL CHECK (valor > 0),
  origen         VARCHAR(15)   NOT NULL DEFAULT 'MANUAL',
  registrado_por VARCHAR(40)   NOT NULL
);

-- ============================================================ E1 · Unidades (el VIN es el hilo conductor)

CREATE TABLE IF NOT EXISTS unidades (
  id               SERIAL PRIMARY KEY,
  vin              VARCHAR(17) NOT NULL UNIQUE CHECK (vin ~ '^[A-HJ-NPR-Z0-9]{17}$'),
  marca            VARCHAR(40) NOT NULL,
  linea            VARCHAR(40) NOT NULL,
  modelo_anio      INTEGER     NOT NULL,
  color            VARCHAR(30),
  tipo_vehiculo    VARCHAR(30),
  placa            VARCHAR(15),
  estado           VARCHAR(20) NOT NULL
                   CHECK (estado IN ('EN_TRANSITO', 'EN_ADUANA', 'EN_TALLER', 'LISTA', 'EN_FLOTA',
                                     'EN_VENTA', 'VENDIDA', 'RECUPERADA')),
  kilometraje      INTEGER     NOT NULL DEFAULT 0,
  fecha_alta_flota DATE,
  costo_alta       NUMERIC(18,6),
  vida_util_meses  INTEGER,
  valor_residual   NUMERIC(18,6)
);

-- HU-4.07: historial de etapas de la unidad.
CREATE TABLE IF NOT EXISTS historial_estados (
  id              SERIAL PRIMARY KEY,
  unidad_id       INTEGER     NOT NULL REFERENCES unidades (id) ON DELETE CASCADE,
  estado_anterior VARCHAR(20),
  estado_nuevo    VARCHAR(20) NOT NULL,
  fecha           TIMESTAMPTZ NOT NULL DEFAULT now(),
  usuario         VARCHAR(40) NOT NULL,
  documento       VARCHAR(60) NOT NULL
);

-- ============================================================ E2 · Contabilidad

CREATE TABLE IF NOT EXISTS partidas (
  id                  SERIAL PRIMARY KEY,
  numero              INTEGER UNIQUE,                    -- correlativo al contabilizar
  fecha               DATE         NOT NULL,
  concepto            VARCHAR(250) NOT NULL,
  estado              VARCHAR(20)  NOT NULL DEFAULT 'BORRADOR'
                      CHECK (estado IN ('BORRADOR', 'EN_REVISION', 'CONTABILIZADA', 'DEVUELTA')),
  automatica          BOOLEAN      NOT NULL DEFAULT FALSE,
  origen_tipo         VARCHAR(30),
  origen_id           INTEGER,
  registrada_por      VARCHAR(40)  NOT NULL,
  contabilizada_por   VARCHAR(40),
  comentario_revision TEXT,
  creada_en           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lineas_partida (
  id             SERIAL PRIMARY KEY,
  partida_id     INTEGER       NOT NULL REFERENCES partidas (id) ON DELETE CASCADE,
  cuenta_id      INTEGER       NOT NULL REFERENCES cuentas (id),
  debe           NUMERIC(18,6) NOT NULL DEFAULT 0 CHECK (debe >= 0),   -- en quetzales
  haber          NUMERIC(18,6) NOT NULL DEFAULT 0 CHECK (haber >= 0),  -- en quetzales
  moneda         CHAR(3)       NOT NULL DEFAULT 'GTQ' CHECK (moneda IN ('GTQ', 'USD')),
  monto_original NUMERIC(18,6),                                        -- en USD si aplica
  tipo_cambio    NUMERIC(18,6) CHECK (tipo_cambio IS NULL OR tipo_cambio > 0),
  linea_negocio  VARCHAR(20)   NOT NULL,
  unidad_id      INTEGER REFERENCES unidades (id),
  detalle        VARCHAR(120)
);

-- ============================================================ E4 · Proveedores y compras

CREATE TABLE IF NOT EXISTS proveedores (
  id     SERIAL PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  tipo   VARCHAR(10)  NOT NULL CHECK (tipo IN ('LOCAL', 'EXTERIOR')),
  nit    VARCHAR(20) UNIQUE,
  pais   VARCHAR(40)  NOT NULL DEFAULT 'Guatemala',
  rubro  VARCHAR(30)  NOT NULL,
  moneda CHAR(3)      NOT NULL CHECK (moneda IN ('GTQ', 'USD'))
);

CREATE TABLE IF NOT EXISTS documentos_por_pagar (
  id           SERIAL PRIMARY KEY,
  proveedor_id INTEGER       NOT NULL REFERENCES proveedores (id),
  tipo         VARCHAR(30)   NOT NULL CHECK (tipo IN ('COMPRA_UNIDAD', 'GASTO_IMPORTACION')),
  referencia   VARCHAR(60),
  fecha        DATE          NOT NULL,
  moneda       CHAR(3)       NOT NULL CHECK (moneda IN ('GTQ', 'USD')),
  monto        NUMERIC(18,6) NOT NULL,
  saldo        NUMERIC(18,6) NOT NULL,
  tipo_cambio  NUMERIC(18,6) CHECK (tipo_cambio IS NULL OR tipo_cambio > 0),
  unidad_id    INTEGER REFERENCES unidades (id),
  partida_id   INTEGER REFERENCES partidas (id)
);

CREATE TABLE IF NOT EXISTS gastos_importacion (
  id           SERIAL PRIMARY KEY,
  unidad_id    INTEGER     NOT NULL REFERENCES unidades (id),
  concepto     VARCHAR(30) NOT NULL,
  documento_id INTEGER     NOT NULL REFERENCES documentos_por_pagar (id)
);

-- ============================================================ E5 · Taller

CREATE TABLE IF NOT EXISTS ordenes_trabajo (
  id                SERIAL PRIMARY KEY,
  unidad_id         INTEGER     NOT NULL REFERENCES unidades (id),
  tipo              VARCHAR(30) NOT NULL CHECK (tipo IN ('REACONDICIONAMIENTO', 'MANTENIMIENTO')),
  descripcion       TEXT        NOT NULL,
  responsable       VARCHAR(80) NOT NULL,
  kilometraje       INTEGER     NOT NULL DEFAULT 0,
  fecha_apertura    DATE        NOT NULL,
  fecha_cierre      DATE,
  estado            VARCHAR(10) NOT NULL DEFAULT 'ABIERTA' CHECK (estado IN ('ABIERTA', 'CERRADA')),
  justificacion_cero TEXT,
  partida_id        INTEGER REFERENCES partidas (id)
);

CREATE TABLE IF NOT EXISTS mano_obra (
  id          SERIAL PRIMARY KEY,
  orden_id    INTEGER       NOT NULL REFERENCES ordenes_trabajo (id) ON DELETE CASCADE,
  mecanico    VARCHAR(80)   NOT NULL,
  fecha       DATE          NOT NULL,
  horas       NUMERIC(18,6) NOT NULL CHECK (horas > 0),
  tarifa      NUMERIC(18,6) NOT NULL,
  costo       NUMERIC(18,6) NOT NULL,
  descripcion VARCHAR(200)  NOT NULL
);

-- ============================================================ Auditoría automática (HU-1.11)
-- Capa de persistencia: registra actor, valores anteriores y nuevos de cada cambio, sin tocar
-- el código de la aplicación. El actor llega por `conTransaccion` (src/config/db.js).
-- Nunca guarda password_hash. La bitácora no admite UPDATE ni DELETE.

CREATE OR REPLACE FUNCTION auditar() RETURNS trigger AS $$
DECLARE
  anterior jsonb;
  nuevo    jsonb;
BEGIN
  IF TG_OP <> 'INSERT' THEN anterior := to_jsonb(OLD) - 'password_hash'; END IF;
  IF TG_OP <> 'DELETE' THEN nuevo    := to_jsonb(NEW) - 'password_hash'; END IF;
  IF TG_OP = 'UPDATE' AND anterior = nuevo THEN RETURN NEW; END IF;

  INSERT INTO bitacora (usuario, accion, entidad, entidad_id, vin, valores_anteriores, valores_nuevos)
  VALUES (
    COALESCE(NULLIF(current_setting('app.usuario', true), ''), 'sistema'),
    TG_OP,
    TG_TABLE_NAME,
    COALESCE((nuevo ->> 'id')::int, (anterior ->> 'id')::int),
    COALESCE(nuevo ->> 'vin', anterior ->> 'vin'),
    anterior,
    nuevo
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION bitacora_inmutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'La bitácora no se puede modificar ni borrar';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_bitacora_inmutable ON bitacora;
CREATE TRIGGER tg_bitacora_inmutable BEFORE UPDATE OR DELETE ON bitacora
  FOR EACH ROW EXECUTE FUNCTION bitacora_inmutable();

DO $$
DECLARE tabla text;
BEGIN
  FOREACH tabla IN ARRAY ARRAY['usuarios', 'cuentas', 'tipos_cambio', 'unidades', 'proveedores',
                               'partidas', 'ordenes_trabajo', 'mano_obra']
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS tg_auditar ON %I', tabla);
    EXECUTE format('CREATE TRIGGER tg_auditar AFTER INSERT OR UPDATE OR DELETE ON %I
                    FOR EACH ROW EXECUTE FUNCTION auditar()', tabla);
  END LOOP;
END $$;

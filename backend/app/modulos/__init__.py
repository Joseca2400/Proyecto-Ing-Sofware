"""Un paquete por módulo de negocio. Cada uno tiene router, schemas, service y models.

Regla de dependencia: un módulo solo importa el `service` de otro módulo, nunca sus `models`.
"""

from app.modulos.seguridad import models as _seguridad  # noqa: F401,E402

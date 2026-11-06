"""Un paquete por módulo de negocio. Cada uno tiene router, schemas, service y models.

Regla de dependencia: un módulo solo importa el `service` de otro módulo, nunca sus `models`.
"""

from app.comun.auditoria import RegistroBitacora as _bitacora  # noqa: F401,E402
from app.modulos.compras import models as _compras  # noqa: F401,E402
from app.modulos.configuracion import models as _configuracion  # noqa: F401,E402
from app.modulos.seguridad import models as _seguridad  # noqa: F401,E402

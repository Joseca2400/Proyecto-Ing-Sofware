# Épica 1. Configuración, multimoneda y seguridad

Prioridad de la épica: 1 · MoSCoW: **Must**
Objetivo: dejar la base para contabilizar por línea de negocio, por unidad y en dos monedas, con funciones separadas.
Criterio de éxito de la épica: toda transacción se clasifica por cuenta, línea y unidad; la que se hace en USD guarda el monto original y el tipo de cambio; quien registra no aprueba.

---

### HU-1.01 Registrar el perfil fiscal de la empresa

**Como** contador, **quiero** registrar los datos de la empresa y su perfil fiscal, **para que** los documentos, libros y cálculos de impuestos usen la información correcta.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Dado que configuro la empresa, cuando guardo, entonces el sistema exige razón social, nombre comercial, NIT, dirección fiscal y establecimiento ante la SAT.
2. El NIT se valida con el dígito verificador antes de guardarse.
3. Puedo indicar el régimen de ISR (sobre utilidades u opcional simplificado), si la empresa es agente de retención de IVA y si es agente de retención de ISR.
4. Cada cambio del perfil fiscal guarda una fecha de vigencia; las transacciones anteriores a esa fecha conservan el perfil que tenían.
5. Solo el contador y el gerente financiero pueden modificar el perfil fiscal.

**Pendiente:** régimen de ISR exacto, calidad de agente de retención y si existe una o dos sociedades (preguntas 2 y 3 de las épicas).

---

### HU-1.02 Mantener el catálogo de cuentas

**Como** contador, **quiero** crear, editar e inactivar cuentas contables en una estructura jerárquica, **para** tener un catálogo ordenado que sirva a todas las líneas de negocio.

Prioridad: Must · Depende de: HU-1.01

**Criterios de aceptación**
1. Cada cuenta tiene código, nombre, tipo (activo, pasivo, patrimonio, ingreso, costo, gasto), naturaleza (deudora o acreedora) y nivel.
2. Solo las cuentas de detalle reciben movimientos; las de agrupación suman a sus hijas.
3. Puedo marcar si la cuenta es monetaria en USD (sujeta a revaluación) o en quetzales.
4. Una cuenta con movimientos no se puede eliminar, solo inactivar; una cuenta inactiva no acepta movimientos nuevos.
5. El código de cuenta es único y respeta la máscara de niveles configurada.

---

### HU-1.03 Importar el catálogo de cuentas existente

**Como** contador, **quiero** importar el catálogo actual desde una hoja de cálculo, **para** conservar o depurar lo que ya existe sin capturarlo cuenta por cuenta.

Prioridad: Should · Depende de: HU-1.02

**Criterios de aceptación**
1. El sistema ofrece una plantilla descargable con las columnas requeridas.
2. Antes de importar, el sistema muestra los errores por fila (códigos duplicados, padres inexistentes, tipos inválidos) y no carga nada si hay errores.
3. Puedo ver una vista previa de la jerarquía resultante y confirmar o cancelar la carga.
4. La importación queda registrada en la bitácora con usuario, fecha y archivo.

**Pendiente:** decidir si se conserva, depura o rediseña el catálogo actual.

---

### HU-1.04 Configurar las dimensiones analíticas

**Como** contador, **quiero** que cada movimiento lleve línea de negocio y, cuando aplique, unidad (VIN), **para** obtener resultados por línea y por vehículo.

Prioridad: Must · Depende de: HU-1.02

**Criterios de aceptación**
1. Las líneas de negocio disponibles son: alquiler, venta, taller y financiamiento, más una línea "administración" para gastos comunes. No existe dimensión de sucursal.
2. En cada cuenta de detalle puedo definir si la línea de negocio es obligatoria y si la unidad (VIN) es obligatoria, opcional o no aplica.
3. Dado que una cuenta exige unidad, cuando registro un movimiento sin VIN, entonces el sistema no permite guardar la partida.
4. Puedo definir una línea por defecto por cuenta para agilizar el registro.

**Pendiente:** confirmar si los gastos comunes se distribuyen entre líneas al cierre y con qué criterio.

---

### HU-1.05 Registrar y validar unidades por VIN

**Como** auxiliar contable, **quiero** que cada vehículo exista como unidad identificada por su VIN, **para** ligar a ella cualquier costo, ingreso o documento.

Prioridad: Must · Depende de: HU-1.04

**Criterios de aceptación**
1. El VIN es único en el sistema, tiene 17 caracteres y se valida con el dígito verificador de la posición 9 (norma de EE. UU.).
2. La unidad guarda marca, línea, modelo (año), color, tipo de vehículo y, cuando exista, placa y número de motor.
3. La unidad tiene un estado único a la vez: en tránsito, en aduana, en taller, lista, en flota, en venta, vendida o recuperada.
4. Cada cambio de estado guarda fecha, usuario y documento que lo originó, y se puede consultar el historial completo.
5. Desde la ficha de la unidad puedo ver todos los movimientos contables ligados a su VIN.

---

### HU-1.06 Cargar el tipo de cambio de referencia del Banguat

**Como** contador, **quiero** que el sistema tenga el tipo de cambio de referencia del Banguat para cada fecha, **para** convertir las transacciones en USD de forma uniforme.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. El sistema obtiene el tipo de cambio diario desde el servicio del Banguat; si no está disponible, permite cargarlo de forma manual.
2. Cada tipo de cambio guarda fecha, valor y origen (automático o manual).
3. Dado que no existe tipo de cambio para la fecha de una transacción en USD, cuando intento registrarla, entonces el sistema me avisa y no la guarda hasta que el tipo de cambio exista.
4. Un tipo de cambio usado en partidas contabilizadas no se puede modificar; corregirlo requiere aprobación del gerente financiero y queda en bitácora.

---

### HU-1.07 Registrar transacciones en dólares

**Como** auxiliar contable, **quiero** registrar documentos en USD indicando el monto original, **para que** el sistema calcule el equivalente en quetzales y conserve ambos valores.

Prioridad: Must · Depende de: HU-1.06

**Criterios de aceptación**
1. La moneda funcional es el quetzal; toda partida cuadra en quetzales.
2. Cada línea en USD guarda monto original, tipo de cambio aplicado y monto en quetzales.
3. Por defecto se aplica el tipo de cambio del Banguat de la fecha del documento.
4. Si el banco aplicó otro tipo de cambio (por ejemplo, en una compra de divisas), puedo indicarlo con justificación; el cambio queda en bitácora.
5. Los reportes permiten ver saldos de las cuentas en USD en su moneda original y en quetzales.

---

### HU-1.08 Configurar cuentas bancarias en quetzales y dólares

**Como** contador, **quiero** registrar las cuentas bancarias de la empresa con su moneda, **para** controlar pagos, cobros y conciliaciones por cuenta.

Prioridad: Must · Depende de: HU-1.02, HU-1.07

**Criterios de aceptación**
1. Cada cuenta bancaria tiene banco, número, tipo, moneda (GTQ o USD) y la cuenta contable a la que se liga.
2. Una cuenta bancaria en USD solo se puede ligar a una cuenta contable marcada como monetaria en USD.
3. Puedo configurar la numeración de cheques por cuenta.
4. Una cuenta bancaria con movimientos no se puede eliminar, solo inactivar.

---

### HU-1.09 Administrar usuarios y roles

**Como** gerente financiero, **quiero** crear usuarios y asignarles un rol, **para que** cada persona solo haga lo que le corresponde.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Existen los roles: auxiliar contable (registra), contador (revisa, contabiliza y cierra), gerente financiero (aprueba pagos, ajustes, descuentos, créditos y reapertura de períodos) y gerencia (solo consulta reportes).
2. Puedo dar de alta, suspender y dar de baja usuarios; un usuario dado de baja no puede iniciar sesión, pero su historial se conserva.
3. El inicio de sesión exige contraseña con reglas mínimas de complejidad y bloquea la cuenta tras varios intentos fallidos.
4. La sesión se cierra tras un tiempo de inactividad configurable.
5. El rol gerencia no ve pantallas de registro, solo reportes y tableros.

**Pendiente:** quién registra la operación (contratos, órdenes de taller, ventas); puede requerir un rol operativo adicional (pregunta 1 de las épicas).

---

### HU-1.10 Separar funciones de registro y aprobación

**Como** gerente financiero, **quiero** que quien registra una transacción no pueda aprobarla, **para** cumplir con el control interno.

Prioridad: Must · Depende de: HU-1.09

**Criterios de aceptación**
1. Dado que un usuario registró un documento, cuando ese mismo usuario intenta aprobarlo, entonces el sistema lo impide aunque su rol tenga permiso de aprobación.
2. Puedo configurar qué documentos requieren aprobación y los montos a partir de los cuales la aprobación pasa al gerente financiero.
3. Cada aprobación o rechazo guarda usuario, fecha y comentario.
4. Un documento rechazado vuelve a borrador con el motivo visible para quien lo registró.

---

### HU-1.11 Consultar la bitácora de cambios

**Como** contador, **quiero** consultar quién creó, modificó, aprobó o anuló cada registro, **para** tener trazabilidad ante auditorías.

Prioridad: Must · Depende de: HU-1.09

**Criterios de aceptación**
1. La bitácora registra usuario, fecha y hora, acción, registro afectado y valores anteriores y nuevos.
2. Puedo filtrar la bitácora por usuario, fecha, tipo de documento y VIN.
3. Ningún usuario, incluido el administrador, puede editar ni borrar la bitácora.
4. La bitácora se puede exportar a Excel.

---

### HU-1.12 Respaldar y restaurar la información

**Como** gerente financiero, **quiero** respaldos automáticos y verificables, **para** no perder la información contable.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. El sistema hace un respaldo diario automático y guarda varias copias según una política de retención configurable.
2. Los respaldos se guardan cifrados y en una ubicación distinta del servidor principal.
3. Puedo consultar el historial de respaldos con su estado (exitoso o fallido) y recibo una alerta si un respaldo falla.
4. Existe un procedimiento documentado de restauración, probado al menos una vez antes del arranque.

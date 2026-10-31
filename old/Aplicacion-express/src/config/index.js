// Configuración tomada de variables de entorno (.env en desarrollo).
require('dotenv').config({ quiet: true });

module.exports = {
  puerto: Number(process.env.PORT || 3000),
  databaseUrl: process.env.DATABASE_URL || 'postgres://postgres@localhost:5432/kilometro_cero',
  // Cuentas sembradas: solo ambiente de pruebas (HU-1.09).
  passwordInicial: process.env.PASSWORD_INICIAL || 'Demo2026!',
  horasSesion: Number(process.env.HORAS_SESION || 8),
};

const express = require('express');
const cors = require('cors');
const path = require('path');
const { noEncontrada, manejarErrores } = require('./middlewares/errores');

const app = express();

app.use(cors());
app.use(express.json());

// Front estático: login (index.html), home, taller...
app.use(express.static(path.join(__dirname, 'public')));

app.get('/health', (_req, res) => res.json({ status: 'ok' }));

// API versionada, mismo prefijo que la API de referencia.
app.use('/api/v1', require('./routes'));
app.use('/api', noEncontrada);

app.use(manejarErrores);

module.exports = app;

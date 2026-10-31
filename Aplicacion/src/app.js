const express = require('express');
const path = require('path');
const app = express();

// Middleware para leer JSON en las peticiones
app.use(express.json());

// Servir la carpeta 'public' como archivos estáticos
app.use(express.static(path.join(__dirname, 'public')));

// Ruta de ejemplo para el login (Backend)
app.post('/api/login', (req, res) => {
    const { email, password } = req.body;

    // Aquí después conectarás con PostgreSQL para validar el usuario
    if (email === "admin@admin.com" && password === "1234") {
        res.json({ success: true, message: "Autenticación exitosa" });
    } else {
        res.status(401).json({ success: false, message: "Credenciales inválidas" });
    }
});

module.exports = app;
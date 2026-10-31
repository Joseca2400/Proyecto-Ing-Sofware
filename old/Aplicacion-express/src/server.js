const config = require('./config');
const app = require('./app');

app.listen(config.puerto, () => {
  console.log(`Kilómetro Cero escuchando en http://localhost:${config.puerto}`);
});

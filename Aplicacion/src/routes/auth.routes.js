const { Router } = require('express');
const auth = require('../controllers/auth.controller');
const { sesionActual } = require('../middlewares/auth');

const router = Router();

router.post('/auth/login', auth.login);
router.post('/auth/logout', sesionActual, auth.logout);
router.get('/yo', sesionActual, auth.yo);

module.exports = router;

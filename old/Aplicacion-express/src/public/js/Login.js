const USUARIO_RECORDADO = 'km_usuario';

const form = document.getElementById('loginForm');
const usuario = document.getElementById('usuario');
const password = document.getElementById('password');
const recordar = document.getElementById('recordar');
const errorUsuario = document.getElementById('errorUsuario');
const errorPassword = document.getElementById('errorPassword');
const togglePass = document.getElementById('togglePass');
const btnLogin = form.querySelector('.btn-login');

// Si ya hay una sesión abierta en esta pestaña, no se vuelve a pedir el login.
if (leerSesion()) window.location.replace('home.html');

// "Recordarme" guarda solo el nombre de usuario, nunca la contraseña.
try {
  const guardado = localStorage.getItem(USUARIO_RECORDADO);
  if (guardado) {
    usuario.value = guardado;
    recordar.checked = true;
  }
} catch { /* almacenamiento bloqueado: se ignora */ }

// Mostrar / ocultar contraseña
togglePass.addEventListener('click', () => {
  const visible = password.type === 'text';
  password.type = visible ? 'password' : 'text';
  togglePass.textContent = visible ? 'Mostrar' : 'Ocultar';
  togglePass.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');
});

// Limpia el error al escribir
[usuario, password].forEach((input) => {
  input.addEventListener('input', () => {
    input.classList.remove('invalid');
    input.closest('.field').querySelector('.error').textContent = '';
  });
});

function validar() {
  let ok = true;

  if (!usuario.value.trim()) {
    usuario.classList.add('invalid');
    errorUsuario.textContent = 'Ingresa tu usuario';
    ok = false;
  }

  if (!password.value.trim()) {
    password.classList.add('invalid');
    errorPassword.textContent = 'Ingresa tu contraseña';
    ok = false;
  }

  return ok;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validar()) return;

  btnLogin.disabled = true;
  btnLogin.textContent = 'Ingresando…';

  try {
    const datos = await api('POST', '/auth/login', {
      usuario: usuario.value.trim(),
      password: password.value,
    });
    guardarSesion(datos);

    try {
      if (recordar.checked) localStorage.setItem(USUARIO_RECORDADO, usuario.value.trim());
      else localStorage.removeItem(USUARIO_RECORDADO);
    } catch { /* almacenamiento bloqueado: se ignora */ }

    window.location.href = 'home.html';
  } catch (error) {
    password.classList.add('invalid');
    errorPassword.textContent = error.message;
    btnLogin.disabled = false;
    btnLogin.textContent = 'Iniciar sesión';
  }
});

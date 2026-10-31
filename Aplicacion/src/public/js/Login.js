// Si es true, exige llenar usuario y contraseña antes de entrar.
// Ponlo en false para que el botón vaya directo a home.html.
const EXIGIR_CAMPOS = true;

const form = document.getElementById('loginForm');
const usuario = document.getElementById('usuario');
const password = document.getElementById('password');
const errorUsuario = document.getElementById('errorUsuario');
const errorPassword = document.getElementById('errorPassword');
const togglePass = document.getElementById('togglePass');

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

form.addEventListener('submit', (e) => {
  e.preventDefault();

  if (EXIGIR_CAMPOS && !validar()) return;

  // Maquetación: sin autenticación real, solo redirige.
  window.location.href = 'home.html';
});
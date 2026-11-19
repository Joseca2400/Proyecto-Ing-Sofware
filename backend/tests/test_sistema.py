def test_health_responde(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_estado_del_sistema_conecta_la_base_y_lee_la_migracion(cliente):
    respuesta = cliente.get("/api/v1/sistema/estado")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["mensaje"] == "Hola, mundo: la API responde"
    assert cuerpo["base_datos"]["conectada"] is True
    assert cuerpo["base_datos"]["motor"] == "postgresql"
    assert cuerpo["base_datos"]["revision_esquema"]  # la revisión vigente cambia con cada migración


def test_ruta_inexistente_usa_el_formato_de_error_comun(cliente):
    respuesta = cliente.get("/api/v1/no-existe")
    assert respuesta.status_code == 404
    assert "detail" in respuesta.json()


def test_los_esquemas_de_la_api_no_chocan_entre_modulos():
    """Dos módulos con un esquema del mismo nombre hacen que el OpenAPI los califique con el módulo
    (`app__modulos__…`) y los tipos generados del front dejan de coincidir."""
    from app.main import app

    repetidos = [nombre for nombre in app.openapi()["components"]["schemas"] if "__" in nombre]
    assert not repetidos, f"Esquemas con el mismo nombre en dos módulos: {repetidos}"

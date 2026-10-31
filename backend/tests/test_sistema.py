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
    assert cuerpo["base_datos"]["revision_esquema"] == "0001"


def test_ruta_inexistente_usa_el_formato_de_error_comun(cliente):
    respuesta = cliente.get("/api/v1/no-existe")
    assert respuesta.status_code == 404
    assert "detail" in respuesta.json()

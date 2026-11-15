import etiquetas
import datos
import modelo
import p_whatif
import resumen


def test_etiquetas_cubren_todos_los_capitulos_sin_cambiar_valores():
    d = datos.cargar()
    codigos = [str(c) for c in d.base["capitulo"].cat.categories]
    opciones = etiquetas.opciones("capitulo", codigos)
    assert list(opciones) == codigos
    assert set(codigos) == set(d.m3["niveles"]["capitulo"]) == set(etiquetas.NOMBRES)
    assert all(opciones[c].startswith(c + " — ") for c in codigos)
    assert etiquetas.etiqueta("capitulo", "desconocido") == "desconocido"
    assert "digestivo" in opciones["K00-K93"]
    assert "mentales" in opciones["F00-F99"]


def test_filtrado_y_simulacion_conservan_codigo():
    d = datos.cargar()
    codigo = "F00-F99"
    filtrado = resumen.filtrar(d.base, {"capitulo": [codigo]})
    assert len(filtrado) > 0 and set(filtrado["capitulo"].unique()) == {codigo}
    perfil = {**p_whatif.perfil_ref(d.m3), "capitulo": codigo}
    assert modelo.dias_estimados(perfil, d.m3)[0] > 0
    fig = p_whatif.fig_niveles(perfil, "capitulo", d.m3)
    assert codigo in fig.data[0].y
    assert etiquetas.etiqueta("capitulo", codigo) in fig.data[0].customdata
    assert fig.layout.height >= 21 * 26
    assert fig.layout.yaxis.dtick == 1
    assert etiquetas.etiqueta("capitulo", codigo) in str(p_whatif.leyenda_capitulos(d.m3))
    assert "digestivo" in p_whatif.textos_resultado(perfil, d.m3)["ref_desc"]


def test_establecimientos_descriptivos_preservan_codigo():
    assert etiquetas.opciones("establecimiento", ["SNSS", "No SNSS"]) == {
        "SNSS": "SNSS — Red de servicios de salud", "No SNSS": "No SNSS — Fuera de la red SNSS"
    }
    d = datos.cargar()
    perfil = p_whatif.perfil_ref(d.m3)
    fig = p_whatif.fig_niveles(perfil, "establecimiento", d.m3)
    assert etiquetas.etiqueta("establecimiento", "SNSS") in fig.data[0].y
    assert "Fuera de la red SNSS" in p_whatif.textos_resultado(perfil, d.m3)["ref_desc"]

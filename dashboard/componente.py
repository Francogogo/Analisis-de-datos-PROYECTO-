"""Contenedor de un gráfico o tabla con su explicación ampliable en un modal (ver www/js/componentes.js)."""
from shiny import ui


def componente(titulo: str, *cuerpo, resumen=None, detalle=None, abierto: bool = False) -> ui.Tag:
    """Muestra `cuerpo` y una lectura breve (`resumen`). Si hay `detalle`, agrega un botón que abre
    el mismo componente en un modal grande, donde `detalle` (oculto en la vista normal) sí se ve.
    Con `abierto=True` (tablas y bloques sin gráfico) el detalle se ve en la página y no hay modal."""
    # El botón va después de la lectura: se ve abajo a la derecha y así también le toca al final con Tab.
    return ui.div(
        *cuerpo,
        ui.div(resumen, class_="componente-resumen") if resumen is not None else None,
        ui.tags.button(
            "Detalles", type="button", class_="componente-abrir",
            aria_haspopup="dialog", aria_label=f"Detalles: {titulo}",
        ) if detalle is not None and not abierto else None,
        ui.div(detalle, class_="componente-detalle") if detalle is not None else None,
        class_="componente componente--abierto" if abierto else "componente",
        data_titulo=titulo,
    )


MODAL = ui.tags.dialog(
    ui.div(
        ui.h2("", id="modal-componente-titulo"),
        ui.tags.button("×", type="button", class_="modal-cerrar", aria_label="Cerrar"),
        class_="modal-cabecera",
    ),
    ui.div(class_="modal-cuerpo"),
    id="modal-componente",
    aria_labelledby="modal-componente-titulo",
)

from magicgui import magicgui, register_type
from napari import Viewer
from ._key_bindings import update_layers, toggle_hide_annotated_segments


def get_viewers(gui, *args):
    try:
        return (gui.parent().qt_viewer.viewer,)
    except AttributeError:
        return tuple(v for v in globals().values() if isinstance(v, Viewer))


register_type(Viewer, choices=get_viewers)


@magicgui(call_button='update layers [u]', viewer={"visible": False})
def update_layers_gui(viewer: Viewer):
    update_layers(viewer)


@magicgui(call_button='hide annotated cells [h]', viewer={"visible": False})
def toggle_hide_annotated_segments_gui(viewer: Viewer):
    toggle_hide_annotated_segments(viewer)

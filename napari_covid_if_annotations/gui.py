from magicgui import magicgui
from napari import Viewer
from ._key_bindings import update_layers, toggle_hide_annotated_segments


@magicgui(call_button='update layers [u]')
def update_layers_gui(viewer: Viewer):
    update_layers(viewer)


@magicgui(call_button='hide annotated cells [h]')
def toggle_hide_annotated_segments_gui(viewer: Viewer):
    toggle_hide_annotated_segments(viewer)

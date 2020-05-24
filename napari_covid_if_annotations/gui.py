from magicgui import magicgui
from ._key_bindings import update_layers, toggle_hide_annotated_segments


@magicgui(call_button='update layers [u]', ignore=['viewer'])
def update_layers_gui(viewer):
    update_layers(viewer)


@magicgui(call_button='hide annotated cells [h]', ignore=['viewer'])
def toggle_hide_annotated_segments_gui(viewer):
    toggle_hide_annotated_segments(viewer)

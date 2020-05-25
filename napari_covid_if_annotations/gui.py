from magicgui import magicgui, register_type
from napari import Viewer
from napari.layers.labels import Labels
from ._key_bindings import update_layers, toggle_hide_annotated_segments, paint_new_label


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


@magicgui(call_button='get next label [n]', viewer={"visible": False})
def paint_new_label_gui(labels: Labels, viewer: Viewer):
    # TODO
    # it would be nice to also change the active layer here, but if I call
    # viewer.active_layer = labels
    # it seems to activate the labels layer without deactivating the current layer properly
    paint_new_label(labels)


def connect_to_viewer(viewer):
    """ Add all gui elements to the viewer
    """
    # the update layers button
    update_gui = update_layers_gui.Gui()
    viewer.window.add_dock_widget(update_gui)

    # the hide annotated segments button
    hide_gui = toggle_hide_annotated_segments_gui.Gui()
    viewer.window.add_dock_widget(hide_gui)

    # the paint new labels button
    paint_gui = paint_new_label_gui.Gui()
    viewer.window.add_dock_widget(paint_gui)
    viewer.layers.events.changed.connect(lambda x: paint_gui.refresh_choices())
    paint_gui.refresh_choices()

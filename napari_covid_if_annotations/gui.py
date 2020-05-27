from magicgui import magicgui, register_type
from napari import Viewer
from qtpy import QtWidgets
from ._key_bindings import update_layers, toggle_hide_annotated_segments, paint_new_label, save

#
# modify the layers
#


def modify_layers(viewer):
    control_widgets = viewer.window.qt_viewer.controls.widgets

    # disable the add point button in the infected-vs-control layer
    points_controls = control_widgets[viewer.layers['infected-vs-control']]
    points_controls.addition_button.setEnabled(False)


#
# additional gui elements
#


def get_viewers(gui, *args):
    try:
        return (gui.parent().qt_viewer.viewer,)
    except AttributeError:
        return tuple(v for v in globals().values() if isinstance(v, Viewer))


register_type(Viewer, choices=get_viewers)


# TODO expose the partial parameter to the gui
@magicgui(call_button='save annotations [shfit + s]', viewer={'visible': False})
def save_gui(viewer: Viewer):
    save(viewer)


@magicgui(call_button='update layers [u]', viewer={"visible": False})
def update_layers_gui(viewer: Viewer):
    update_layers(viewer)


@magicgui(call_button='hide annotated cells [h]', viewer={"visible": False})
def toggle_hide_annotated_segments_gui(viewer: Viewer):
    toggle_hide_annotated_segments(viewer)


@magicgui(call_button='get next label [n]', viewer={"visible": False})
def paint_new_label_gui(viewer: Viewer):
    paint_new_label(viewer)


def connect_to_viewer(viewer):
    """ Add all gui elements to the viewer
    """

    # get gui buttons for the additional functionality
    saving_gui = save_gui.Gui()
    update_gui = update_layers_gui.Gui()
    hide_gui = toggle_hide_annotated_segments_gui.Gui()
    paint_gui = paint_new_label_gui.Gui()

    # make a tooltop about the label colors
    # TODO instead of this, do "Labels: Unlabeled, Infected, Control, Uncertain" and each in their respective color
    tooltip = QtWidgets.QLabel("White: unlabeled; Red: infected; Cyan: control; Yellow: uncertain")

    # merge all the gui elements
    my_gui = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()
    my_gui.setLayout(layout)
    layout.addWidget(tooltip)
    layout.addWidget(saving_gui)
    layout.addWidget(update_gui)
    layout.addWidget(hide_gui)
    layout.addWidget(paint_gui)

    # add them to the viewer
    viewer.window.add_dock_widget(my_gui, area='right', allowed_areas=['right', 'left'])

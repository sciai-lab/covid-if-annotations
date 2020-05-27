import os
from magicgui import magicgui, register_type
from napari import Viewer
from qtpy import QtWidgets
from ._key_bindings import update_layers, toggle_hide_annotated_segments, paint_new_label, _save_labels

#
# additional gui elements
#


def get_viewers(gui, *args):
    try:
        viewer = gui.parent().qt_viewer.viewer
        return (viewer,)
    except AttributeError:
        return tuple(v for v in globals().values() if isinstance(v, Viewer))


register_type(Viewer, choices=get_viewers)


# FIXME the gui is broken and gets passed None !
# TODO expose the partial parameter to the gui
@magicgui(call_button='save annotations [shfit + s]', viewer={'visible': False})
def save_gui(viewer: Viewer):
    print(viewer)
    _save_labels(viewer)


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
    # tooltip = QtWidgets.QLabel("White: unlabeled; Red: infected; Cyan: control; Yellow: uncertain")
    tooltip = QtWidgets.QLabel()

    # TODO see if we can get this working
    im_file = os.path.join(os.path.split(__file__)[0], 'images', 'placeholder.png')
    if os.path.exists(im_file):
        qimage = None
        tooltip.setPicture(qimage)
    else:
        qtext = "<b>Labels:</b>"
        qtext += "<br><font color='white'>Unlabeled</font> <br> <font color='red'>Infected</font>"
        qtext += "<br><font color='cyan'>Control</font> <br> <font color='yellow'>Uncertain</font>"
        tooltip.setText(qtext)

    # merge all the gui elements
    my_gui = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()

    my_gui.setLayout(layout)
    layout.addWidget(tooltip)
    layout.addWidget(update_gui)
    layout.addWidget(hide_gui)
    layout.addWidget(paint_gui)
    layout.addWidget(saving_gui)

    # add them to the viewer
    viewer.window.add_dock_widget(my_gui, area='right', allowed_areas=['right', 'left'])

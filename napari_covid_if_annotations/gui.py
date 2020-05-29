import os
from qtpy.QtWidgets import QLabel, QPushButton
from ._key_bindings import (
    update_layers,
    toggle_hide_annotated_segments,
    paint_new_label,
    _save_labels,
)


def connect_to_viewer(viewer):
    """ Add all gui elements to the viewer
    """

    save_gui_btn = QPushButton("save annotations [shift + s]")
    save_gui_btn.clicked.connect(lambda: _save_labels(viewer))

    update_gui_btn = QPushButton("update layers [u]")
    update_gui_btn.clicked.connect(lambda: update_layers(viewer))

    hide_gui_btn = QPushButton("hide annotated cells [h]")
    hide_gui_btn.clicked.connect(lambda: toggle_hide_annotated_segments(viewer))

    paint_gui_btn = QPushButton("get next label [n]")
    paint_gui_btn.clicked.connect(lambda: paint_new_label(viewer))

    # make a tooltop about the label colors
    tooltip = QLabel()

    # TODO see if we can get this working
    im_file = os.path.join(os.path.split(__file__)[0], "images", "placeholder.png")
    if os.path.exists(im_file):
        qimage = None
        tooltip.setPicture(qimage)
    else:
        qtext = "<b>Labels:</b>"
        qtext += "<br><font color='white'>Unlabeled</font> <br> <font color='red'>Infected</font>"
        qtext += "<br><font color='cyan'>Control</font> <br> <font color='yellow'>Uncertain</font>"
        tooltip.setText(qtext)

    viewer.window.add_dock_widget(
        [tooltip, update_gui_btn, hide_gui_btn, paint_gui_btn, save_gui_btn],
        area="right",
        allowed_areas=["right", "left"],
    )

import os

import numpy as np
from napari import Viewer
from napari.layers.points import Points
from napari.layers.labels import Labels

from .image_utils import get_edge_segmentation, get_centroids, map_labels_to_edges
from .layers import get_centroid_properties, save_labels


def replace_layer(new_layer, layers, name_to_replace, protected_metadata=None):
    for layer in layers:
        if layer.name == name_to_replace:
            if protected_metadata is None:
                new_metadata = new_layer.metadata
            else:
                new_metadata = layer.metadata
                new_metadata.update({k: v for k, v in new_layer.metadata.items()
                                     if k not in protected_metadata})
            layer.data = new_layer.data
            layer.metadata = new_metadata

            if isinstance(layer, Points):
                layer.properties = new_layer.properties

    layers.remove(new_layer.name)


# the event object will have the following useful things:
# event.source -> the full viewer.layers object itself
# event.item -> the specific layer that cause the change
# event.type -> a string like 'added', 'removed'
def on_layer_change(event):
    try:
        # if we add new labels or new points, we need to replace instead
        # of adding them
        if isinstance(event.item, Labels) and event.type == 'added':
            layers = event.source
            layer = event.item
            if len([ll for ll in layers if isinstance(ll, Labels)]) > 1:
                replace_layer(layer, layers, 'cell-segmentation', protected_metadata=['filename'])

        if isinstance(event.item, Points) and event.type == 'added':
            layers = event.source
            layer = event.item
            if len([ll for ll in layers if isinstance(ll, Points)]) > 1:
                replace_layer(event.item, layers, 'infected-vs-control')

        # add the 'change label on click' functionality to the points layer
        if isinstance(event.item, Points) and event.type == 'added':
            event.item.mouse_drag_callbacks.append(next_on_click)
    except AttributeError:
        pass


def update_infected_labels_from_segmentation(seg_ids, prev_seg_ids, infected_labels):
    assert len(infected_labels) == len(prev_seg_ids), f"{len(infected_labels)}, {len(prev_seg_ids)}"
    if np.array_equal(seg_ids, prev_seg_ids):
        return infected_labels
    else:
        new_infected_labels = np.zeros_like(seg_ids)
        mask_a = np.isin(seg_ids, prev_seg_ids)
        mask_b = np.isin(prev_seg_ids, seg_ids)

        new_infected_labels[mask_a] = infected_labels[mask_b]
        assert len(new_infected_labels) == len(seg_ids), f"{len(new_infected_labels)}, {len(seg_ids)}"

        return new_infected_labels


# NOTE we expect len(point_labels) == len(infected_labels) - 1
# because we don't have a point for the background
def update_infected_labels_from_points(point_labels, infected_labels):
    assert len(point_labels) == len(infected_labels) - 1
    return np.array([0] + point_labels.tolist())


# TODO we should also disable removing all the layers!
def modify_points_layer(viewer):
    control_widgets = viewer.window.qt_viewer.controls.widgets
    # disable the add point button in the infected-vs-control layer
    points_controls = control_widgets[viewer.layers['infected-vs-control']]
    points_controls.addition_button.setEnabled(False)
    points_controls.select_button.setEnabled(False)


#
# keybindings for the viewer
#

@Viewer.bind_key('n')
def paint_new_label(viewer):
    # FIXME this should be calloed on initialization, but don't know how to do it via the events
    modify_points_layer(viewer)

    layer = viewer.layers['cell-segmentation']
    viewer.layers.unselect_all()
    layer.selected = True
    seg = layer.data
    next_label = seg.max() + 1
    layer.mode = 'paint'
    layer.selected_label = next_label


@Viewer.bind_key('Shift-S')
def _save_labels(viewer, is_partial=False):
    # FIXME this should be calloed on initialization, but don't know how to do it via the events
    modify_points_layer(viewer)

    # we need to update before saving, otherwise segmentation
    update_layers(viewer)

    to_save = [
        (viewer.layers['cell-segmentation'], {}, 'labels')
    ]
    save_labels(os.getcwd(), to_save, is_partial)


@Viewer.bind_key('u')
def update_layers(viewer):
    # FIXME this should be calloed on initialization, but don't know how to do it via the events
    modify_points_layer(viewer)

    # get the segmentation as well as the previous seg ids and infected labels
    # from the segmentation layer
    seg_layer = viewer.layers['cell-segmentation']
    seg = seg_layer.data
    metadata = seg_layer.metadata
    prev_seg_ids, infected_labels = metadata['seg_ids'], metadata['infected_labels']
    seg_ids = np.unique(seg)

    # get the updated labels from the point layer properties
    points_layer = viewer.layers['infected-vs-control']
    point_labels = points_layer.properties['cell_type']
    infected_labels = update_infected_labels_from_points(point_labels, infected_labels)

    # the seg ids might have changed because labels were erased or new labels were added
    # in this case, we need to update the infected labels
    infected_labels = update_infected_labels_from_segmentation(seg_ids, prev_seg_ids, infected_labels)
    metadata.update({'seg_ids': seg_ids, 'infected_labels': infected_labels})

    hide_annotated_segments = metadata['hide_annotated_segments']
    if hide_annotated_segments:
        # TODO the most elegant vay to hide annotated segments would be to
        hidden_segments = seg_ids[infected_labels > 0]
        # color_dict = {seg_id: 'transparent' for seg_id in hidden_segments}
    else:
        hidden_segments = None
    viewer.layers['cell-segmentation'].metadata = metadata

    # get the new centroids and update the centroid properties
    centroids = get_centroids(seg)
    properties = get_centroid_properties(centroids, infected_labels)

    viewer.layers['infected-vs-control'].data = centroids
    viewer.layers['infected-vs-control'].properties = properties
    # need to call refresh colors here, otherwise new centroids don't get the correct color
    viewer.layers['infected-vs-control'].refresh_colors()

    edge_width = viewer.layers['cell-outlines'].metadata['edge_width']
    edges = get_edge_segmentation(seg, edge_width)
    infected_edges = map_labels_to_edges(edges, seg_ids, infected_labels, hidden_segments, remap_background=4)
    viewer.layers['cell-outlines'].data = infected_edges


@Viewer.bind_key('h')
def toggle_hide_annotated_segments(viewer):
    # FIXME this should be calloed on initialization, but don't know how for io hook
    modify_points_layer(viewer)

    seg_layer = viewer.layers['cell-segmentation']
    metadata = seg_layer.metadata
    metadata['hide_annotated_segments'] = not metadata['hide_annotated_segments']
    viewer.layers['cell-segmentation'].metadata = metadata
    update_layers(viewer)


#
# keybindings for toggling the labels of the point layer
#

def next_label(layer, event=None):
    """Keybinding to advance to the next label value in
    the labels list (defined near the top) with wraparound

    Setting the values in points_layer.current_properties modifies the property
    values for the currently selected points and also will be the values used for
    the next points that are added.
    """
    if layer._value is None:
        return

    labels = layer.metadata['labels']
    layer.selected_data = [layer._value]

    # get the current properties and cell type value
    current_properties = layer.current_properties
    current_label = current_properties['cell_type'][0]

    # get the next label value with wraparound
    ind = list(labels).index(current_label)
    new_ind = (ind + 1) % len(labels)
    new_label = labels[new_ind]

    # set the new cell type value and update the current_properties
    current_properties['cell_type'] = np.array([new_label])
    layer.current_properties = current_properties


def next_on_click(layer, event):
    """Mouse click binding to advance the label of the point under cursor"""
    next_label(layer)

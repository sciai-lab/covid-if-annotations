import os

import numpy as np
from napari import Viewer
from napari.layers.points import Points

from .image_utils import get_edge_segmentation, get_centroids, map_labels_to_edges
from .layers import get_centroid_properties, save_labels


def update_infected_labels_from_segmentation(seg_ids, prev_seg_ids, infected_labels):
    if np.array_equal(seg_ids, prev_seg_ids):
        return infected_labels
    else:
        # TODO update the infected labels according to the diff in seg_ids
        pass


# NOTE we expect len(point_labels) == len(infected_labels) - 1
# because we don't have a point for the background
def update_infected_labels_from_points(point_labels, infected_labels):
    assert len(point_labels) == len(infected_labels) - 1
    return np.array([0] + point_labels.tolist())


#
# keybindings for the viewer
#

@Viewer.bind_key('n')
def paint_new_label(viewer):
    layer = viewer.layers['cell-segmentation']
    viewer.layers.unselect_all()
    layer.selected = True
    seg = layer.data
    next_label = seg.max() + 1
    layer.mode = 'paint'
    layer.selected_label = next_label


@Viewer.bind_key('Shift-S')
def save(viewer, is_partial=False):
    to_save = [
        (viewer.layers['cell-segmentation'], {}, 'labels')
    ]
    save_labels(os.getcwd(), to_save, is_partial)


@Viewer.bind_key('u')
def update_layers(viewer):

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
    # TODO the most elegant vay to hide annotated segments would be to
    # change the color map for these segment ids. I don't know if this is possible / how to do it.
    if hide_annotated_segments:
        pass
        # hidden_segments = seg_ids[infected_labels > 0]
        # color_dict = {seg_id: 'transparent' for seg_id in hidden_segments}
    viewer.layers['cell-segmentation'].metadata = metadata

    # get the new centroids and update the centroid properties
    centroids = get_centroids(seg)
    properties = get_centroid_properties(centroids, infected_labels)
    viewer.layers['infected-vs-control'].data = centroids
    viewer.layers['infected-vs-control'].properties = properties

    if hide_annotated_segments:
        infected_edges = np.zeros_like(seg)
    else:
        edge_width = viewer.layers['cell-outlines'].metadata['edge_width']
        edges = get_edge_segmentation(seg, edge_width)
        infected_edges = map_labels_to_edges(edges, seg_ids, infected_labels)
    viewer.layers['cell-outlines'].data = infected_edges


@Viewer.bind_key('h')
def toggle_hide_annotated_segments(viewer):
    seg_layer = viewer.layers['cell-segmentation']
    metadata = seg_layer.metadata
    metadata['hide_annotated_segments'] = not metadata['hide_annotated_segments']
    viewer.layers['cell-segmentation'].metadata = metadata
    update_layers(viewer)


#
# keybindings for toggling the labels of the point layer
#

@Points.bind_key('.')
def next_label(layer, event=None):
    """Keybinding to advance to the next label value in
    the labels list (defined near the top) with wraparound

    Setting the values in points_layer.current_properties modifies the property
    values for the currently selected points and also will be the values used for
    the next points that are added.
    """
    labels = layer.metadata['labels']

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
    """Mouse click binding to advance the label of the selected point"""

    # only do stuff in selection mode
    if not layer.mode == 'select':
        return

    # only do stuff if we have next on click in the mouse bindings
    if next_on_click not in layer.mouse_drag_callbacks:
        return

    # make sure that next on click is always the last callback in the mouse bindings
    # otherwise we have unintended consequences when selecting a new node
    if next_on_click in layer.mouse_drag_callbacks and next_on_click != layer.mouse_drag_callbacks[-1]:
        layer.mouse_drag_callbacks.remove(next_on_click)
        layer.mouse_drag_callbacks.append(next_on_click)
        return

    if len(layer.selected_data) > 0:
        next_label(layer)


def set_toggle_mode(viewer):
    """Keybinding to set the viewer selection mode and mouse callbacks
    for toggling selected points properties by clicking on them
    """
    layer = viewer.layers['infected-vs-control']
    layer.mouse_drag_callbacks.append(next_on_click)

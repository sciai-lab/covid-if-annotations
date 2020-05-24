import numpy as np
from napari import Viewer
from .image_utils import get_edge_segmentation, get_centroids, map_labels_to_edges
from .layers import get_centroid_properties


def update_infected_labels_from_segmentation(seg_ids, prev_seg_ids, infected_labels):
    if np.array_equal(seg_ids, prev_seg_ids):
        return infected_labels
    else:
        # TODO update the infected labels according to the diff in seg_ids
        pass


# NOTE we expect len(point_labels) == len(infected_labels) - 1
# because we don't have a point for the background
def update_infected_labels_from_points(point_labels, infected_labels, labels):
    assert len(point_labels) == len(infected_labels) - 1
    labels_to_val = {label: ii for ii, label in enumerate(labels)}
    infected_labels = np.array([0] + [labels_to_val[point_label] for point_label in point_labels])
    return infected_labels


#
# keybindings for updating the layers
#


# TODO this is still a bit slow and interactivity would profit from speeding it up.
# I think the best candidate for this is 'get_edge_segmentation', which includes a loop over
# every segment and performs erosion in this loop
# TODO create a corresponing gui element via magicgui
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
    labels = points_layer.metadata['labels']
    infected_labels = update_infected_labels_from_points(point_labels, infected_labels, labels)

    # the seg ids might have changed because labels were erased or new labels were added
    # in this case, we need to update the infected labels
    infected_labels = update_infected_labels_from_segmentation(seg_ids, prev_seg_ids, infected_labels)
    metadata.update({'seg_ids': seg_ids, 'infected_labels': infected_labels})

    hide_annotated_segments = metadata['hide_annotated_segments']
    if hide_annotated_segments:
        hidden_segments = seg_ids[infected_labels > 0]
        # TODO the most elegant vay to hide annotated segments would be to
        # change the color map for these segment ids. I don't know if this is possible / how to do it.
    else:
        hidden_segments = None
    viewer.layers['cell-segmentation'].metadata = metadata

    # get the new centroids and update the centroid properties
    centroids = get_centroids(seg)
    properties = get_centroid_properties(centroids, infected_labels, labels)
    viewer.layers['infected-vs-control'].data = centroids
    viewer.layers['infected-vs-control'].properties = properties

    edges = get_edge_segmentation(seg, 2)
    infected_edges = map_labels_to_edges(edges, seg_ids, infected_labels, hidden_segments)
    viewer.layers['cell-outlines'].data = infected_edges


# TODO create a corresponing gui element via magicgui
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

@Viewer.bind_key('.')
def next_label(viewer, event=None):
    """Keybinding to advance to the next label value in
    the labels list (defined near the top) with wraparound

    Setting the values in points_layer.current_properties modifies the property
    values for the currently selected points and also will be the values used for
    the next points that are added.
    """
    points_layer = viewer.layers['infected-vs-control']
    labels = points_layer.metadata['labels']

    # get the current properties and cell type value
    current_properties = points_layer.current_properties
    current_label = current_properties['cell_type'][0]

    print("Current_label:", current_label)
    # get the next label value with wraparound
    ind = list(labels).index(current_label)
    print("Current index:", ind)
    new_ind = (ind + 1) % len(labels)
    print("New index:", new_ind)
    new_label = labels[new_ind]

    print("New label:", new_label)
    # set the new cell type value and update the current_properties
    current_properties['cell_type'] = np.array([new_label])
    points_layer.current_properties = current_properties


def next_on_click(layer, event):
    """Mouse click binding to advance the label of the selected point"""
    # only perform toggling if in the selection mode and there are points selected
    if (layer.mode == 'select') and (len(layer.selected_data) > 0):
        # check that the mouse click callback is in the right position
        if layer.mouse_drag_callbacks.index(next_on_click) > 0:
            # FIXME this does not work, because we need to pass the viewer to it!
            next_label()


# also have a gui element to activate/deactivate?
@Viewer.bind_key('t')
def set_toggle_mode(viewer, event=None):
    """Keybinding to set the viewer selection mode and mouse callbacks
    for toggling selected points properties by clicking on them
    """
    points_layer = viewer.layers['infected-vs-control']
    if next_on_click in points_layer.mouse_drag_callbacks:
        points_layer.mouse_drag_callbacks.remove(next_on_click)
    points_layer.mode = 'select'
    points_layer.mouse_drag_callbacks.append(next_on_click)

import numpy as np
from napari import Viewer
from .image_utils import get_edge_segmentation, get_centroids, map_labels_to_edges


def update_infected_labels(seg_ids, prev_seg_ids, infected_labels):
    if np.array_equal(seg_ids, prev_seg_ids):
        return infected_labels
    else:
        # TODO update the infected labels according to the diff in seg_ids
        pass


# TODO would be better to have this as an event listener that is triggered whenever
# the segmentation is update (= painted) but I don't know how to do this
# add a key binding to update the edges and point layers from the segmentation
@Viewer.bind_key('u')
def update_edges_and_centroids(viewer):
    # get the segmentation as well as the previous seg ids and infected labels
    # from the segmentation layer
    seg_layer = viewer.layers['cell-segmentation']
    seg = seg_layer.data
    metadata = seg_layer.metadata
    prev_seg_ids, infected_labels = metadata['seg_ids'], metadata['infected_labels']
    seg_ids = np.unique(seg)

    # the seg ids might have changed because labels were erased or new labels were added
    # in this case, we need to update the infected labels
    infected_labels = update_infected_labels(seg_ids, prev_seg_ids, infected_labels)
    metadata.update({'seg_ids': seg_ids, 'infected_labels': infected_labels})
    viewer.layers['cell-segmentation'].metadata = metadata

    # TODO need to set the values of the points according to the infected labels
    centroids = get_centroids(seg)
    viewer.layers['infected-vs-control'].data = centroids

    edges = get_edge_segmentation(seg, 2)
    infected_edges = map_labels_to_edges(edges, seg_ids, infected_labels)
    viewer.layers['cell-outlines'].data = infected_edges


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

    # get the next label value with wraparound
    ind = list(labels).index(current_label)
    new_ind = (ind + 1) % len(labels)
    new_label = labels[new_ind]

    # set the new cell type value and update the current_properties
    current_properties['cell_type'] = np.array([new_label])
    points_layer.current_properties = current_properties

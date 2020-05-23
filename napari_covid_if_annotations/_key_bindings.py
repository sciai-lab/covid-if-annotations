import numpy as np
from napari import Viewer
from .image_utils import get_edge_segmentation, get_centroids
from .io_utils import to_infected_edges


# TODO would be better to have this as an event listener that is triggered whenever
# the segmentation is update (= painted) but I don't know how to do this
# add a key binding to update the edges and point layers from the segmentation
@Viewer.bind_key('u')
def update_edges_and_centroids(viewer):
    infected_labels = viewer.infected_labels
    seg = viewer.layers['cell-segmentation'].data

    # TODO need to set the values of the points according to the infected labels
    centroids = get_centroids(seg)
    viewer.layers['centers'].data = centroids

    edges = get_edge_segmentation(seg, 2)
    seg_ids = np.unique(seg)
    infected_edges = to_infected_edges(edges, seg_ids, infected_labels)
    viewer.layers['infected-classification'].data = infected_edges

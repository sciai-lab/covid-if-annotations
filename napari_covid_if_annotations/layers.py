import numpy as np
import skimage.color as skc

from .image_utils import (get_centroids, get_edge_segmentation, map_labels_to_edges,
                          normalize, quantile_normalize)
from .io_utils import read_image, read_table


def get_raw_data(f, seg, saturation_factor):

    serum = normalize(read_image(f, 'serum_IgG'))
    marker = quantile_normalize(read_image(f, 'marker'))
    nuclei = normalize(read_image(f, 'nuclei'))
    bg_mask = seg == 0

    def subtract_bg(im):
        bg = np.median(im[bg_mask])
        im -= bg
        return im

    serum = subtract_bg(serum)
    marker = subtract_bg(marker)
    nuclei = subtract_bg(nuclei)

    raw = np.concatenate([marker[..., None], serum[..., None], nuclei[..., None]], axis=-1)
    if saturation_factor > 1:
        raw = skc.rgb2hsv(raw)
        raw[..., 1] *= saturation_factor
        raw = skc.hsv2rgb(raw).clip(0, 1)

    return raw, marker


def get_segmentation_data(f, seg, edge_width):
    _, infected_labels = read_table(f, 'infected_cell_labels')
    assert len(infected_labels) == seg.max() + 1
    assert infected_labels.shape[1] == 2
    infected_labels = infected_labels[:, 1]

    seg_ids = np.unique(seg)
    assert seg_ids.shape == infected_labels.shape, f"{seg_ids.shape}, {infected_labels.shape}"

    edges = get_edge_segmentation(seg, edge_width)
    infected_edges = map_labels_to_edges(edges, seg_ids, infected_labels)

    centroids = get_centroids(seg)

    return seg_ids, centroids, infected_edges, infected_labels


def get_layers_from_file(f, saturation_factor=1., edge_width=2):
    seg = read_image(f, 'cell_segmentation')

    raw, marker = get_raw_data(f, seg, saturation_factor)
    (seg_ids, centroids,
     infected_edges, infected_labels) = get_segmentation_data(f, seg, edge_width)

    seg_kwargs = {
        'name': 'cell-segmentation',
        'metadata': {'seg_ids': seg_ids,
                     'infected_labels': infected_labels}
    }

    # the kwargs for the point layer we use for semantic labeling
    # TODO this is based on the example code by @kevinyamauchi, I don't understand
    # the meaning of the following parameters yet:
    # - properties (how exactly are these associated with points?)
    # - confidence

    n_points = len(centroids)
    labels = ['unlabeled', 'infected', 'control', 'uncertain']
    face_color_cycle = ['white', 'red', 'cyan', 'yellow']
    properties = {
        'confidence': np.zeros(n_points),
        'cell_type': np.array(['unlabeled'] * n_points)
    }

    centroid_kwargs = {
        'name': 'infected-vs-control',
        'properties': properties,
        'size': 15,
        'edge_width': 5,
        'edge_color': 'black',
        'edge_colormap': 'gray',
        'face_color': 'cell_type',
        'face_color_cycle': face_color_cycle,
        'metadata': {'labels': labels}
    }

    layers = [
        (raw, {'name': 'raw'}, 'image'),
        (marker, {'name': 'virus-marker', 'visible': False}, 'image'),
        (seg, seg_kwargs, 'labels'),
        (infected_edges, {'name': 'cell-outlines', 'visible': False}, 'labels'),
        (centroids, centroid_kwargs, 'points')
    ]
    return layers

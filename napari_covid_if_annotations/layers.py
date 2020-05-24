import numpy as np
import skimage.color as skc
from vispy.color import Colormap

from .image_utils import (get_centroids, get_edge_segmentation, map_labels_to_edges,
                          normalize, quantile_normalize)
from .io_utils import has_table, read_image, read_table


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


def get_segmentation_data(f, seg, edge_width, infected_label_name='infected_cell_labels'):

    seg_ids = np.unique(seg)
    # TODO log if labels were loaded or initialized to be zero
    if has_table(f, infected_label_name):
        _, infected_labels = read_table(f, infected_label_name)
        assert infected_labels.shape[1] == 2
        infected_labels = infected_labels[:, 1]
        infected_labels = infected_labels.astype('int32')

        # we only support labels [0, 1, 2, 3] = ['unlabeled', 'infected', 'control', 'uncertain']
        expected_labels = {0, 1, 2, 3}
        unique_labels = np.unique(infected_labels)
        assert len(set(unique_labels) - expected_labels) == 0
        # the background should always be mapped to 0
        assert infected_labels[0] == 0

    else:
        infected_labels = np.zeros(len(seg_ids), dtype='int32')

    assert seg_ids.shape == infected_labels.shape, f"{seg_ids.shape}, {infected_labels.shape}"

    edges = get_edge_segmentation(seg, edge_width)
    infected_edges = map_labels_to_edges(edges, seg_ids, infected_labels)

    centroids = get_centroids(seg)

    return seg_ids, centroids, infected_edges, infected_labels


def get_centroid_properties(centroids, infected_labels):
    label_values = infected_labels[1:]
    assert len(label_values) == len(centroids), f"{len(label_values)}, {len(centroids)}"
    properties = {'cell_type': label_values}
    return properties


def get_layers_from_file(f, saturation_factor=1., edge_width=2):
    seg = read_image(f, 'cell_segmentation')

    raw, marker = get_raw_data(f, seg, saturation_factor)
    (seg_ids, centroids,
     infected_edges, infected_labels) = get_segmentation_data(f, seg, edge_width)

    # the keyword arguments passed to 'add_labels' for the cell segmentation layer
    seg_kwargs = {
        'name': 'cell-segmentation',
        'metadata': {'seg_ids': seg_ids,
                     'infected_labels': infected_labels,
                     'hide_annotated_segments': False}
    }

    # the keyword arguments passed to 'add_image' for the edge layer
    # custom colormap to have colors in sync with the point layer
    cmap = Colormap([
        [0., 0., 0., 0.],  # label 0 is fully transparent
        [1., 0., 0., 1.],  # label 1 is red
        [0., 1., 1., 1.],  # label 2 is cyan
        [1., 1., 0., 1.],  # label 3 is yellow
    ])
    edge_kwargs = {
        'name': 'cell-outlines',
        'visible': False,
        'colormap': cmap,
        'metadata': {'edge_width': edge_width},
        'contrast_limits': [0, 3]
    }

    # napari reorders the labels (it casts np.unique)
    # so for now it's easier to just use numeric labels and have separate
    # label-names to not get confused by reordering
    label_names = ['unlabeled', 'infected', 'control', 'uncertain']
    labels = [0, 1, 2, 3]
    face_color_cycle = ['white', 'red', 'cyan', 'yellow']

    properties = get_centroid_properties(centroids, infected_labels)
    centroid_kwargs = {
        'name': 'infected-vs-control',
        'properties': properties,
        'size': 15,
        'edge_width': 5,
        'edge_color': 'black',
        'edge_colormap': 'gray',
        'face_color': 'cell_type',
        'face_color_cycle': face_color_cycle,
        'metadata': {'labels': labels,
                     'label_names': label_names}
    }

    layers = [
        (raw, {'name': 'raw'}, 'image'),
        (marker, {'name': 'virus-marker', 'visible': False}, 'image'),
        (seg, seg_kwargs, 'labels'),
        (infected_edges, edge_kwargs, 'image'),
        (centroids, centroid_kwargs, 'points')
    ]
    return layers

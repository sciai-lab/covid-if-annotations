import numpy as np
from scipy.ndimage.morphology import binary_dilation
from skimage.measure import regionprops
from skimage.segmentation import find_boundaries


def normalize(im):
    im = im.astype('float32')
    im -= im.min()
    im /= im.max()
    return im


def quantile_normalize(im, low=.01, high=.99):
    im = im.astype('float32')
    tlow, thigh = np.quantile(im, low), np.quantile(im, high)
    im -= tlow
    im /= thigh
    return np.clip(im, 0., 1.)


def get_edge_segmentation(seg, edge_width):
    edge_seg = seg.copy()
    boundaries = find_boundaries(seg, mode='thick')
    if edge_width > 1:
        boundaries = binary_dilation(boundaries, iterations=edge_width-1)
    edge_seg[~boundaries] = 0
    return edge_seg


def get_centroids(seg):
    props = regionprops(seg)
    return np.array([prop['centroid'] for prop in props])


def apply_dict_to_array(x, my_dict):
    unique_values, inverse_indices = np.unique(x, return_inverse=True)
    return np.array([my_dict[val] for val in unique_values])[inverse_indices].reshape(x.shape)


def map_labels_to_edges(edges, seg_ids, labels, hide_ids=None, remap_background=None):
    assert len(seg_ids) == len(labels)
    replace_dict = dict(zip(seg_ids, labels))

    if hide_ids is not None:
        for hide_id in hide_ids:
            replace_dict[hide_id] = 0 if remap_background is None else remap_background
    if remap_background is not None:
        replace_dict[0] = remap_background

    return apply_dict_to_array(edges, replace_dict)

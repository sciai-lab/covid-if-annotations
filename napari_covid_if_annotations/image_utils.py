import numpy as np
from scipy.ndimage.morphology import binary_erosion
from skimage.measure import regionprops


def normalize(im):
    im = im.astype('float32')
    im -= im.min()
    im /= im.max()
    return im


def quantile_normalize(im, low=.01, high=.99):
    tlow, thigh = np.quantile(im, low), np.quantile(im, high)
    im -= tlow
    im /= thigh
    return np.clip(im, 0., 1.)


def get_edge_segmentation(seg, iters):
    seg_ids = np.unique(seg)[1:]
    new_seg = np.zeros_like(seg)
    for seg_id in seg_ids:
        seg_mask = seg == seg_id
        eroded_mask = binary_erosion(seg_mask, iterations=iters)
        edge_mask = np.logical_xor(seg_mask, eroded_mask)
        new_seg[edge_mask] = seg_id
    return new_seg


def get_centroids(seg):
    props = regionprops(seg)
    return np.array([prop['centroid'] for prop in props])


def apply_dict_to_array(x, my_dict):
    unique_values, inverse_indices = np.unique(x, return_inverse=True)
    return np.array([my_dict[val] for val in unique_values])[inverse_indices].reshape(x.shape)


def map_labels_to_edges(edges, seg_ids, labels):
    assert len(seg_ids) == len(labels)
    replace_dict = dict(zip(seg_ids, labels))
    return apply_dict_to_array(edges, replace_dict)

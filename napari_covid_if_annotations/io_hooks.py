"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the ``napari_get_reader`` hook specification, (to create
a reader plugin) but your plugin may choose to implement any of the hook
specifications offered by napari.
see: https://napari.org/docs/plugins/hook_specifications.html

Replace code below accordingly.  For complete documentation see:
https://napari.org/docs/plugins/for_plugin_developers.html
"""
import os
import h5py
from napari_plugin_engine import napari_hook_implementation
from .util import read_image, read_table, write_image, write_table

H5_EXTS = ['.hdf', '.hdf5', '.h5']


@napari_hook_implementation
def napari_get_reader(path):
    """A basic implementation of the napari_get_reader hook specification.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are only going to look at the first file.
        path = path[0]

    # if we know we cannot read the file, we immediately return None.
    if not os.path.splitext(path)[1].lower() in H5_EXTS:
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def get_image_edges_and_labels(path, saturation_factor=1.5, edge_width=2, return_seg=False):
    with h5py.File(path, 'r') as f:
        serum = normalize(read_image(f, 'serum_IgG'))
        marker = quantile_normalize(read_image(f, 'marker'))
        nuclei = normalize(read_image(f, 'nuclei'))

        seg = read_image(f, 'cell_segmentation')
        _, infected_labels = read_table(f, 'infected_cell_labels')
        assert len(infected_labels) == seg.max() + 1
        assert infected_labels.shape[1] == 2

    bg_mask = seg == 0

    def subtract_bg(raw):
        bg = np.median(raw[bg_mask])
        raw -= bg
        return raw

    serum = subtract_bg(serum)
    marker = subtract_bg(marker)
    nuclei = subtract_bg(nuclei)

    infected_labels = infected_labels[:, 1]
    edges = get_edge_segmentation(seg, edge_width)

    raw = np.concatenate([marker[..., None], serum[..., None], nuclei[..., None]], axis=-1)
    if saturation_factor > 1:
        raw = skc.rgb2hsv(raw)
        raw[..., 1] *= saturation_factor
        raw = skc.hsv2rgb(raw).clip(0, 1)

    if return_seg:
        return raw, edges, infected_labels, seg
    else:
        return raw, edges, infected_labels


def reader_function(path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of layer.
        Both "meta", and "layer_type" are optional. napari will default to
        layer_type=="image" if not provided
    """
    # can only read a single h5 input file
    if not isinstance(path, str):
        return None

    layers = []

    with h5py.File(path, 'r') as f:
        serum = normalize(read_image(f, 'serum_IgG'))
        marker = quantile_normalize(read_image(f, 'marker'))
        nuclei = normalize(read_image(f, 'nuclei'))

        seg = read_image(f, 'cell_segmentation')
        _, infected_labels = read_table(f, 'infected_cell_labels')
        assert len(infected_labels) == seg.max() + 1
        assert infected_labels.shape[1] == 2

    bg_mask = seg == 0

    def subtract_bg(raw):
        bg = np.median(raw[bg_mask])
        raw -= bg
        return raw

    serum = subtract_bg(serum)
    marker = subtract_bg(marker)
    nuclei = subtract_bg(nuclei)

    infected_labels = infected_labels[:, 1]
    edges = get_edge_segmentation(seg, edge_width)

    raw = np.concatenate([marker[..., None], serum[..., None], nuclei[..., None]], axis=-1)
    if saturation_factor > 1:
        raw = skc.rgb2hsv(raw)
        raw[..., 1] *= saturation_factor
        raw = skc.hsv2rgb(raw).clip(0, 1)

    # optional kwargs for the corresponding viewer.add_* method
    # https://napari.org/docs/api/napari.components.html#module-napari.components.add_layers_mixin
    add_kwargs = {}

    layer_type = "image"  # optional, default is "image"
    return [(data, add_kwargs, layer_type)]

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

from .layers import get_layers_from_file, save_labels


H5_EXTS = ['.hdf', '.hdf5', '.h5']


# NOTE this doesn't work yet, but also doesn'make much sense in this context
@napari_hook_implementation
def napari_get_writer(path, layers):

    print("Hook!")

    ext = os.path.splitext(path)[1]
    if not ext.lower() in H5_EXTS:
        return None

    # make sure we have exactly one labels layer
    if any(layer == 'labels' for layer in layers):
        return save_labels

    return None


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
        layers = get_layers_from_file(f)

    return layers

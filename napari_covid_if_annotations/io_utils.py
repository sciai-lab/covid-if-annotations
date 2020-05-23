import json
import os

import h5py
import numpy as np
import pandas as pd
import skimage.color as skc

from .image_utils import normalize, quantile_normalize, get_centroids, get_edge_segmentation

DEFAULT_CHUNKS = tuple(json.loads(os.environ.get('DEFAULT_CHUNKS', '[256, 256]')))


def get_raw_data(f, saturation_factor):

    serum = normalize(read_image(f, 'serum_IgG'))
    marker = quantile_normalize(read_image(f, 'marker'))
    nuclei = normalize(read_image(f, 'nuclei'))

    seg = read_image(f, 'cell_segmentation')
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


def make_raw_layers(f, saturation_factor):

    raw, marker = get_raw_data(f, saturation_factor)

    raw_kwargs = {'name': 'raw'}
    raw_layer = (raw, raw_kwargs, 'image')

    marker_kwargs = {'name': 'marker', 'visible': False}
    marker_layer = (marker, marker_kwargs, 'image')
    return [raw_layer, marker_layer]


def to_infected_edges(edges, seg_ids, infected_labels):
    infected_edges = np.zeros_like(edges)
    infected_ids = seg_ids[infected_labels == 1]
    control_ids = seg_ids[infected_labels == 2]
    infected_edges[np.isin(edges, infected_ids)] = 1
    infected_edges[np.isin(edges, control_ids)] = 2
    return infected_edges


def get_segmentation_data(f, edge_width):
    seg = read_image(f, 'cell_segmentation')

    _, infected_labels = read_table(f, 'infected_cell_labels')
    assert len(infected_labels) == seg.max() + 1
    assert infected_labels.shape[1] == 2
    infected_labels = infected_labels[:, 1]

    seg_ids = np.unique(seg)
    assert seg_ids.shape == infected_labels.shape, f"{seg_ids.shape}, {infected_labels.shape}"

    edges = get_edge_segmentation(seg, edge_width)
    infected_edges = to_infected_edges(edges, seg_ids, infected_labels)

    centroids = get_centroids(seg)

    return seg, centroids, infected_edges, infected_labels


def make_segmentation_layers(f, edge_width):

    seg, centroids, infected_edges, _ = get_segmentation_data(f, edge_width)

    edges_kwargs = {'name': 'infected-classification', 'visible': False}
    edges_layer = (infected_edges, edges_kwargs, 'labels')

    seg_kwargs = {'name': 'cell-segmentation'}
    seg_layer = (seg, seg_kwargs, 'labels')

    # TODO better name
    center_kwargs = {'name': 'centers'}
    center_layer = (centroids, center_kwargs, 'points')

    return [edges_layer, seg_layer, center_layer]


def get_default_chunks(data):
    chunks = DEFAULT_CHUNKS
    shape = data.shape

    len_diff = len(shape) - len(chunks)
    if len_diff > 0:
        chunks = len_diff * (1,) + chunks
    assert len(chunks) == len(shape)

    chunks = tuple(min(ch, sh) for ch, sh in zip(chunks, shape))
    return chunks


def is_dataset(obj):
    if isinstance(obj, h5py.Dataset):
        return True
    return False


def is_group(obj):
    if isinstance(obj, h5py.Group):
        return True
    return False


# read/write images
def read_image(f, key, scale=0, channel=None):
    ds = f[key]
    if is_group(ds):
        ds = ds['s%i' % scale]
    assert is_dataset(ds)
    data = ds[:] if channel is None else ds[channel]
    return data


def _write_single_scale(g, out_key, image):
    chunks = get_default_chunks(image)
    ds = g.require_dataset(out_key, shape=image.shape, dtype=image.dtype,
                           compression='gzip', chunks=chunks)
    ds[:] = image
    return ds


def write_image(f, name, image, viewer_settings={}):
    g = f.require_group(name)
    _write_single_scale(g, "s0", image)
    assert isinstance(viewer_settings, dict)


def has_image(f, name):
    if name not in f:
        return False
    return 's0' in f[name]


# read/write tables
def read_table(f, name, table_string_type='U100'):
    key = 'tables/%s' % name
    g = f[key]
    ds = g['cells']
    table = ds[:]

    ds = g['columns']
    column_names = [col_name.decode('utf-8') for col_name in ds[:]]

    def _col_dtype(column):
        try:
            column.astype('int')
            return 'int'
        except ValueError:
            pass
        try:
            column.astype('float')
            return 'float'
        except ValueError:
            pass
        return table_string_type

    # find the proper dtypes for the columns and cast
    dtypes = [_col_dtype(col) for col in table.T]
    columns = [col.astype(dtype) for col, dtype in zip(table.T, dtypes)]
    n_rows = table.shape[0]

    table = [[col[row] for col in columns] for row in range(n_rows)]

    # a bit hacky, but we use pandas to handle the mixed dataset
    df = pd.DataFrame(table)
    return column_names, df.values


def write_table(f, name, column_names, table,
                visible=None, force_write=False, table_string_type='S100'):
    if len(column_names) != table.shape[1]:
        raise ValueError(f"Number of columns does not match: {len(column_names)}, {table.shape[1]}")

    # set None to np.nan
    table[np.equal(table, None)] = np.nan

    # make the table datasets. we follow the layout
    # table/cells - contains the data
    # table/columns - containse the column names
    # table/visible - contains which columns are visible in the plate-viewer

    key = 'tables/%s' % name
    g = f.require_group(key)

    def _write_dataset(name, data):
        if name in g:
            shape = g[name].shape
            if shape != data.shape and force_write:
                del g[name]

        ds = g.require_dataset(name, shape=data.shape, dtype=data.dtype,
                               compression='gzip')
        ds[:] = data

    # TODO try varlen string, and if that doesn't work with java,
    # issue a warning if a string is cut
    # cast all values to numpy string
    _write_dataset('cells', table.astype(table_string_type))
    _write_dataset('columns', np.array(column_names, dtype=table_string_type))

    if visible is None:
        visible = np.ones(len(column_names), dtype='uint8')
    _write_dataset('visible', visible)


def has_table(f, name):
    actual_key = 'tables/%s' % name
    if actual_key not in f:
        return False
    g = f[actual_key]
    if not ('cells' in g and 'columns' in g and 'visible' in g):
        return False
    return True

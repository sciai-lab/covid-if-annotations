import json
import os

import h5py
import numpy as np
import pandas as pd

DEFAULT_CHUNKS = tuple(json.loads(os.environ.get('DEFAULT_CHUNKS', '[256, 256]')))


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

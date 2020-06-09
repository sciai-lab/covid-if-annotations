import argparse
import os
import subprocess
import warnings
from glob import glob

import h5py
import napari
import numpy as np
import pandas as pd

from napari_covid_if_annotations.io_utils import read_image, has_table
from napari_covid_if_annotations.layers import (get_centroids,
                                                get_centroid_kwargs,
                                                get_segmentation_data)


def get_file_lists():
    files = subprocess.check_output(['mc', 'ls', 'embl/covid-if/round1']).decode('utf-8')
    files = files.split('\n')
    files = [ff.split()[-1] for ff in files if len(ff.split()) > 1]
    files = [ff for ff in files if ff.endswith('.h5')]

    uploaded_annotations = [ff for ff in files if ff.endswith('annotations.h5')]

    return files, uploaded_annotations


def check_uploads():

    files, uploaded_annotations = get_file_lists()
    checked_files = pd.read_excel('./annotation_status.xlsx')['FileName'].values

    for upload in uploaded_annotations:
        print("Have upload", upload)
        original_file = upload.replace('_annotations.h5', '.h5')
        if original_file not in files:
            print("Could not find the associated original", original_file)

        file_name = os.path.split(original_file)[1]
        if file_name in checked_files:
            print("This file has already been checked")
        else:
            print("This file is new!")
        print()

    print("Found", len(uploaded_annotations), "uploads")


def sync_uploads():
    prefix = 'embl/covid-if/round1'
    out_root = '/g/kreshuk/data/covid/ground-truth/embl-annotations'
    os.makedirs(out_root, exist_ok=True)
    _, uploaded_annotations = get_file_lists()
    checked_files = pd.read_excel('./annotation_status.xlsx')['FileName'].values

    for upload in uploaded_annotations:
        file_name = upload.replace('_annotations.h5', '.h5')
        file_name = os.path.split(file_name)[1]
        if file_name in checked_files:
            continue

        in_path = os.path.join(prefix, upload)
        out_path = os.path.join(out_root, upload)
        cmd = ['mc', 'cp', in_path, out_path]
        subprocess.run(cmd)


def validate_upload(ff, input_root):
    file_name = os.path.split(ff)[1].replace('_annotations', '')
    in_file = os.path.join(input_root, file_name)
    assert os.path.exists(in_file), in_file

    exp_labels = np.array([0, 1, 2, 3])

    with h5py.File(in_file, 'r') as f:
        serum = read_image(f, 'serum_IgG')
        marker = read_image(f, 'marker')

    with h5py.File(ff, 'r') as f:
        seg = read_image(f, 'cell_segmentation')
        if not has_table(f, 'infected_cell_labels'):
            warnings.warn(f"{file_name} does not have labels!")
            return
        (label_ids, centroids,
         _, infected_cell_labels) = get_segmentation_data(f, seg, edge_width=1)

    n_labels = len(infected_cell_labels) - 1
    unique_labels = np.unique(infected_cell_labels)
    if not np.array_equal(unique_labels, exp_labels):
        print("Found unexpected labels for", file_name)
        print(unique_labels)

    print("Check annotations for file:", file_name)

    # print percentage of infected / control / uncertain / unlabeled
    n_unlabeled = (infected_cell_labels == 0).sum() - 1
    frac_unlabeled = float(n_unlabeled) / n_labels
    print("Unlabeled:", n_unlabeled, "/", n_labels, "=", frac_unlabeled, "%")

    n_infected = (infected_cell_labels == 1).sum()
    frac_infected = float(n_infected) / n_labels
    print("infected:", n_infected, "/", n_labels, "=", frac_infected, "%")

    n_control = (infected_cell_labels == 2).sum()
    frac_control = float(n_control) / n_labels
    print("control:", n_control, "/", n_labels, "=", frac_control, "%")

    n_uncertain = (infected_cell_labels == 3).sum()
    frac_uncertain = float(n_uncertain) / n_labels
    print("uncertain:", n_uncertain, "/", n_labels, "=", frac_uncertain, "%")

    # make label mask
    label_mask = np.zeros_like(seg)
    label_mask[np.isin(seg, label_ids[infected_cell_labels == 1])] = 1
    label_mask[np.isin(seg, label_ids[infected_cell_labels == 2])] = 2
    label_mask[np.isin(seg, label_ids[infected_cell_labels == 3])] = 3
    label_mask[np.isin(seg, label_ids[infected_cell_labels == 0])] = 4

    label_mask[seg == 0] = 0

    centroids = get_centroids(seg)
    ckwargs = get_centroid_kwargs(centroids, infected_cell_labels)

    with napari.gui_qt():
        viewer = napari.Viewer(title=file_name)
        viewer.add_image(serum)
        viewer.add_image(marker)
        viewer.add_labels(seg, visible=False)
        viewer.add_labels(label_mask, visible=True)
        # FIXME something with the points is weird ...
        viewer.add_points(centroids, visible=False, **ckwargs)


def validate_uploads():
    input_root = '/g/kreshuk/data/covid/for_annotation/round1'
    annotations_root = '/g/kreshuk/data/covid/ground-truth/embl-annotations'
    files = glob(os.path.join(annotations_root, '*.h5'))
    files.sort()

    for ff in files:
        validate_upload(ff, input_root)


def debug():
    input_root = '/g/kreshuk/data/covid/for_annotation/round1'
    annotations_root = '/g/kreshuk/data/covid/ground-truth/embl-annotations'
    fname = '20200417_132123_311_WellD06_PointD06_0005_ChannelDAPI,WF_GFP,TRITC,WF_Cy5,DIA_Seq0365_annotations.h5'
    path = os.path.join(annotations_root, fname)
    validate_upload(path, input_root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', type=int, default=0)
    parser.add_argument('--sync', type=int, default=0)
    parser.add_argument('--validate', type=int, default=0)
    parser.add_argument('--debug', type=int, default=0)

    args = parser.parse_args()

    if bool(args.check):
        check_uploads()

    if bool(args.sync):
        sync_uploads()

    if bool(args.validate):
        validate_uploads()

    if bool(args.debug):
        debug()

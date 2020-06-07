import argparse
import os
import subprocess
from glob import glob

import h5py


def get_file_lists():
    files = subprocess.check_output(['mc', 'ls', 'embl/covid-if/round1']).decode('utf-8')
    files = files.split('\n')
    files = [ff.split()[-1] for ff in files if len(ff.split()) > 1]
    files = [ff for ff in files if ff.endswith('.h5')]

    uploaded_annotations = [ff for ff in files if ff.endswith('annotations.h5')]

    return files, uploaded_annotations


def check_uploads():

    files, uploaded_annotations = get_file_lists()

    for upload in uploaded_annotations:
        print("Have upload", upload)
        original_file = upload.replace('_annotations.h5', '.h5')
        if original_file not in files:
            print("Could not find the associated original", original_file)

    print()
    print("Found", len(uploaded_annotations), "uploads")


def sync_uploads():
    prefix = 'embl/covid-if/round1'
    out_root = '/g/kreshuk/data/covid/ground-truth/embl-annotations'
    os.makedirs(out_root, exist_ok=True)
    _, uploaded_annotations = get_file_lists()

    for upload in uploaded_annotations:
        in_path = os.path.join(prefix, upload)
        out_path = os.path.join(out_root, upload)
        cmd = ['mc', 'cp', in_path, out_path]
        subprocess.run(cmd)


def validate_uploads():
    import napari
    from napari_covid_if_annotations.io_utils import read_image

    input_root = '/g/kreshuk/data/covid/ground-truth/round1'
    annotations_root = '/g/kreshuk/data/covid/ground-truth/embl-annotations'
    files = glob(os.path.join(annotations_root, '*.h5'))

    # TODO load the infected labels and display them as point layers
    # print percentage of infected / control / uncertain / unlabeled
    for ff in files:

        in_file = os.path.join(input_root, ff.replace('_annotation', ''))
        assert os.path.exists(in_file), in_file

        with h5py.File(in_file, 'r') as f:
            serum = read_image(f, 'serum_IgG')
            marker = read_image(f, 'marker')

        with h5py.File(ff, 'r') as f:
            seg = read_image(f, 'cell_segmentation')

        with napari.gui_qt():
            viewer = napari.Viewer()
            viewer.add_image(serum)
            viewer.add_image(marker)
            viewer.add_labels(seg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', type=int, default=0)
    parser.add_argument('--sync', type=int, default=0)
    parser.add_argument('--validate', type=int, default=0)

    args = parser.parse_args()

    if bool(args.check):
        check_uploads()

    if bool(args.sync):
        sync_uploads()

    if bool(args.validate):
        validate_uploads()

import argparse
import os
import pandas as pd

from napari_covid_if_annotations.launcher.covid_if_annotations import launch_covid_if_annotation_tool


def proofread(data_path, annotation_path):
    assert os.path.exists(data_path), data_path
    assert os.path.exists(annotation_path), annotation_path
    launch_covid_if_annotation_tool(data_path, annotation_path)


def proofread_annotations(table_path, data_root, annotation_root):
    table = pd.read_excel(table_path)
    names = table['FileName'].values
    status = table['Status'].values

    for name, stat in zip(names, status):
        data_path = os.path.join(data_root, name)
        annotation_path = os.path.join(annotation_root,
                                       name.replace('.h5', '_annotations.h5'))
        if stat == 'second_pass':
            print("Proofread:", name)
            proofread(data_path, annotation_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    data_root = '/home/pape/Work/data/covid/for_annotation/round1'
    parser.add_argument('--data_root', default=data_root)

    annotation_root = '/home/pape/Work/data/covid/ground-truth/embl-annotations'
    parser.add_argument('--annotation_root', default=annotation_root)

    table_path = './annotation_status.xlsx'
    args = parser.parse_args()
    proofread_annotations(table_path, args.data_root, args.annotation_root)

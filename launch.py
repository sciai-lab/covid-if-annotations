import argparse
import os
from napari_covid_if_annotations.launcher import launch_covid_if_annotation_tool

# This script and the default path are just for my convenience during the development.
# Eventually, 'launch_covid_if_annotation_tool' should be installed to the environment
# and then this should be used to call the tool.
# Also a stand-alone app would be great for users.

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str,
                    default='/home/pape/Work/data/covid/ground-truth/20200522/gt_image_001.h5')
args = parser.parse_args()

path = args.path
# (make this work for other people)
if not os.path.exists(path):
    print("Cannot find the file", path, "opening the annotation tool without data.")
    print("You can add data by drag and dropping a compatible file.")
    path = None

launch_covid_if_annotation_tool(path)

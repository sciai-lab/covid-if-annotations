import argparse
from napari_covid_if_annotations.launcher import launch_covid_if_annotation_tool

parser = argparse.ArgumentParser()
# I just put the default value here for my convenience, remove this eventually
parser.add_argument('--path', type=str,
                    default='/home/pape/Work/data/covid/ground-truth/20200522/gt_image_001.h5')
args = parser.parse_args()

launch_covid_if_annotation_tool(args.path)

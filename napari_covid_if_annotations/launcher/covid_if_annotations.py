import argparse
import h5py
import napari

from napari_covid_if_annotations.io_utils import get_raw_data, get_segmentation_data


# TODO
# initialize data when called via filehook; need to recompute infected labels
# or somehow preserve it through the filehook call
def initialize_from_layers():
    pass


def initialize_from_file(viewer, path, saturation_factor, edge_width):
    with h5py.File(path, 'r') as f:
        raw, marker = get_raw_data(f, saturation_factor=saturation_factor)
        (seg, centroids,
         infected_edges, infected_labels) = get_segmentation_data(f, edge_width=edge_width)

    viewer.add_image(raw, name='raw')
    viewer.add_image(marker, name='marker', visible=False)

    viewer.add_labels(infected_edges, name='infected-classification', visible=False)
    viewer.add_labels(seg, name='cell-segmentation')

    # TODO better name for the points layer
    viewer.add_points(centroids, name='centers')

    # monkey patch the infected labels to the viewer, because
    # we need it in the gui functions later
    viewer.infected_labels = infected_labels


# should be installed as a script in setup.py
def launch_covid_if_annotation_tool(path=None, saturation_factor=1, edge_width=2):
    """ Launch the Covid IF anootation tool.

    Based on https://github.com/transformify-plugins/segmentify/blob/master/examples/launch.py
    """

    # TODO in addition to providing the path here, it would be great to
    # also support the filehook for drag and drop support.
    # In principle, this works but we would somehow need
    # to trigger 'initialize_from_layers' when the filehook is triggered
    if path is None:
        raise NotImplementedError

    with napari.gui_qt():
        viewer = napari.Viewer()

        if path is not None:
            initialize_from_file(viewer, path,
                                 saturation_factor, edge_width)

        # TODO
        # connect the gui elements


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default=None)
    parser.add_argument('--saturation_factor', type=float, default=1)
    parser.add_argument('--edge_width', type=int, default=2)

    args = parser.parse_args()
    launch_covid_if_annotation_tool(args.path, args.saturation_factor, args.edge_width)

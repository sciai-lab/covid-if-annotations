import argparse
import h5py
import napari

from napari.layers.points import Points
from napari.layers.labels import Labels
from napari.layers.image import Image
from napari_covid_if_annotations.layers import get_layers_from_file
from napari_covid_if_annotations.gui import connect_to_viewer
from napari_covid_if_annotations._key_bindings import modify_points_layer, update_layers


def initialize_from_file(viewer, path, saturation_factor, edge_width):
    with h5py.File(path, 'r') as f:
        layers = get_layers_from_file(f, saturation_factor, edge_width)

    for (data, kwargs, layer_type) in layers:
        adder = getattr(viewer, f'add_{layer_type}')
        adder(data, **kwargs)


def replace_layer(new_layer, layers, name_to_replace, protected_metadata=None):
    for layer in layers:
        if layer.name == name_to_replace:
            if protected_metadata is None:
                new_metadata = new_layer.metadata
            else:
                new_metadata = layer.metadata
                new_metadata.update({k: v for k, v in new_layer.metadata.items()
                                     if k not in protected_metadata})
            layer.data = new_layer.data
            layer.metadata = new_metadata

            if isinstance(layer, Points):
                layer.properties = new_layer.properties

    layers.remove(new_layer.name)


# should be installed as a script in setup.py
def launch_covid_if_annotation_tool(path=None, saturation_factor=1, edge_width=1):
    """ Launch the Covid IF anootation tool.

    Based on https://github.com/transformify-plugins/segmentify/blob/master/examples/launch.py
    """

    with_data = path is not None
    with napari.gui_qt():
        viewer = napari.Viewer()

        # the event object will have the following useful things:
        # event.source -> the full viewer.layers object itself
        # event.item -> the specific layer that cause the change
        # event.type -> a string like 'added', 'removed'
        def on_layer_change(event):
            try:
                needs_update = False
                layers = event.source
                layer = event.item

                def replace_image_layer(name, im_layer):
                    im_layers = [ll for ll in layers if name in ll.name]
                    if name in im_layer.name and len(im_layers) > 1:
                        replace_layer(im_layer, layers, name)

                # replace the raw data image layers
                if isinstance(layer, Image) and event.type == 'added':
                    replace_image_layer('raw', layer)
                    replace_image_layer('virus-marker', layer)
                    replace_image_layer('cell-outlines', layer)

                # if we add new labels or new points, we need to replace instead
                # of adding them
                if isinstance(layer, Labels) and event.type == 'added':
                    if len([ll for ll in layers if isinstance(ll, Labels)]) > 1:
                        replace_layer(layer, layers, 'cell-segmentation')

                if isinstance(layer, Points) and event.type == 'added':
                    if len([ll for ll in layers if isinstance(ll, Points)]) > 1:
                        replace_layer(layer, layers, 'infected-vs-control')

                        # select the new points layer
                        layer = viewer.layers['infected-vs-control']
                        viewer.layers.unselect_all()
                        layer.selected = True
                        needs_update = True

                    # modifty the new points layer
                    # set the corect color maps
                    face_color_cycle_map = {0: (1, 1, 1, 1),
                                            1: (1, 0, 0, 1),
                                            2: (0, 1, 1, 1),
                                            3: (1, 1, 0, 1)}

                    viewer.layers['infected-vs-control'].face_color_cycle_map = face_color_cycle_map
                    viewer.layers['infected-vs-control'].refresh_colors()

                # always modify the points layer to deactivate the buttons we don't need
                if isinstance(event.item, Points):
                    modify_points_layer(viewer)

                if needs_update:
                    update_layers(viewer)

            except AttributeError:
                pass

        viewer.layers.events.changed.connect(on_layer_change)
        if with_data:
            initialize_from_file(viewer, path,
                                 saturation_factor, edge_width)

        # connect the gui elements and modify layer functionality
        connect_to_viewer(viewer)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default=None)
    parser.add_argument('--saturation_factor', type=float, default=1)
    parser.add_argument('--edge_width', type=int, default=1)

    args = parser.parse_args()
    launch_covid_if_annotation_tool(args.path, args.saturation_factor, args.edge_width)


if __name__ == '__main__':
    main()

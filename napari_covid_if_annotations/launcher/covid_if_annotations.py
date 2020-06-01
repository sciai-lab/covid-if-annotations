import argparse
import h5py
import napari

from napari.layers.points import Points
from napari.layers.labels import Labels
from napari_covid_if_annotations.layers import get_layers_from_file
from napari_covid_if_annotations.gui import connect_to_viewer
from napari_covid_if_annotations._key_bindings import next_on_click, modify_points_layer


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
def launch_covid_if_annotation_tool(path=None, saturation_factor=1, edge_width=2):
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
                # if we add new labels or new points, we need to replace instead
                # of adding them
                if isinstance(event.item, Labels) and event.type == 'added':
                    layers = event.source
                    layer = event.item
                    if len([ll for ll in layers if isinstance(ll, Labels)]) > 1:
                        replace_layer(layer, layers, 'cell-segmentation', protected_metadata=['filename'])

                if isinstance(event.item, Points) and event.type == 'added':
                    layers = event.source
                    layer = event.item
                    if len([ll for ll in layers if isinstance(ll, Points)]) > 1:
                        replace_layer(event.item, layers, 'infected-vs-control')

                    # select the new points layer
                    layer = viewer.layers['infected-vs-control']
                    viewer.layers.unselect_all()
                    layer.selected = True

                    # modifty the new points layer
                    viewer.layers['infected-vs-control'].refresh_colors()

                    # add the 'change label on click' functionality to the points layer
                    event.item.mouse_drag_callbacks.append(next_on_click)

                # always modify the points layer to deactivate the buttons we don't need
                if isinstance(event.item, Points):
                    modify_points_layer(viewer)

            except AttributeError:
                pass

        viewer.layers.events.changed.connect(on_layer_change)
        if with_data:
            initialize_from_file(viewer, path,
                                 saturation_factor, edge_width)

        # connect the gui elements and modify layer functionality
        connect_to_viewer(viewer)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default=None)
    parser.add_argument('--saturation_factor', type=float, default=1)
    parser.add_argument('--edge_width', type=int, default=2)

    args = parser.parse_args()
    launch_covid_if_annotation_tool(args.path, args.saturation_factor, args.edge_width)

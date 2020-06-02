import argparse
import os
from glob import glob

import numpy as np
import imageio
from skimage.transform import downscale_local_mean


def copy_image(in_path, out_path):
    im = imageio.imread(in_path)

    scaled = []
    for channel_id in range(im.shape[-1]):
        channel = downscale_local_mean(im[..., channel_id], (2, 2))
        scaled.append(channel[..., None])
    im = np.concatenate(scaled, axis=-1)

    imageio.imwrite(out_path, im)


def sync_images(out_folder):
    input_files = glob('./img/*.png')
    input_names = [os.path.split(path)[1] for path in input_files]

    existing_files = glob(os.path.join(out_folder, '*.png'))
    existing_names = [os.path.split(path)[1] for path in existing_files]

    to_copy = list(set(input_names) - set(existing_names))

    for name in to_copy:
        in_path = os.path.join('./img', name)
        out_path = os.path.join(out_folder, name)
        copy_image(in_path, out_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    default_out = '../embl-annotation-service/images/static/images/img'
    parser.add_argument('--out_folder', type=str, default=default_out)
    args = parser.parse_args()
    sync_images(args.out_folder)

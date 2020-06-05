###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
"""
This script uses py2app to generate an app bundle in "alias mode".
The resulting app is NOT suitable for redistribution, because it won't 
contain any of the python modules needed for the app to run.
(They are all assumed to be available elsewhere on your system.)

However, if your environment is already "relocatable", then you can use the 
"alias mode" app as template for a fully relocatable app.
"""

import sys
import os
from setuptools import setup, find_packages

import napari_covid_if_annotations


if len(sys.argv) < 3 or sys.argv[1] != "py2app" or "--alias" not in sys.argv:
    sys.stderr.write("Usage: python {} py2app --alias ...\n".format(sys.argv[0]))
    sys.exit(1)

COVID_REPO = os.path.normpath(os.path.split(napari_covid_if_annotations.__file__)[0])
APP = ['covid_if_annotations.py']

icon_file = os.path.join(os.path.split(__file__)[0], 'covid-if.icns')
assert os.path.exists(icon_file)

OPTIONS = { 'dist_dir' : os.getcwd(),
            'site_packages' : False,
            'argv_emulation': False, # argv_emulation interferes with gui apps
            'iconfile' : icon_file, 
            'extra_scripts': [os.path.join(COVID_REPO, 'mac_execfile.py')],
            'alias': True }

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    version="0.0.2dev5",
    description='Covid if annotations',
    url='http://github.com/hci-unihd/covid-if-annotations'
)


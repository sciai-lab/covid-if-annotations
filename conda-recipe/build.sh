${PYTHON} -m pip install . -vv

if [ "$(uname)" == "Darwin" ]
then
    cp dev/deployment/osx/mac_execfile.py ${SP_DIR}/napari_covid_if_annotations
fi



set -e
set -x

RELEASE_VERSION=0.0.3dev6

echo "Creating app bundle for covid-if-annotations ${RELEASE_VERSION}"

# run from covid-if-annotations folder

# setup conda
eval "$(conda shell.bash hook)"
conda activate base
CONDA_ROOT=`conda info --root`
source ${CONDA_ROOT}/bin/activate root

RELEASE_ENV=${CONDA_ROOT}/envs/covid-release

# remove old release environment
conda env remove -y -q -n covid-release

echo "Creating new release environment"
conda create -q -y -n covid-release covid-if-annotations=${RELEASE_VERSION} py2app --override-channels -c ilastik-forge -c conda-forge -c defaults
conda activate covid-release

${RELEASE_ENV}/bin/python dev/deployment/osx/setup-alias-app.py py2app --alias --dist-dir .

# proper QT-conf
cat <<EOF > covid_if_annotations.app/Contents/Resources/qt.conf
; Qt Configuration file
[Paths]
Plugins = covid-release/plugins
EOF

# add __main__ for convenience
cat <<EOF > covid_if_annotations.app/Contents/Resources/covid_if_annotations.py
from napari_covid_if_annotations.launcher.covid_if_annotations import main

if __name__ == "__main__":
    main()

EOF

# Moving covid-release environment into covid_if_annotations.app bundle
mv ${RELEASE_ENV} covid_if_annotations.app/Contents/covid-release

# Updating bundle internal paths
# Fix __boot__ script
sed -i '' 's|^_path_inject|#_path_inject|g' covid_if_annotations.app/Contents/Resources/__boot__.py
sed -i '' "s|${CONDA_ROOT}/envs/covid-release/||" covid_if_annotations.app/Contents/Resources/__boot__.py
sed -i '' "s|DEFAULT_SCRIPT=.*|DEFAULT_SCRIPT='covid_if_annotations.py'|" covid_if_annotations.app/Contents/Resources/__boot__.py

# Fix Info.plist
sed -i '' "s|${CONDA_ROOT}/envs/covid-release|@executable_path/../covid-release|" covid_if_annotations.app/Contents/Info.plist
sed -i '' "s|\.dylib|m\.dylib|" covid_if_annotations.app/Contents/Info.plist

# Fix python executable link
rm covid_if_annotations.app/Contents/MacOS/python
cd covid_if_annotations.app/Contents/MacOS && ln -s ../covid-release/bin/python
cd -

# Fix app icon link
rm covid_if_annotations.app/Contents/Resources/covid-if.icns
cp dev/deployment/osx/covid-if.icns covid_if_annotations.app/Contents/Resources

# Replace Resources/lib with a symlink
rm -rf covid_if_annotations.app/Contents/Resources/lib
cd covid_if_annotations.app/Contents/Resources && ln -s ../covid-release/lib
cd -

# Rename app bundle
mv covid_if_annotations.app covid-if-annotations_${RELEASE_VERSION}.app

# tar app bundle
tar -cjf covid-if-annotations_${RELEASE_VERSION}.app.tar.bz2 covid-if-annotations_${RELEASE_VERSION}.app/


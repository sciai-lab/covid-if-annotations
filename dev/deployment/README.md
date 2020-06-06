# Deployment

## Workflow

* bump version via bumpversion
* rebuild conda recipe (per os)
* run deployment (per os), see below for os-specific instructions.

### Windows

Deployment via [conda's constructor](https://github.com/conda/constructor).

Prerequisites: Install constructor in your base environment:

```cmd
conda install -n base -c conda-forge -c defaults constructor
```

Generate an installer by invoking (assuming root directory of this repo):

```cmd
constructor dev\deployment\win
```

### OSX

Deployment via `py2app` in alias mode, as done for ilastik, too.

From repo root:

```bash
./dev/deployment/osx/make-release.sh
```

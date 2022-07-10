#!/bin/bash

_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

DEFAULT_CONDA_PATH="$HOME/opt/anaconda3/etc/profile.d/conda.sh"
PYTHON_VERSION=3.8


function get_conda_path() {
        local conda_exe=$(which conda)
        if [[ -z ${conda_exe} ]]; then
                echo "Fail to detect conda! Have you installed Anaconda/Miniconda?" 1>&2
                exit 1
        fi

        echo "$(dirname ${conda_exe})/../etc/profile.d/conda.sh"
}


function prepare_conda_env() {
        # the conda env name
        local env_name=${1:-seutil}; shift
        # path to conda.sh script; automatically inferred from conda executable path if not provided
        local conda_path=${1:-$(get_conda_path)}; shift

        echo ">>> Preparing conda environment \"${env_name}\", for conda at ${conda_path}"
        
        # Preparation
        set -e
        set -x
        source ${conda_path}
        conda env remove --name $env_name
        conda create --name $env_name python=$PYTHON_VERSION pip -y
        conda activate $env_name

        # Install libraries
        pip install -e .[dev,compat-io]
}


prepare_conda_env "$@"

#!/bin/bash
# prepare a conda environment for developing seutil

_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

function prepare_conda_env() {
        # the python version to use
        local python_version=${1:-3.10}; shift
        # the conda env name
        local env_name=${1:-seutil}; shift
        # if true, install optional dependencies
        local opt_deps=${1:-true}; shift

        echo ">>> Preparing conda environment \"${env_name}\", python_version=${python_version}"
        
        # Preparation
        set -e
        eval "$(conda shell.bash hook)"
        conda env remove --name $env_name -y
        conda create --name $env_name python=$python_version pip -y
        conda activate $env_name
        pip install --upgrade pip

        # Install libraries
        if [ "$opt_deps" = true ]; then
                pip install torch --index-url https://download.pytorch.org/whl/cpu  # prioritize the use of cpu version of pytorch
                pip install -e .[dev,dev-opt]
        else
                pip install -e .[dev]
        fi
}


prepare_conda_env "$@"

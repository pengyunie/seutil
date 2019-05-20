#!/bin/bash

ANACONDA_URL='https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh'

function install_anaconda() {
        local install_dir="$1"; shift; : ${install_dir:=$HOME/opt/anaconda3}

        if [[ -d ${install_dir} ]]; then
                echo "Target directory ${install_dir} not empty!"
                exit 1
        fi

        local temp_dir=$(mktemp -d)
        ( cd ${temp_dir}
          wget $ANACONDA_URL -O anaconda.sh
          chmod +x anaconda.sh
          ./anaconda.sh -b -p ${install_dir}
        )

        rm -rf ${temp_dir}

        echo ""
        echo "========================================"
        echo "Installation complete.  Please add this to your ~/.bashrc:"
        echo "    source \"${install_dir}/etc/profile.d/conda.sh\""
        echo ""
        echo "Then restart this shell so that conda is ready for use."
        echo ""
        echo "To activate conda and use Python 3.7:"
        echo "$ conda activate"
        echo "To deactivate conda and stop using Python 3.7:"
        echo "$ conda deactivate"
        echo ""
}

install_anaconda $@

#!/bin/bash

ANACONDA_URL='https://repo.anaconda.com/archive/Anaconda3-2018.12-Linux-x86_64.sh'

function install_anaconda() {
        local install_dir="$1"; shift; : ${install_dir:=$HOME/opt/anaconda3}

        if [[ -d ${install_dir} ]]; then
                echo "Target directory ${install_dir} not empty!"
                exit 1
        fi

        local temp_dir=$(mktemp -d)
        ( cd ${temp_dir}
          wget $ANACONDA_URL -O anaconda.sh
          ./anaconda.sh
        )

        rm -rf ${temp_dir}
}

install_anaconda $@

#!/bin/bash

if [[ "$(python --version 2>&1)" == "Python 3.7"* ]]; then
        pip install --upgrade seutil
else
        echo "Requires Python 3.7!" 1>&2
        echo "You can install anaconda 3 to use Python 3.7:" 1>&2
        echo "$ ./install_anaconda.sh" 1>&2
fi

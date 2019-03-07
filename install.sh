#!/bin/bash

if [[ "$(python --version 2>&1)" == "Python 3.7"* ]]; then
        pip install --upgrade seutil
else
        echo "Requires Python 3.7!" 1>&2
fi

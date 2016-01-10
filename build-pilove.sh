#!/bin/bash
#
#  Builds the Pilove bootable image from scratch.
#

logfile=build.log

echo "Building PiLove - follow progress at $logfile..."
python -u pilove.py > $logfile 2>&1

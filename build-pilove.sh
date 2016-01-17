#!/bin/bash
#
#  Builds the Pilove bootable image from scratch.
#

xsysroot_profile=$1
if [ "$xsysroot_profile" == "" ]; then
    xsysroot_profile="pilove"
fi

logfile=build.log

echo "Building PiLove - follow progress at $logfile..."
python -u pilove.py $xsysroot_profile > $logfile 2>&1

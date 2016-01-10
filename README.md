## PiLove

Welcome to PiLove!

This project builds a RaspberryPI bootable image, based on Raspbian Jessie, running the wonderful Löve2D version 0.10.0 game framework.

## Requirements

You need an Intel based system with the QEmu emulator, NBD driver, and [xsysroot](https://github.com/skarbat/xsysroot) tools installed.

Copy the file `xsysroot.conf` into your home directory, and download the latest pipaOS image referred to within the file.

## Build

Run the script `build-pilove.sh` and sit back. The image file along with the SDL2 and Löve binaries will appear on your current directory.

#!/bin/bash
#
#  The MIT License (MIT)
#
#  Copyright (c) 2016 Albert Casals - albert@mitako.eu
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#
#  build-love2d.sh
#
#  Script to run on the RaspberryPI which downloads, builds and installs the Love2d framework.
#
#  Invoke with "--sdl-only" to simply build the SDL2 library.
#

# System jail protection code
ARM_MUST_BE='armv7l'
mach=`uname -m`
if [ "$mach" != "$ARM_MUST_BE" ]; then
    echo "Careful! Looks like I am not running inside an ARM system!"
    echo "uname -m is telling me: $mach"
    exit 1
else
    # Avoid errors from stopping the script
    set +e
fi

# pass this string as the first argument to fast-build sdl2
sdlonly="--sdl-only"

# Install dependencies
echo ">>> Installing dependencies"
PKGS="build-essential devscripts pkg-config git-core debhelper dh-autoreconf

libasound2-dev libudev0 libudev-dev libdbus-1-dev libx11-dev libxcursor-dev
libxext-dev libxi-dev libxinerama-dev libxrandr-dev libxss-dev libxt-dev libxxf86vm-dev
libfreetype6-dev libopenal-dev libmodplug-dev libvorbis-dev
libgl1-mesa-dev libpulse-dev libibus-1.0-dev

libtheora-dev libphysfs-dev libluajit-5.1-dev libmpg123-dev
libraspberrypi-dev
pulseaudio
"

if [ "$1" != "$sdlonly" ]; then
    apt-get update
    apt-get install -y --no-install-recommends $PKGS
    if [ "$?" != "0" ]; then
	echo ">>> ERROR: Installing dependencies"
	exit 1
    fi
fi

# Build SDL
cd /tmp
sdl2_dir="sdl2.0.4"
if [ ! -d "$sdl2_dir" ]; then
    echo ">>> Getting SDL2 sources"
    git clone https://github.com/spurious/SDL-mirror.git $sdl2_dir
fi
cd $sdl2_dir

echo ">>> Building SDL2"
export CFLAGS="-I/opt/vc/include -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux"
export LDFLAGS="-L/opt/vc/lib"

# HACK: the rules file pass special options to configure (--host and others)
cp -fv ../debian-rules-sdl2 ./debian/rules

#./configure --host=arm-raspberry-linux-gnueabihf --disable-pulseaudio --disable-esd --disable-video-mir --disable-video-wayland
#make
#make install

dpkg-buildpackage
if [ "$?" != "0" ]; then
    echo ">>> ERROR: Could not build SDL2 libraries"
    exit 1
else
    echo ">>> Installing SDL2 libraries"
    cd /tmp
    dpkg -i libsdl2_2.0.4_armhf.deb
    dpkg -i libsdl2-dev_2.0.4_armhf.deb
fi

# stop if only SDL was required
if [ "$1" == "$sdlonly" ]; then
    echo "SDL2 built - terminating due to $sdlonly"
    exit 0
fi

# Build Love2d
echo ">>> Building Love2D"
love2d_url="https://bitbucket.org/rude/love/downloads/love-0.10.0-linux-src.tar.gz"
love2d_tgz="lovesrc.tgz"
love2d_bin="/tmp/pilove-0.10.0-bin.tgz"

cd /tmp
curl -L $love2d_url > $love2d_tgz
cd /usr/local/games
tar zxf /tmp/$love2d_tgz
cd love-0.10.0
./configure
if [ "$?" != "0" ]; then
    echo ">>> Error: running Love2D configure rc=$?"
    exit 1
fi
make -j 2
if [ "$?" != "0" ]; then
    echo ">>> Error: running Love2D make rc=$?"
    exit 1
fi
cd ..
tar -zcf $love2d_bin love-0.10.0
echo ">>> Love2D build completed"

# Raspi2png is a tool to take screenshots
echo ">>> Building Raspi2png"
cd /tmp
git clone https://github.com/AndrewFromMelbourne/raspi2png.git
cd raspi2png
make
if [ "$?" != "0" ]; then
    echo "Warning: error building raspi2png"
else
    cp -fv raspi2png /usr/local/bin
    echo ">>> Raspi2png built"
fi

exit 0

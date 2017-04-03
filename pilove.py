#!/usr/bin/env python
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
#  pilove.py
#
#  Program that builds the PiLove OS image for the Raspberry PI.
#
#  You need to download and setup xsysroot to run this script, see README for details.
#

import os
import sys
import time
import xsysroot

# Release version of PiLove
__version__='0.4'


def test_image(pilove):

    count_failed=0
    tests = [
        { 'cmd' : '/usr/local/games/love-0.10.2/src/love --version', 'msg': 'Love app does not load' },
        { 'cmd' : 'raspi2png --help', 'msg': 'Raspi2png could not be found' },
        { 'cmd' : 'dpkg -l | grep libsdl2:armhf', 'msg': 'libSDL2 did not install' },
        { 'cmd' : 'luarocks list | grep lua-periphery', 'msg': 'LUA periphery did not install' },
        { 'cmd' : 'luarocks list | grep rpi-gpio', 'msg': 'LUA RPi GPIO did not install' },
        { 'cmd' : 'emacs --version', 'msg': 'Emacs did not install' },
        { 'cmd' : 'find /usr/share/fonts/truetype/isabella', 'msg': 'Isabella fonts not installed' },
        { 'cmd' : 'find /usr/share/fonts/truetype/fonts-georgewilliams', 'msg': 'GeorgeWilliams fonts not installed' }
        ]

    print '>>> RUNNIG TESTS'
    for test in tests:
        rc=pilove.execute(test['cmd'])
        if rc:
            print '>>> TEST FAILED: {}'.format(test['msg'])
            count_failed += 1
        else:
            print '>>> TEST PASSED'

    if count_failed:
        print '>>> {} TESTS FAILED'.format(count_failed)
    else:
        print '>>> ALL TESTS PASSED!'

    return count_failed


if __name__ == '__main__':

    output_image='pilove-{}.img'.format(__version__)
    prepare_only=False

    # Xsysroot profile name that holds the original pipaOS image
    # (See the file xsysroot.conf for details)
    if len(sys.argv) < 2:
        print 'Please specify a xsysroot profile name'
        sys.exit(1)
    else:
        xsysroot_profile_name=sys.argv[1]

    # Find and activate the xsysroot profile
    try:
        pilove=xsysroot.XSysroot(profile=xsysroot_profile_name)
    except:
        print 'You need to create a Xsysroot Pilove profile'
        print 'Please see the README file'
        sys.exit(1)

    # start timer
    time_start=time.time()

    # make sure the image is not mounted, or not currently in use
    if pilove.is_mounted():
        if not pilove.umount():
            sys.exit(1)

    # renew the image so we start from scratch
    if not pilove.renew():
        sys.exit(1)
    else:
        # once renewed, expand it to grow in size
        pilove.umount()
        if not pilove.expand():
            print 'error expanding image size to {}'.format(pilove.query('qcow_size'))
            sys.exit(1)
        else:
            pilove.mount()

    # baptize the pilove version
    pilove.edfile('/etc/pilove_version', 'pilove v{} - {}'.format(__version__, time.ctime()))

    # set the system hostname
    pilove_hostname='pilove'
    pilove_hosts_file='/etc/hosts'
    pilove.edfile('/etc/hostname', pilove_hostname)
    pilove.edfile(pilove_hosts_file, '127.0.0.1 localhost')
    pilove.edfile(pilove_hosts_file, '127.0.0.1 {}'.format(pilove_hostname), append=True)

    # firmware config.txt with any special settings to smooth Love2D on the RPi
    src_config_txt='config.txt'
    dst_config_txt=os.path.join(pilove.query('sysboot'), src_config_txt)
    rc=os.system('sudo cp -fv {} {}'.format(src_config_txt, dst_config_txt))
    if rc:
        print 'WARNING: could not copy config.txt rc={}'.format(rc)

    # custom kernel boot parameters
    src_cmdline='cmdline.txt'
    dst_cmdline=os.path.join(pilove.query('sysboot'), src_cmdline)
    rc=os.system('sudo cp -fv {} {}'.format(src_cmdline, dst_cmdline))
    if rc:
        print 'WARNING: could not copy cmdline rc={}'.format(rc)

    # make the Pilove installation script available in the image through /tmp
    src_install_script='build-love2d.sh'
    dst_install_script=os.path.join(pilove.query('tmp'), src_install_script)
    print 'Copying Pilove installation script {} -> {}'.format(src_install_script, dst_install_script)
    rc=os.system('cp {} {}'.format(src_install_script, dst_install_script))
    if rc:
        print 'ERROR: could not copy love build script in the image rc={}'.format(rc)
        sys.exit(1)

    # HACK : this is the custom debian rules file to build SDL2 with RPi support
    rc=os.system('cp {} {}'.format('SDL2/sdl2-debian-rules', pilove.query('tmp')))
    rc=os.system('cp {} {}'.format('SDL2/sdl2-changelog', pilove.query('tmp')))

    # run the Love2D build script
    rc=pilove.execute('/bin/bash -c "cd /tmp ; ./{}"'.format(src_install_script))
    if rc:
        print 'ERROR: pilove installation script failed rc={}'.format(rc)
        sys.exit(1)

    # extract SDL2 and Loved2D built binaries from the image
    rc=os.system('cp {}/libsdl2*deb . '.format(os.path.join(pilove.query('tmp'))))
    rc=os.system('cp {}/pilove*bin.tgz . '.format(os.path.join(pilove.query('tmp'))))

    # start Love2D during boot, and enable sound
    rclocal='/etc/rc.local'
    pilove.edfile(rclocal, '#!/bin/bash')
    pilove.edfile(rclocal, 'pulseaudio --start', append=True)
    pilove.edfile(rclocal, '/usr/local/bin/love &', append=True)
    pilove.edfile(rclocal, 'exit 0', append=True)
    rc=pilove.execute('chmod +x {}'.format(rclocal))

    # create a symlink to reach love
    rc=pilove.execute('ln -sfv {} {}'.format('/usr/local/games/love-0.10.2/src/love', '/usr/local/bin/love'))

    # Install emacs with LUA syntax mode, and additional free TrueType fonts
    ttf_packages='fontconfig fonts-isabella fonts-georgewilliams fonts-linuxlibertine'
    pilove.execute('apt-get install -y --no-install-recommends emacs24-nox lua-mode luarocks {}'.format(ttf_packages))

    # Install lua rocks to access the GPIO
    pilove.execute('luarocks install lua-periphery')
    pilove.execute('luarocks install rpi-gpio')

    # run some basic tests on the image
    test_image(pilove)

    # unmount the image
    if not pilove.umount():
        print 'WARNING: Image is busy, most likely installation left some running processes, skipping conversion'
        sys.exit(1)
    else:
        pilove.zerofree(verbose=False)

    # Convert the xsysroot image to a raw format ready to flash and boot
    qcow_image=pilove.query('qcow_image')
    print 'Converting image {}...'.format(qcow_image)
    if os.path.isfile(output_image):
        os.unlink(output_image)

    rc = os.system('qemu-img convert {} {}'.format(qcow_image, output_image))

    time_end=time.time()
    print 'Process finished in {} secs - image ready at {}'.format(time_end - time_start, output_image)
    sys.exit(0)

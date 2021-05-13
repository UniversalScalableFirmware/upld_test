#!/usr/bin/env python
## @ sbl_upld.py
#
# Copyright (c) 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
##

import os
import sys
import struct
from   ctypes import Structure, c_char, c_uint32, c_uint8, c_uint64, c_uint16, sizeof, ARRAY
from   test_base import *

def get_check_lines (pld_name):

    if pld_name.startswith('uboot'):
        name = 'u-boot'
    elif pld_name.startswith('uefi'):
        name = 'UEFI'
    elif pld_name.startswith('linux'):
        name = 'Linux'
    else:
        name = 'unknown'

    lines = [
              "===== Intel Slim Bootloader STAGE1A =====",
              "===== Intel Slim Bootloader STAGE1B =====",
              "===== Intel Slim Bootloader STAGE2 ======",
              "Univeral Payload %s" % name,
              "Jump to payload",
            ]

    if pld_name.startswith('uboot'):
        lines.extend([
              "U-Boot ",
              "Hit any key to stop autoboot:",
              "=>",
              ])

    if pld_name.startswith('uefi'):
        lines.extend([
              "[Bds]Booting UEFI Shell",
              "UEFI v2.70 (EDK II, 0x00010000)"
              ])

    if pld_name.startswith('linux'):
        lines.extend([
              "Run /init as init process",
              ])

    return lines

def usage():
    print("usage:\n  python %s bios_image os_image_dir\n" % sys.argv[0])
    print("  bios_image  :  QEMU Slim Bootloader firmware image.")
    print("                 This image can be generated through the normal Slim Bootloader build process.")
    print("  os_image_dir:  Directory containing bootable OS image.")
    print("                 This image can be generated using GenContainer.py tool.")
    print("")


def main():
    if sys.version_info.major < 3:
        print ("This script needs Python3 !")
        return -1

    if len(sys.argv) != 4:
        usage()
        return -2

    bios_img = sys.argv[1]
    os_dir   = sys.argv[2]
    pld_name = sys.argv[3]

    print("Universal Payload boot test for Slim BootLoader")

    # run QEMU boot with timeout
    output = []
    lines = run_qemu(bios_img, os_dir, timeout = 8)
    output.extend(lines)

    # check test result
    ret = check_result (output, get_check_lines(pld_name))

    print ('\nBoot test %s !\n' % ('PASSED' if ret == 0 else 'FAILED'))

    return ret

if __name__ == '__main__':
    sys.exit(main())

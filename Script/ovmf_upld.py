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

    lines = [
              "Install PPI: 8C8CE578-8A3D-4F1C-9935-896185C32DD3",
              "Total temporary memory:",
              "DXE IPL Entry",
              "[Bds] Entry...",
              "[Bds]Exit the waiting!",
              "UEFI v2.70"
            ]

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

    print("Universal Payload boot test for OVMF")

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

#!/usr/bin/env python3
## @ upld_swap.py
#
# This script swaps extended payload in SBL
#
# Copyright (c) 2021, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
##


import os
import sys
import glob
import threading
import platform
import argparse
import hashlib
import subprocess
from   shutil import copy

script_dir = os.path.dirname(__file__)
tool_dir   = script_dir + '/../SlimBoot/BootloaderCorePkg/Tools'
sys.path.insert(0, tool_dir)
from CommonUtility import *
from BuildUtility  import gen_hash_file, HashStoreData, HashStoreTable


def swap_payload (args):

    if 'SBL_KEY_DIR' not in os.environ:
        os.environ['SBL_KEY_DIR'] = "SblKeys/"

    out_dir  = 'Outputs'

    if os.name == 'nt':
        if os.path.exists (os.path.join (script_dir, 'LzmaCompress.exe')):
            compress_tool_dir = script_dir
        else:
            compress_tool_dir = os.path.realpath (os.path.join (script_dir, '../SlimBoot/BaseTools/Bin/Win32'))
    else:
        if os.path.exists (os.path.join (script_dir, 'LzmaCompress')):
            compress_tool_dir = script_dir
        else:
            compress_tool_dir = os.path.realpath (os.path.join (script_dir, '../SlimBoot/BaseTools/BinWrappers/PosixLike'))

    # create output dir
    if not os.path.exists(args.out_dir):
        os.mkdir (args.out_dir)

    new_ifwi =  os.path.join (args.out_dir, os.path.basename(args.ifwi_image))
    shutil.copyfile (args.ifwi_image, new_ifwi)

    print ('\nSwap payload')
    print ('============================')

    layout = [
      "( 'EPLD', 'EPLD.bin'      , 'NORMAL'  , 'RSA3072_PSS_SHA2_384'  , 'KEY_ID_CONTAINER_RSA3072'      , 0x10      , 0         , 0x0       ),"
      "( 'UPLD', '%s'  , 'Lzma'  , 'SHA2_384'              , ''                              , 0x10      , 0         , 0x0       )," % args.payload_bin
    ]

    gen_file_from_object ( out_dir + '/EPLD.txt', '\n'.join(layout).encode())

    print ('\nCreating new EPLD with %s ...' % args.payload_bin)
    cmd = ['python', tool_dir + '/GenContainer.py', 'create', '-l', out_dir + '/EPLD.txt', '-td', compress_tool_dir, '-o', out_dir]
    run_process (cmd)

    print ('\nSwapping EPLD ...')
    cmd = ['python', tool_dir + '/IfwiUtility.py', 'replace', '-f', out_dir + '/EPLD.bin', '-p', 'IFWI/BIOS/NRD/EPLD', '-i', new_ifwi]
    run_process (cmd)

    print ('\nPayload has been swapped successfully !')
    print ('New IFWI image is generated at:')
    print ('  %s' % os.path.realpath(new_ifwi))


def main():
    parser     = argparse.ArgumentParser()
    parser.add_argument('-i',  '--ifwi'   , dest='ifwi_image',  type=str, help='IFWI image binary file path', required = True)
    parser.add_argument('-p',  '--pldbin' , dest='payload_bin', type=str, help='Payload binary file path',  required = True)
    parser.add_argument('-n',  '--non-redundant' , dest='non_redundant', action="store_true", help='Non-redundant flash map layout')
    parser.add_argument('-o',  '--outdir' , dest='out_dir',     type=str, help='Output directory path', default = 'Out')
    parser.set_defaults(func=swap_payload)

    # Parse arguments and run sub-command
    args = parser.parse_args()
    try:
        func = args.func
    except AttributeError:
        parser.error("too few arguments")

    func(args)


if __name__ == '__main__':
    main()

## @file
# This file is used to provide testing for universal payload.
#
#  Copyright (c) 2021, Intel Corporation. All rights reserved.<BR>
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import sys
import shutil
import subprocess
import fnmatch
import argparse

def fatal (msg):
    sys.stdout.flush()
    raise Exception (msg)

def run_process (arg_list, print_cmd = False, capture_out = False):
    sys.stdout.flush()
    if os.name == 'nt' and os.path.splitext(arg_list[0])[1] == '' and \
       os.path.exists (arg_list[0] + '.exe'):
        arg_list[0] += '.exe'
    if print_cmd:
        print (' '.join(arg_list))

    exc    = None
    result = 0
    output = ''
    try:
        if capture_out:
            output = subprocess.check_output(arg_list, cwd = cwd).decode()
        else:
            result = subprocess.call (arg_list)
    except Exception as ex:
        result = 1
        exc    = ex

    if result:
        if not print_cmd:
            print ('Error in running process:\n  %s' % ' '.join(arg_list))
        if exc is None:
            sys.exit(1)
        else:
            raise exc

    return output

def clone_repo (clone_dir, repo, branch):
    if not os.path.exists(clone_dir + '/.git'):
        print ('Cloning the repo ... %s' % repo)
        cmd = 'git clone %s %s' % (repo, clone_dir)
        ret = subprocess.call(cmd.split(' '))
        if ret:
            fatal ('Failed to clone repo to directory %s !' % clone_dir)
        print ('Done\n')

        print ('Checking out specified branch ... %s' % branch)

        cmd = 'git checkout %s -f' % branch
        ret = subprocess.call(cmd.split(' '), cwd=clone_dir)
        if ret:
            fatal ('Failed to check out specified branch !')
        print ('Done\n')

    else:
        print ('Update the repo ...')
        cmd = 'git fetch origin'
        ret = subprocess.call(cmd.split(' '), cwd=clone_dir)
        if ret:
            fatal ('Failed to update repo in directory %s !' % clone_dir)
        print ('Done\n')

        cmd = 'git reset --hard origin/%s' % branch


    cmd = 'git submodule init'
    ret = subprocess.call(cmd.split(' '), cwd=clone_dir)
    if ret:
        fatal ('Failed to init submodules !')
    print ('Done\n')

    cmd = 'git submodule update'
    ret = subprocess.call(cmd.split(' '), cwd=clone_dir)
    if ret:
        fatal ('Failed to update submodules !')
    print ('Done\n')

    print ('Done\n')

def qemu_test (test_pat, dir_dict):

    if 'SBL_KEY_DIR' not in os.environ:
        os.environ['SBL_KEY_DIR'] = "SblKeys/"

    # check QEMU SlimBootloader.bin
    ovmf_img = '%s/Build/OvmfPol/DEBUG_VS2019/FV/OVMF.fd' % dir_dict['uefi_dir']
    sbl_img  = '%s/Outputs/qemu/SlimBootloader.bin' % dir_dict['sbl_dir']

    disk_dir = 'Disk'
    out_dir  = 'Outputs'
    if not os.path.exists(disk_dir):
        os.mkdir(disk_dir)

    # run test cases
    test_cases = [
      ('ovmf_upld.py',  [ovmf_img, disk_dir, 'uefi_64'],  'UefiPld_64.elf'),
      ('sbl_upld.py',   [sbl_img,  disk_dir, 'uefi_64'],  'UefiPld_64.elf'),
      ('sbl_upld.py',   [sbl_img,  disk_dir, 'linux_64'], 'LinuxPld_64.elf'),
    ]

    test_cnt = 0
    for test_file, test_args, upld_img in test_cases:
        loc_args = list(test_args)
        if test_pat:
            filtered = fnmatch.filter([upld_img.lower()], test_pat)
            if len(filtered) == 0:
                continue

        print ('######### Running run test %s' % test_file)
        if 'slimboot' in loc_args[0].lower():
            # create new IFWI using the upld
            cmd = [ sys.executable, 'Script/upld_swap.py', '-i', sbl_img, '-p', 'Outputs/%s' % upld_img, '-o', out_dir]
            run_process (cmd)
            tst_img  = '%s/SlimBootloader.bin' % dir_dict['out_dir']
        else:
            tst_img  = '%s/Ovmf.bin' % dir_dict['out_dir']
            shutil.copyfile (ovmf_img, tst_img)
        loc_args[0] = tst_img

        # run QEMU test cases
        cmd = [ sys.executable, 'Script/%s' % test_file] + loc_args
        try:
            output = subprocess.run (cmd)
            output.check_returncode()
        except subprocess.CalledProcessError:
            print ('Failed to run test %s !' % test_file)
            return -3
        print ('######### Completed test %s\n\n' % test_file)
        test_cnt += 1

    print ('\nAll %d test cases passed !\n' % test_cnt)

    return 0


def build_uefi_images (dir_dict):
    out_dir  = dir_dict['out_dir']
    uefi_dir = dir_dict['uefi_dir']
    clone_repo  (uefi_dir, 'https://github.com/universalpayload/edk2.git', 'for_upstream_test')

    # Build UEFI
    os.chdir(uefi_dir)
    cmd = 'build_qemu_pol.bat'
    run_process (cmd.split(' '))
    os.chdir('..')
    entry = '%s\\Build\\UefiPayloadPkgX64\\DEBUG_CLANGDWARF\\X64\\UefiPayloadPkg\\UefiPayloadEntry\\UniversalPayloadEntry\\DEBUG\\UniversalPayloadEntry.elf' % uefi_dir
    shutil.copyfile(entry, '%s\\UefiPld_64.elf' % out_dir)

    return 0


def build_sbl_images (dir_dict):
    out_dir = dir_dict['out_dir']
    sbl_dir = dir_dict['sbl_dir']

    clone_repo  (sbl_dir, 'https://github.com/universalpayload/slimbootloader.git', 'universal_payload')
    shutil.copy ('QemuFspBins/Fsp.bsf', '%s/Silicon/QemuSocPkg/FspBin/Fsp.bsf' % sbl_dir)
    shutil.copy ('QemuFspBins/FspRel.bin', '%s/Silicon/QemuSocPkg/FspBin/FspRel.bin' % sbl_dir)

    # Build SBL
    shutil.copy ('QemuFspBins/FspRel.bin', '%s/Silicon/QemuSocPkg/FspBin/FspRel.bin' % sbl_dir)
    cmd = 'python BuildLoader.py build qemu -k'
    ret = subprocess.call(cmd.split(' '), cwd=sbl_dir)
    if ret:
        fatal ('Failed to build SBL!')

    return 0


def build_linux_images (dir_dict):
    out_dir = dir_dict['out_dir']
    sbl_dir = dir_dict['sbl_dir']
    objcopy = dir_dict['objcopy_path']

    # Build Linux Payload 32
    cmd = 'python BuildLoader.py build_dsc -p UniversalPayloadPkg/UniversalPayloadPkg.dsc -a x64 -t clangdwarf'
    ret = subprocess.call(cmd.split(' '), cwd=sbl_dir)
    if ret:
        fatal ('Failed to build Linux Payload x64!')
    shutil.copy ('%s/Build/UniversalPayloadPkg/DEBUG_CLANGDWARF/X64/UniversalPayloadPkg/LinuxLoaderStub/LinuxLoaderStub/DEBUG/LinuxLoaderStub.dll' % sbl_dir, '%s/LinuxPld_64.elf' % out_dir)

    # Inject sections
    cmd = 'python Script/upld_info.py %s/upld_info.bin Linux64' % out_dir
    run_process (cmd.split(' '))
    cmd = objcopy + " -I elf64-x86-64 -O elf64-x86-64 --add-section .upld.initrd=LinuxBins/initrd --add-section .upld.cmdline=LinuxBins/config.cfg --add-section .upld.kernel=LinuxBins/vmlinuz --add-section .upld_info=%s/upld_info.bin %s/LinuxPld_64.elf" % (out_dir, out_dir)
    run_process (cmd.split(' '))
    cmd = objcopy + " -I elf64-x86-64 -O elf64-x86-64 --set-section-alignment .upld.kernel=256 --set-section-alignment .upld.initrd=4096 --set-section-alignment .upld.cmdline=16 --set-section-alignment .upld.info=16 %s/LinuxPld_64.elf" % (out_dir)
    run_process (cmd.split(' '))

    return 0

def get_objcopy():
    if os.name == 'nt':
        return "C:\\Program Files\\LLVM\\bin\\llvm-objcopy.exe"
    else:
        return "objcopy"

def main ():
    dir_dict = {
                  'out_dir'      : 'Outputs',
                  'sbl_dir'      : 'SlimBoot',
                  'uefi_dir'     : 'UefiPayload',
                  'objcopy_path' : get_objcopy()
               }

    arg_parse  = argparse.ArgumentParser()
    arg_parse.add_argument('-sb',  dest='skip_build', action='store_true', help='Specify name pattern for payloads to be built')
    arg_parse.add_argument('-b',   dest='build',  choices=['all', 'uefi', 'sbl', 'linux'], default='all', help='Build specific target')
    arg_parse.add_argument('-t',   dest='test',  type=str, default = '', help='Specify name pattern for payloads to be tested')
    args = arg_parse.parse_args()

    if os.name != 'nt':
        fatal ('Only Windows is supported!')

    if not os.path.exists(dir_dict['out_dir']):
        os.mkdir(dir_dict['out_dir'])

    if not args.skip_build:
        if args.build in ['all', 'uefi']:
            if build_uefi_images (dir_dict):
                return -1

        if args.build in ['all', 'sbl']:
            if build_sbl_images (dir_dict):
                return -2

        if args.build in ['all', 'linux']:
            if build_linux_images (dir_dict):
                return -3

    if args.test not in ['none']:
        if qemu_test (args.test, dir_dict):
            return -10

    return 0

if __name__ == '__main__':
    sys.exit(main())

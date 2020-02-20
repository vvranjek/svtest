#!/usr/bin/env python
# Copyright (c) 2014 Wladimir J. van der Laan
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
'''
A script to check that the (Linux) executables produced by gitian only contain
allowed gcc, glibc and libstdc++ version symbols.  This makes sure they are
still compatible with the minimum supported Linux distribution versions.

Example usage:

    find ../gitian-builder/build -type f -executable | xargs python contrib/devtools/symbol-check.py
'''
from __future__ import division, print_function, unicode_literals
import subprocess
import re
import sys
import os

# Debian 8.11 (Jessie) has:
#
# - g++ version 4.9.2 (https://packages.debian.org/search?suite=default&section=all&arch=any&searchon=names&keywords=g%2B%2B)
# - libc version 2.19.18 (https://packages.debian.org/search?suite=default&section=all&arch=any&searchon=names&keywords=libc6)
# - libstdc++ version 4.8.4 (https://packages.debian.org/search?suite=default&section=all&arch=any&searchon=names&keywords=libstdc%2B%2B6)
#
# Ubuntu 14.04 (Trusty Tahr) has:
#
# - g++ version 4.8.2 (https://packages.ubuntu.com/search?suite=trusty&section=all&arch=any&keywords=g%2B%2B&searchon=names)
# - libc version 2.19.0 (https://packages.ubuntu.com/search?suite=trusty&section=all&arch=any&keywords=libc6&searchon=names)
# - libstdc++ version 4.8.2 (https://packages.ubuntu.com/search?suite=trusty&section=all&arch=any&keywords=libstdc%2B%2B&searchon=names)
#
# Taking the minimum of these as our target.
#
# According to GNU ABI document (http://gcc.gnu.org/onlinedocs/libstdc++/manual/abi.html) this corresponds to:
#   GCC 4.8.0: GCC_4.8.0
#   GCC 4.8.0: GLIBCXX_3.4.18, CXXABI_1.3.7
#   (glibc)    GLIBC_2_19
#
MAX_VERSIONS = {
    'GCC':          (4,8,0),
    'CXXABI':       (1,3,7),
    'GLIBCXX':      (3,4,18),
    'GLIBC':        (2,19),
    'LIBATOMIC':    (1,0)
}
# See here for a description of _IO_stdin_used:
# https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=634261#109

# Ignore symbols that are exported as part of every executable
IGNORE_EXPORTS = {
    '_edata', '_end', '__end__', '_init', '__bss_start', '__bss_start__', '_bss_end__', '__bss_end__', '_fini', '_IO_stdin_used', 'stdin', 'stdout', 'stderr',
    # Figure out why we get these symbols exported on xenial.
    '_ZNKSt5ctypeIcE8do_widenEc', 'in6addr_any', 'optarg',
    '_ZNSt16_Sp_counted_baseILN9__gnu_cxx12_Lock_policyE2EE10_M_destroyEv'
}
READELF_CMD = os.getenv('READELF', '/usr/bin/readelf')
CPPFILT_CMD = os.getenv('CPPFILT', '/usr/bin/c++filt')
# Allowed NEEDED libraries
ALLOWED_LIBRARIES = {
    # bitcoind
    'libgcc_s.so.1',  # GCC base support
    'libc.so.6',  # C library
    'libpthread.so.0',  # threading
    'libanl.so.1',  # DNS resolve
    'libm.so.6',  # math library
    'librt.so.1',  # real-time (clock)
    'libatomic.so.1',
    'ld-linux-x86-64.so.2',  # 64-bit dynamic linker
    'ld-linux.so.2',  # 32-bit dynamic linker
    'ld-linux-aarch64.so.1', # 64-bit ARM dynamic linker
    'ld-linux-armhf.so.3', # 32-bit ARM dynamic linker
    'ld-linux-riscv64-lp64d.so.1', # 64-bit RISC-V dynamic linker
}

ARCH_MIN_GLIBC_VER = {
'80386':  (2,1),
'X86-64': (2,2,5),
'ARM':    (2,4),
'AArch64':(2,17),
'RISC-V': (2,27)
}

class CPPFilt(object):
    '''
    Demangle C++ symbol names.

    Use a pipe to the 'c++filt' command.
    '''

    def __init__(self):
        self.proc = subprocess.Popen(
            CPPFILT_CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

    def __call__(self, mangled):
        self.proc.stdin.write(mangled + '\n')
        self.proc.stdin.flush()
        return self.proc.stdout.readline().rstrip()

    def close(self):
        self.proc.stdin.close()
        self.proc.stdout.close()
        self.proc.wait()


def read_symbols(executable, imports=True):
    '''
    Parse an ELF executable and return a list of (symbol,version) tuples
    for dynamic, imported symbols.
    '''
    p = subprocess.Popen([READELF_CMD, '--dyn-syms', '-W', '-h', executable], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)
    (stdout, stderr) = p.communicate()
    if p.returncode:
        raise IOError('Could not read symbols for %s: %s' %
                      (executable, stderr.strip()))
    syms = []
    for line in stdout.splitlines():
        line = line.split()
        if 'Machine:' in line:
            arch = line[-1]
        if len(line) > 7 and re.match('[0-9]+:$', line[0]):
            (sym, _, version) = line[7].partition('@')
            is_import = line[6] == 'UND'
            if version.startswith('@'):
                version = version[1:]
            if is_import == imports:
                syms.append((sym, version, arch))
    return syms


def check_version(max_versions, version, arch):
    if '_' in version:
        (lib, _, ver) = version.rpartition('_')
    else:
        lib = version
        ver = '0'
    ver = tuple([int(x) for x in ver.split('.')])
    if not lib in max_versions:
        return False
    return ver <= max_versions[lib] or lib == 'GLIBC' and ver <= ARCH_MIN_GLIBC_VER[arch]


def read_libraries(filename):
    p = subprocess.Popen([READELF_CMD, '-d', '-W', filename], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)
    (stdout, stderr) = p.communicate()
    if p.returncode:
        raise IOError('Error opening file')
    libraries = []
    for line in stdout.splitlines():
        tokens = line.split()
        if len(tokens) > 2 and tokens[1] == '(NEEDED)':
            match = re.match(
                '^Shared library: \[(.*)\]$', ' '.join(tokens[2:]))
            if match:
                libraries.append(match.group(1))
            else:
                raise ValueError('Unparseable (NEEDED) specification')
    return libraries


if __name__ == '__main__':
    cppfilt = CPPFilt()
    retval = 0
    for filename in sys.argv[1:]:
        # Check imported symbols
        for sym, version, arch in read_symbols(filename, True):
            if version and not check_version(MAX_VERSIONS, version, arch):
                print('%s: symbol %s from unsupported version %s' %
                      (filename, cppfilt(sym), version))
                retval = 1
        # Check exported symbols
        if arch != 'RISC-V':
            for sym, version, arch in read_symbols(filename, False):
                if sym in IGNORE_EXPORTS:
                    continue
                print('%s: export of symbol %s not allowed' % (filename, cppfilt(sym)))
                retval = 1
        # Check dependency libraries
        for library_name in read_libraries(filename):
            if library_name not in ALLOWED_LIBRARIES:
                print('%s: NEEDED library %s is not allowed' %
                      (filename, library_name))
                retval = 1

    sys.exit(retval)

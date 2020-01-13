#
# isys.py - installer utility functions and glue for C module
#
# Copyright (C) 2001-2013  Red Hat, Inc.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Matt Wilson <msw@redhat.com>
#            Erik Troan <ewt@redhat.com>
#            Jeremy Katz <katzj@redhat.com>
#

try:
    from pyanaconda import _isys
except ImportError:
    # We're running in some sort of testing mode, in which case we can fix
    # up PYTHONPATH and just do this basic import.
    import _isys

import blivet.arch
import time
import datetime
import pytz

import logging
log = logging.getLogger("anaconda")

if blivet.arch.getArch() in ["ppc64", "ppc64le"]:
    MIN_RAM = 768
    GUI_INSTALL_EXTRA_RAM = 512
else:
    MIN_RAM = 320
    GUI_INSTALL_EXTRA_RAM = 90

MIN_GUI_RAM = MIN_RAM + GUI_INSTALL_EXTRA_RAM
SQUASHFS_EXTRA_RAM = 350
NO_SWAP_EXTRA_RAM = 200

## Flush filesystem buffers.
def sync ():
    # TODO: This can be replaced with os.sync in Python 3.3
    return _isys.sync ()

ISO_BLOCK_SIZE = 2048

## Determine if a file is an ISO image or not.
# @param file The full path to a file to check.
# @return True if ISO image, False otherwise.
def isIsoImage(path):
    try:
        with open(path, "rb") as isoFile:
            for blockNum in range(16, 100):
                isoFile.seek(blockNum * ISO_BLOCK_SIZE + 1)
                if isoFile.read(5) == "CD001":
                    return True
    except IOError:
        pass

    return False

isPAE = None
def isPaeAvailable():
    global isPAE
    if isPAE is not None:
        return isPAE

    isPAE = False
    if not blivet.arch.isX86():
        return isPAE

    f = open("/proc/cpuinfo", "r")
    lines = f.readlines()
    f.close()

    for line in lines:
        if line.startswith("flags") and line.find("pae") != -1:
            isPAE = True
            break

    return isPAE

def isLpaeAvailable():
    with open("/proc/cpuinfo", "r") as fobj:
        for line in fobj:
            if line.startswith("Features") and "lpae" in line.split():
                return True

    return False

def get_cpu_model():
    """Get the cpu model number.

    :return: an integer value or None
    """
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            name, value = line.split(":")

            if name.strip() == "model":
                return int(value.strip())

    return None

def is_skylake():
    """Is it one of the supported Skylake cpu models?

    :return: True or False
    """
    return blivet.arch.isX86() and get_cpu_model() in {
        0x4E,  # INTEL_FAM6_SKYLAKE_MOBILE
        0x5E,  # INTEL_FAM6_SKYLAKE_DESKTOP
        0x55,  # INTEL_FAM6_SKYLAKE_X
        0x8E,  # INTEL_FAM6_KABYLAKE_MOBILE
        0x9E,  # INTEL_FAM6_KABYLAKE_DESKTOP
    }

def set_system_time(secs):
    """
    Set system time to time given as a number of seconds since the Epoch.

    :param secs: a number of seconds since the Epoch to set system time to
    :type secs: int

    """

    _isys.set_system_time(secs)
    log.info("System time set to %s UTC", time.asctime(time.gmtime(secs)))

def set_system_date_time(year=None, month=None, day=None, hour=None, minute=None,
                         second=None, tz=None):
    """
    Set system date and time given by the parameters as numbers. If some
    parameter is missing or None, the current system date/time field is used
    instead (i.e. the value is not changed by this function).

    :type year, month, ..., second: int

    """

    # If no timezone is set, use UTC
    if not tz:
        tz = pytz.UTC

    # get the right values
    now = datetime.datetime.now(tz)
    year = year if year is not None else now.year
    month = month if month is not None else now.month
    day = day if day is not None else now.day
    hour = hour if hour is not None else now.hour
    minute = minute if minute is not None else now.minute
    second = second if second is not None else now.second

    set_date = tz.localize(datetime.datetime(year, month, day, hour, minute, second))

    # Calculate the number of seconds between this time and timestamp 0
    epoch = tz.localize(datetime.datetime.fromtimestamp(0))
    timestamp = (set_date - epoch).total_seconds()

    set_system_time(timestamp)

def total_memory():
    """Returns total system memory in kB (given to us by /proc/meminfo)"""

    with open("/proc/meminfo", "r") as fobj:
        for line in fobj:
            if not line.startswith("MemTotal"):
                # we are only interested in the MemTotal: line
                continue

            fields = line.split()
            if len(fields) != 3:
                log.error("unknown format for MemTotal line in /proc/meminfo: %s", line.rstrip())
                raise RuntimeError("unknown format for MemTotal line in /proc/meminfo: %s" % line.rstrip())

            try:
                memsize = int(fields[1])
            except ValueError:
                log.error("ivalid value of MemTotal /proc/meminfo: %s", fields[1])
                raise RuntimeError("ivalid value of MemTotal /proc/meminfo: %s" % fields[1])

            # Because /proc/meminfo only gives us the MemTotal (total physical
            # RAM minus the kernel binary code), we need to round this
            # up. Assuming every machine has the total RAM MB number divisible
            # by 128.
            memsize /= 1024
            memsize = (memsize / 128 + 1) * 128
            memsize *= 1024

            log.info("%d kB (%d MB) are available", memsize, memsize / 1024)
            return memsize

        log.error("MemTotal: line not found in /proc/meminfo")
        raise RuntimeError("MemTotal: line not found in /proc/meminfo")

handleSegv = _isys.handleSegv

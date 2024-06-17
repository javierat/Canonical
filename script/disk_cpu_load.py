# Canonical Technical Assesment
# Candidate: Javier Torres
# Email: javier_alejandro_torres_r@hotmail.com
# Date: 06/17/2024

import os
import sys
import argparse
import subprocess


class CpuLoad:

    def __init__(self, disk_device="/dev/sda", max_load=30, xfer=4096):
        self.disk_device = disk_device
        self.verbose = 0
        self.max_load = max_load
        self.xfer = xfer

    def get_params(self):
        max_load_desc = "The maximum acceptable CPU load, as a percentage"
        xfer_desc = "The amount of data to read from the disk, in mebibytes"
        verbose_desc = "If present, produce more verbose output"
        parser = argparse.ArgumentParser(
            description='''The purpose of this script is to run disk stress
                            tests using the stress-ng program.''')

        parser.add_argument('--max-load', type=int, default=self.max_load,
                            help=max_load_desc)

        parser.add_argument('--xfer', type=int, default=self.xfer,
                            help=xfer_desc)

        parser.add_argument('--verbose', action='store_const', const=1,
                            default=self.verbose, help=verbose_desc)

        parser.add_argument("device_file", nargs="?", default=self.disk_device,
                            help='''This is the WHOLE-DISK device filename (with
                            or without "/dev/"), e.g. "sda" or "/dev/sda". The
                            script finds a filesystem on that device,
                            mounts it if necessary, and runs the tests on that
                            mounted filesystem. Defaults to /dev/sda.''')

        args = parser.parse_args()
        disk_device = "/dev/{}".format(args.device_file)

        if args.device_file.startswith("/dev/"):
            disk_device = args.device_file
        else:
            disk_device = "/dev/{}".format(args.device_file)

        disk_device = disk_device.replace("//", "/")

        if not self.system_device(disk_device):
            print('Unknown block device "\{}\"'.format(disk_device))
            print("Usage: script.py [options] [device-file]")
            sys.exit(1)

        disk_device = self.disk_device
        self.verbose = args.verbose
        params = {
            "disk_device": self.disk_device,
            "verbose": args.verbose,
            "max_load": args.max_load,
            "xfer": args.xfer

        }
        return params

    def sum_array(self, array):
        total = 0
        for i in array:
            total += int(i)
        return total

    def compute_cpu_load(self, start_use, end_use):
        start_use = start_use.split()
        end_use = end_use.split()

        diff_idle = int(end_use[3])-int(start_use[3])

        start_total = self.sum_array(start_use)
        end_total = self.sum_array(end_use)

        diff_total = end_total - start_total
        diff_used = diff_total - diff_idle
        if self.verbose == 1:
            print("Start CPU time = {}".format(start_total))
            print("End CPU time = {}".format(end_total))
            print("CPU time used = {}".format(diff_used))
            print("Total elapsed time = {}".format(diff_total))

        if diff_total != 0:
            cpu_load = (diff_used * 100) // diff_total

        else:
            cpu_load = 0

        return cpu_load

    def get_cpu_stats(self):
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith("cpu "):
                    # Split the line into parts and remove extra spaces
                    parts = line.strip().split()
                    # Exclude the first element ('cpu') and join the rest
                    cpu_stats = ' '.join(parts[1:])
                    return cpu_stats
        return None

    def system_device(self, path):
        try:
            status = os.stat(path)
            return os.path.exists(path)

        except OSError:
            return False

if __name__ == '__main__':
    application = CpuLoad()
    params = application.get_params()

    retval = 0
    print("Testing CPU load when reading {} MiB from {}".format(
        params['xfer'], params['disk_device']))
    print("Maximum acceptable CPU load is {}".format(params['max_load']))

    subprocess.run(["blockdev", "--flushbufs",
                    params['disk_device']], check=True)

    start_load = application.get_cpu_stats()
    if params['verbose'] == 1:
        print("Beginning disk read....")
    subprocess.run(["dd",
                    "if={}".format(params['disk_device']),
                    "of=/dev/null",
                    "bs=1048576",
                    "count={}".format(params['xfer'])],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if params['verbose'] == 1:
        print("Disk read complete!")

    end_load = application.get_cpu_stats()

    cpu_load = application.compute_cpu_load(start_load, end_load)
    print("Detected disk read CPU load is {}".format(cpu_load))

    if cpu_load > params['max_load']:
        retval = 1
        print("*** DISK CPU LOAD TEST HAS FAILED! ***")

    sys.exit(retval)

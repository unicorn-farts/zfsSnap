#!/usr/bin/python3
from datetime import datetime
from pprint import pprint
import argparse, subprocess

# configurable options
zfsPool = 'rpool/ROOT/ubuntu_in1307' # pool you want to snapshot // "grep zfs /proc/mounts" to list currently mounted pools
zfs = '/usr/sbin/zfs' # path to zfs binary // "which zfs" to find the path of yours
snapLimit = {
'hourly':   8,
'daily':    7,
'weekly':   4,
'monthly':  2 }
maxDiskUsage = 100 # GB
snapNameSchema = (zfsPool + '@' + datetime.now().strftime('%Y-%m-%d--%H%M') + '_')


def makeSnap(name):
    if not byteTotal > (maxDiskUsage * 1024000000):
        subprocess.run([zfs, 'snap', name])
    else:
        print('Error: snapshot maxDiskUsage exceeded!')
        subprocess.run(['/usr/bin/logger', 'zfsSnap.py: Error: snapshot maxDiskUsage exceeded!'])

def destroySnap(name):
    return subprocess.call([zfs, 'destroy', zfsPool + name], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

def fetchSnaps(): # populate snapshot lists
    global ss, byteTotal
    ss = {}
    ss['hourly'], ss['daily'], ss['weekly'], ss['monthly'] = ([], [], [], [])
    result = subprocess.run([zfs, 'list', '-t', 'snapshot'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    snaps, sizes = (result.stdout.strip().split()[5::5], result.stdout.strip().split()[6::5])
    interval = len(snapNameSchema)
    for snap in snaps:
        if snap[interval:] == 'hourly':
            ss['hourly'].append(snap[snap.index('@'):])
        elif snap[interval:] == 'daily':
            ss['daily'].append(snap[snap.index('@'):])
        elif snap[interval:] == 'weekly':
            ss['weekly'].append(snap[snap.index('@'):])
        elif snap[interval:] == 'monthly':
            ss['monthly'].append(snap[snap.index('@'):])
        else: # some other snap not part of this script
            pass
    kTotal, mTotal, gTotal = (0, 0, 0)
    for snapSize in sizes:
        if snapSize[-1] == 'K':
            kTotal += float(snapSize[:-1])
        elif snapSize[-1] == 'M':
            mTotal += float(snapSize[:-1])
        elif snapSize[-1] == 'G':
            gTotal += float(snapSize[:-1])
    byteTotal = (kTotal * 1024) + (mTotal * 1024000) + (gTotal * 1024000000)
    cleanSnaps()

def cleanSnaps(): # cleanup old snaps // cleanup can also be accomplished by running script without arguments
    for interval in snapLimit.keys():
        while len(ss[interval]) > snapLimit[interval]:
            if destroySnap(ss[interval][0]) == 0:
                del ss[interval][0]
            else:
                print('Warning: old snap(s) present and couldn\'t be removed. Does this user have permission?')
                break

# set cmdline arguments/options
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--create', choices=['hourly', 'daily', 'weekly', 'monthly'], help='set snap name suffix')
group.add_argument('--list', help='show current snapshots', action='store_true')
args = parser.parse_args()

fetchSnaps()

if args.create: # crontab calls script using create argument
    makeSnap((snapNameSchema + args.create))

if args.list: # display current snapshots
    for interval in ss.keys():
        heading = '[ ' + interval + ' ]  current=' + str(len(ss[interval])) + ' max=' + str(snapLimit[interval])
        if not len(ss[interval]) > snapLimit[interval]:
            print(heading)
        else:
            print(heading.upper() + ' !WARN')
        for snapList in ss.values():
            for snap in snapList:
                if snap[(snap.index('_') + 1):] == interval:
                    print(' ' + snap[:snap.index('_')])
    print('Total disk space used: ' + str(int(byteTotal / 1024000)) + 'M') # print byte total as MB
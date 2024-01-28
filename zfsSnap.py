#!/usr/bin/python3
from datetime import datetime
from os.path import basename
import argparse, subprocess

# configurable options
zfsPool = 'rpool/ROOT/ubuntu_in1307' # pool you want to snapshot // "grep zfs /proc/mounts" to list currently mounted pools
zfs = '/usr/sbin/zfs' # path to zfs binary
logger = '/usr/bin/logger' # path to logger binary
snapLimit = {
'hourly':   8,
'daily':    7,
'weekly':   4,
'monthly':  2 }
maxDiskUsage = 100 # GB
snapNameSchema = (zfsPool + '@' + datetime.now().strftime('%Y-%m-%d--%H%M') + '_')

def makeSnap(name):
    if not byteTotal > (maxDiskUsage * 1024000000):
        retCode = subprocess.call([zfs, 'snap', name])
        if retCode == 0:
            return 0
        return 2
    return 1

def destroySnap(name):
    return subprocess.call([zfs, 'destroy', zfsPool + name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# set cmdline arguments/options
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--create', choices=['hourly', 'daily', 'weekly', 'monthly'], help='set snap name suffix')
group.add_argument('--list', help='show current snapshots', action='store_true')
args = parser.parse_args()

# fetch snapshot information (names, disk space used)
ss = {}
ss['hourly'], ss['daily'], ss['weekly'], ss['monthly'] = ([], [], [], [])
result = subprocess.run([zfs, 'list', '-t', 'snapshot'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
snaps, sizes = (result.stdout.strip().split()[5::5], result.stdout.strip().split()[6::5]) # this will break if list output/format from zfs binary changes
interval = len(snapNameSchema)
for snap in snaps: # load snap names into ss dict
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
bTotal, kTotal, mTotal, gTotal = (0, 0, 0, 0)
for snapSize in sizes: # load snap sizes 
    if snapSize[-1] == 'B':
        bTotal += float(snapSize[:-1])
    elif snapSize[-1] == 'K':
        kTotal += float(snapSize[:-1])
    elif snapSize[-1] == 'M':
        mTotal += float(snapSize[:-1])
    elif snapSize[-1] == 'G':
        gTotal += float(snapSize[:-1])
byteTotal = bTotal + (kTotal * 1024) + (mTotal * 1024000) + (gTotal * 1024000000)

# cleanup old snaps
for interval in snapLimit.keys():
    while len(ss[interval]) > snapLimit[interval]:
        if destroySnap(ss[interval][0]) == 0:
            subprocess.run([logger, basename(__file__), 'INFO:', 'snapshot expired, removed:', zfsPool + ss[interval][0]])
            del ss[interval][0]
        else:
            print('Warning: old snap(s) present and couldn\'t be removed. Does this user have permission?')
            subprocess.run([logger, basename(__file__), 'WARN:', 'old snap(s) present but couldn\'t be removed. Does this user have permission?'])
            break

if args.create: # crontab calls script using create argument
    newSnap = (snapNameSchema + args.create)
    retCode = makeSnap(newSnap)
    if retCode == 1:
        print('Error: snapshot maxDiskUsage exceeded!')
        subprocess.run([logger, basename(__file__), 'ERR:', 'snapshot maxDiskUsage exceeded!'])
    elif retCode == 2:
        print('Warning: could not create snap:', newSnap)
        subprocess.run([logger, basename(__file__), 'WARN:', 'could not create snap:', newSnap + '.', 'does this user have permission?'])
    else:
        print('Snapshot created:', newSnap)
        subprocess.run([logger, basename(__file__), 'INFO:', 'snapshot created:', newSnap])

if args.list: # display current snapshots
    for interval in ss.keys():
        heading = interval + ' :: current=' + str(len(ss[interval])) + ' max=' + str(snapLimit[interval])
        if not len(ss[interval]) > snapLimit[interval]:
            print(heading)
        else:
            print(heading.upper(), '!WARN')
        for snapList in ss.values():
            for snap in snapList:
                if snap[(snap.index('_') + 1):] == interval:
                    print(' ' + snap)
        print()
    print('disk space :: current=' + str(round(byteTotal / 1024000000, 2)) + 'G', 'max=' + str(maxDiskUsage) + 'G') # print byte total as GB
#!/usr/bin/python3
from datetime import datetime
from pprint import pprint
import argparse, subprocess

# configurable options
zfsPool = 'rpool/ROOT/ubuntu_in1307'
snapLimitHourly  = 8
snapLimitDaily   = 7
snapLimitWeekly  = 4
snapLimitMonthly = 2
maxDiskUsage = 100 # GB
snapNameSchema = (zfsPool + '@' + datetime.now().strftime('%Y-%m-%d--%H%M') + '_')


def makeSnap(name):
    if not byteTotal > (maxDiskUsage * 1024000000):
        subprocess.run(['/usr/bin/sudo', 'zfs', 'snap', name])
    else:
        print('Error: snapshot maxDiskUsage exceeded!')
        subprocess.run(['/usr/bin/logger', 'zfsSnap.py: Error: snapshot maxDiskUsage exceeded!'])

def destroySnap(name):
    subprocess.run(['/usr/bin/sudo', 'zfs', 'destroy', zfsPool + name])

def fetchSnaps(): # populate snapshot lists
    global hourlySnaps, dailySnaps, weeklySnaps, monthlySnaps, byteTotal
    hourlySnaps, dailySnaps, weeklySnaps, monthlySnaps = ([], [], [], [])
    result = subprocess.run(['/usr/sbin/zfs', 'list', '-t', 'snapshot'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    snaps, sizes = (result.stdout.strip().split()[5::5], result.stdout.strip().split()[6::5])
    interval = len(snapNameSchema)
    for snapName in snaps:
        if snapName[interval:] == 'hourly':
            hourlySnaps.append(snapName[snapName.index('@'):])
        elif snapName[interval:] == 'daily':
            dailySnaps.append(snapName[snapName.index('@'):])
        elif snapName[interval:] == 'weekly':
            weeklySnaps.append(snapName[snapName.index('@'):])
        elif snapName[interval:] == 'monthly':
            monthlySnaps.append(snapName[snapName.index('@'):])
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
    while len(hourlySnaps) > snapLimitHourly:
        destroySnap(hourlySnaps[0])
        del hourlySnaps[0]
    while len(dailySnaps) > snapLimitDaily:
        destroySnap(dailySnaps[0])
        del dailySnaps[0]
    while len(weeklySnaps) > snapLimitWeekly:
        destroySnap(weeklySnaps[0])
        del weeklySnaps[0]
    while len(monthlySnaps) > snapLimitMonthly:
        destroySnap(monthlySnaps[0])
        del monthlySnaps[0]

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
    for i in [hourlySnaps, dailySnaps, weeklySnaps, monthlySnaps]:
        pprint(i, width=1)
    print('Total disk space used: ' + str(int(byteTotal / 1024000)) + 'M') # print byte total as MB
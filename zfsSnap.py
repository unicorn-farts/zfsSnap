#!/usr/bin/python3
from datetime import datetime
from pprint import pprint
import argparse, subprocess

# configurable options
zfsPool = 'rpool/ROOT/ubuntu_in1307'
snapNameSchema = (zfsPool + '@' + datetime.now().strftime('%Y-%m-%d--%H%M') + '_')
snapLimitHourly  = 8
snapLimitDaily   = 7
snapLimitWeekly  = 4
snapLimitMonthly = 2

def makeSnap(name):
    subprocess.run(['/usr/bin/sudo', 'zfs', 'snap', name])

def destroySnap(name):
    subprocess.run(['/usr/bin/sudo', 'zfs', 'destroy', name])

# populate snapshot lists
hourlySnaps, dailySnaps, weeklySnaps, monthlySnaps = ([], [], [], [])
result = subprocess.run(['/usr/sbin/zfs', 'list', '-t', 'snapshot'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
snaps = result.stdout.strip().split()[5::5]
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

# set cmdline arguments/options
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--create', choices=['hourly', 'daily', 'weekly', 'monthly'], help='set snap name suffix')
group.add_argument('--list', help='show current snapshots', action='store_true')
args = parser.parse_args()

if args.create: # crontab calls script using create argument
    makeSnap((snapNameSchema + args.create))

if args.list: # display current snapshots
    for i in [hourlySnaps, dailySnaps, weeklySnaps, monthlySnaps]:
        pprint(i)

# cleanup old snaps // cleanup can also be accomplished by running script without arguments
while len(dailySnaps) > snapLimitDaily:
    destroySnap(dailySnaps[0])
    del dailySnaps[0]
while len(weeklySnaps) > snapLimitWeekly:
    destroySnap(weeklySnaps[0])
    del weeklySnaps[0]
while len(monthlySnaps) > snapLimitMonthly:
    destroySnap(monthlySnaps[0])
    del monthlySnaps[0]
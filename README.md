<h1>zfsSnap.py</h1>
<h2>A simple script to help automate snapshot schedules of a zfs pool</h2>

Setup:<br>
  - Tested under Ubuntu 22
  - 'zfsPool' needs to be set before use. Use ```grep zfs /proc/mounts``` to view your currently mounted pools
  - Script needs to be run as root/sudo, or user with zfs create/destroy permissions

Usage:<br>
  - Script written to be used with crontab events; a snapshot schedule crontab example is below:
```
## zfs snapshot schedules ##
00 * * * *  /usr/bin/sudo /home/user/.local/bin/zfsSnap.py --create hourly  > /dev/null 2>&1
01 12 * * * /usr/bin/sudo /home/user/.local/bin/zfsSnap.py --create daily   > /dev/null 2>&1
02 12 * * 1 /usr/bin/sudo /home/user/.local/bin/zfsSnap.py --create weekly  > /dev/null 2>&1
03 12 1 * * /usr/bin/sudo /home/user/.local/bin/zfsSnap.py --create monthly > /dev/null 2>&1
```
  - Manually calling script and passing ```--create {hourly,daily,weekly,monthly}``` argument/option will force a snapshot using the script's schema
  - Calling script and passing ```--list``` argument will output the current snapshot status and disk space usage:
```
hourly :: current=8 max=8
 @2024-01-28--1000_hourly
 @2024-01-28--1100_hourly
 @2024-01-28--1200_hourly
 @2024-01-28--1300_hourly
 @2024-01-28--1400_hourly
 @2024-01-28--1500_hourly
 @2024-01-28--1600_hourly
 @2024-01-28--1700_hourly

daily :: current=7 max=7
 @2024-01-21--1201_daily
 @2024-01-22--1201_daily
 @2024-01-23--1201_daily
 @2024-01-24--1201_daily
 @2024-01-25--1201_daily
 @2024-01-26--1201_daily
 @2024-01-27--1201_daily

weekly :: current=1 max=4
 @2024-01-22--1202_weekly

monthly :: current=1 max=2
 @2024-01-21--1203_monthly

disk space :: current=0.68G max=100G
```
  - Anytime the script is called, if a snapshot count exceeds it's respective interval limit (what is set under ```snapLimit{```), the script will destroy the oldest snaps until the snapshot count is no longer exceeded.
  - Actions are logged in syslog. Use ```grep zfsSnap.py /var/log/syslog``` to see what it's been doing.
  - To view all snapshots on the system, including those not managed by the script, use ```zfs list -t snapshot```
  - To manually destroy a snapshot created by the script, use ```zfs destroy rpool/ROOT/ubuntu_--your-pool-here--@2024-01-22--1203_monthly```, make sure to use the full snapshot name from the above zfs list command, not from the script's ```--list``` output.

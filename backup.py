#!/usr/bin/env python

import os.path
import subprocess
import datetime
import gzip

BACKUP_DIR = '/root/backups/{app}/'
BACKUP_DEST = os.path.join(BACKUP_DIR, '{item}')


def get_output(cmd):
    results = []
    for result in subprocess.check_output(cmd).split('\n'):
        result = result.strip()
        if not result:
            continue
        results.append(result)
    return results

now = datetime.datetime.utcnow()

# Get dokku apps
apps = get_output(['dokku', 'apps:list'])

# Create backup dirs
for app in apps:
    try:
        os.makedirs(BACKUP_DIR.format(app=app), 0700)
    except OSError, exp:
        if exp.message.startswith('File exists'):
            pass

# Get postgres dbs
dbs = {}
for app in apps:
    dbs[app] = get_output(['dokku', 'postgresql:list', app])


# Backup dbs
for app, dbs in dbs.items():
    for db in dbs:
        filename = 'postgresql_backup_rattic_rattic_{date}.sql.gz'.format(date=now.isoformat())
        output = subprocess.check_output(['dokku', 'postgresql:dump', app, db])
        with gzip.open(BACKUP_DEST.format(app=app, item=filename), 'wb') as f:
            f.write(output)
g

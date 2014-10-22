#!/usr/bin/env python
import os.path
import subprocess
import datetime
import gzip

BACKUP_ROOT = os.environ.get('BACKUP_ROOT', '/var/backups/data')
BACKUP_DIR = os.path.join(BACKUP_ROOT, '{app}/')
BACKUP_DEST = os.path.join(BACKUP_DIR, '{item}')


def create_app_dir(app):
    path = BACKUP_DIR.format(app=app)
    try:
        os.makedirs(path)
    except OSError, exp:
        if exp.message.startswith('File exists'):
            pass
    # root, backup
    os.chown(path, 0, 34)
    os.chmod(path, 0770)


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
    create_app_dir(app)

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

# Backup dokku
create_app_dir('dokku')
filename = 'dokku_backup_{date}.tar'.format(date=now.isoformat())
get_output(['dokku', 'backup:export', BACKUP_DEST.format(app='dokku', item=filename)])

#!/usr/bin/env python
import os.path
import subprocess
import datetime
import gzip

DOKKU_CMD = '/usr/local/bin/dokku'
BACKUP_ROOT = os.environ.get('BACKUP_ROOT', '/var/backups/data')
BACKUP_DIR = os.path.join(BACKUP_ROOT, '{app}/')
BACKUP_DEST = os.path.join(BACKUP_DIR, '{item}')
VOLUME_BACKUP_CMD = '/usr/bin/docker run --volumes-from volume_data_{volume_name} -v {dest}:/tmp/backup ubuntu tar cfj /tmp/backup/volume_name_{volume_name}_{date}.tar.bz2 {path}'


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
apps = get_output([DOKKU_CMD, 'apps:list'])

# Create backup dirs
for app in apps:
    create_app_dir(app)

# Get postgres dbs
dbs = {}
for app in apps:
    dbs[app] = get_output([DOKKU_CMD, 'postgresql:list', app])


# Backup dbs
for app, dbs in dbs.items():
    for db in dbs:
        filename = 'postgresql_backup_{db}_{date}.sql.gz'.format(db=db, date=now.isoformat())
        output = subprocess.check_output([DOKKU_CMD, 'postgresql:dump', app, db])
        with gzip.open(BACKUP_DEST.format(app=app, item=filename), 'wb') as f:
            f.write(output)

# Backup volumes
create_app_dir('_volumes')


volumes = get_output([DOKKU_CMD, 'volume:list'])
for volume in volumes:
    volume_path = get_output([DOKKU_CMD, 'volume:info', volume])[0]
    cmd = VOLUME_BACKUP_CMD.format(volume_name=volume,
                                   dest=BACKUP_DIR.format(app='_volumes'),
                                   date=now.isoformat(), path=volume_path)
    get_output(cmd.split())

# Backup dokku
create_app_dir('dokku')
filename = 'dokku_backup_{date}.tar'.format(date=now.isoformat())
get_output([DOKKU_CMD, 'backup:export', BACKUP_DEST.format(app='dokku', item=filename)])

# Chown
get_output(['/bin/chown', '-R', 'backup:backup', BACKUP_ROOT])

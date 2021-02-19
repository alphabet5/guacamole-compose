# guacamole-compose
 docker-compose script for running apache guacamole.

## Overview

This set of scripts and templates automates the deployment process for guacamole.

- Generates the docker-compose script.
- Generates the mysql initialization script, to configure a new mysql database.
- Generates an nginx configuration.
- Has parameter options and templates, so you should just have to change a single parameter file for each deployment.
- Adds users to mysql from ldap.
- Configures connections from ldap.
- Configures connections from the paramter file.


## Requirements

- docker
- docker-compose
- python3 (3.9)
- git

Python Packages
- sqlalchemy
- docker
- ldap3
- pymysql
- dnspython (v2.0.0)
- pyyaml
- cryptography


## Usage
```bash
python3.9 -m pip install --upgrade guacamole_compose
python3.9 -m guacamole_compose --deploy --create_users --create_connections
```


## Old Usage
```bash
git clone https://github.com/alphabet5/guacamole-compose.git
cd guacamole-compose
```

```bash
python3.8 ./guac-deploy.py --deploy --create_users --create_connections
```
```bash
usage: guacamole-compose [-h] [--init] [--clean] [--deploy] [--nginx] [--ldap-groups]

optional arguments:
  -h, --help     show this help message and exit
  --init         Initialize the directory and files required.
  --clean        Clean the directories automatically created during deployment.
  --deploy       Generate configurations and deploy guacamole using docker-compose.
  --nginx        Generate the nginx.conf file located at./nginx/conf/nginx.conf.
  --ldap-groups  Used to create/update connections and groups using ldap.

```


## Cleanup of shared directory, and periodic user sync.

Note: Check your python executable path, and modify for the cron entry below. 

```bash
python3.8
```

```python
import sys
print(sys.executable)
```

```bash
crontab -e

0 0 * * * find /root/guacamole-compose/shared/* -mtime +6 -type f -delete
*/5 * * * * cd /root/guacamole-compose && /usr/local/bin/python3.8 ./guac-deploy.py --create_users
```

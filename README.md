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
- Configures additional manual connections from the paramters.yaml file.


## Requirements

- docker
- docker-compose
- python3 (3.9)
- pip

Python Packages
- guacamole-compose
  
- **Note, guacamole-compose will install the following packages:**
    - sqlalchemy
    - docker
    - ldap3
    - pymysql
    - dnspython (v2.0.0)
    - pyyaml
    - cryptography
    - yamlarg
    - cffi


## Usage

This requires active directory to be configured with a user group containing child user groups that will be synced to Apache Guacamole.

For example:

- guacamole/group1
- guacamole/group2

- Computer1 is a member of group1
- Computer2 is a member of group2

If a user logs in and is a member of group1, they will have access to the connection created for Computer1. 

All computers that are in child groups will be created based off of the configuration settings in parameters.yaml.

```bash
sudo python3.9 -m pip install --upgrade guacamole-compose
sudo guacamole-compose --init
vi parameters.yaml
sudo guacamole-compose --deploy --ldap

% guacamole-compose --help
usage: guacamole-compose [-h] [--init] [--clean] [--deploy] [--nginx] [--ldap]

optional arguments:
  -h, --help  show this help message and exit
  --init      Initialize the directory and files required.
  --clean     Clean the directories automatically created during deployment.
  --deploy    Generate configurations and deploy guacamole using docker-compose.
  --nginx     Generate the nginx.conf file located at./nginx/conf/nginx.conf.
  --ldap      Used to create/update connections, groups, and permissions using ldap.
```


## Cleanup of shared directory

The template parameters.yaml uses a common folder called 'shared' for transferring files in and out of the remote computers. To prevent this folder from growing too large, you can periodically remove files older than ~6 days with a cron job. This example is shown below.
```bash
crontab -e

0 0 * * * find /root/shared/* -mtime +6 -type f -delete
```

## Updating the package and uploading to pypi
Make sure the version information is updated before uploading. You cannot upload 2 copies with the same version.

```bash
sudo rm -r dist
python3.9 setup.py bdist_wheel --universal
twine upload dist/*
```
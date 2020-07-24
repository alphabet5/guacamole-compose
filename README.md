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
- python3.8

Python Packages
- mysqlclient
- sqlalchemy
- docker
- docker-compose


## Usage
```bash
git clone https://github.com/alphabet5/guacamole-compose.git
cd guacamole-compose
```

```bash
python3.8 ./guac-deploy.py --deploy --create_users --create_connections
```
```bash
usage: guac-deploy.py [-h] [--clean] [--deploy] [--configs] [--skip_nginx] [--create_users] [--create_connections]

optional arguments:
  -h, --help            show this help message and exit
  --clean               Clean the directories automatically created during deployment.
  --deploy              Generate configurations and deploy guacamole using docker-compose.
  --configs             Generate configurations only. Do not deploy guacamole.
  --skip_nginx          Skip generating the nginx.conf file - this must be manually created and located at ./nginx/conf/nginx.conf.
  --create_users        Create users within MySQL.
  --create_connections  Create connections within MySQL.
```



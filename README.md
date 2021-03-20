# guacamole-compose
 docker-compose script for running apache guacamole.

## Overview

This set of scripts and templates automates the deployment process for guacamole.

- Generates the docker-compose script.
- Generates the mysql initialization script, to configure a new mysql database.
- Generates an nginx configuration.
- Has parameter options and templates, so you should just have to change a single parameter file for each deployment.
- Adds user groups to mysql from ldap.
- Configures connections from ldap.
- Configures user groups with permissions to connections
- Configures additional manual connections from the paramters.yaml file.


## Requirements

Tested on Ubuntu 20.04 LTS

- docker
- docker-compose
- python3 (3.9)
- pip

```bash
sudo apt update && sudo apt upgrade -y && sudo apt install docker docker-compose python3.9 -y
curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py
sudo python3.9 ./get-pip.py
```

Python Packages
- guacamole-compose
  
- **Note, guacamole-compose will install the following packages:**
    - sqlalchemy
    - docker
    - ldap3
    - pymysql
    - dnspython
    - pyyaml
    - cryptography
    - yamlarg
    - cffi

```bash
sudo python3.9 -m pip install guacamole-compose
```

Note: sudo is needed in the above command only if docker requires sudo privileges to be ran. This is the case by default when running docker.

## Usage

This requires active directory to be configured with a user group containing child user groups that will be synced to Apache Guacamole.

An example structure in active directory.
```yaml
- guacamole: # 'guacamole' is the base user group, configured in parameters.yaml under ldap-user-search-filter and ldap/ldap_group.
    - user_group1: # This is a child group, a member of the 'guacamole' user group. This group will be created in apache guacamole.
        - computer1 # This is a computer object whos connection will be automatically created. Permission to read/connect/view will be granted to members of user_group1, or user_group2 - since the computer object also exists in user_group2
        - user1 # user1 will not have a user created in guacamole, but will be able to view any connections it's in a group with.
    - user_group2:
        - computer1
        - computer2
        - user2
```

- If a user logs in and is a member of group1, they will have access to the connection created for computer1. 
- All computers that are in child groups will have connections created based off of the configuration settings in parameters.yaml. (auto_connections)

Steps:
- Run `guacamole-compose --init`
- Edit the paramters.yaml file for the specific deployment.
- Edit either the nginx.conf or haproxy.cfg files depending on which rwp you prefer.
    - The default haproxy.cfg and nginx.conf files use http 80 over localhost for testing.
    - If you --deploy with the --haproxy_cfg or --nginx flags, it will overwrite the existing nginx.conf/haproxy.cfg using a template. This is most likely not what you want.
- Fetch certificates, and place in the corresponding folder.
- Deploy guacamole with `sudo guacamole-compose --deploy --haproxy --ldap`
- If you want to update your user groups / connections after active directory changes run `sudo guacamole-compose --ldap`



```bash
guacamole-compose --init
vi parameters.yaml
sudo guacamole-compose --deploy --ldap

% guacamole-compose --help
usage: guacamole-compose [-h] [--init] [--clean] [--deploy] [--nginx] [--haproxy] [--haproxy_cfg] [--ldap]

optional arguments:
  -h, --help     show this help message and exit
  --init         Initialize the directory and files required.
  --clean        Clean the directories automatically created during deployment.
  --deploy       Generate configurations and deploy guacamole using docker-compose.
  --nginx        Generate the nginx.conf file located at./nginx/conf/nginx.conf.
  --haproxy      Deploy with haproxy instead of nginx.
  --haproxy_cfg  Generate the haproxy .cfg file using values from parameters.yaml
  --ldap         Used to create/update connections, groups, and permissions using ldap.
```

## Cleanup of shared directory

The template parameters.yaml uses a common folder called 'shared' for transferring files in and out of the remote computers. To prevent this folder from growing too large, you can periodically remove files older than ~6 days with a cron job. This example is shown below.
```bash
crontab -e

0 0 * * * find /home/user/shared/* -mtime +6 -type f -delete
```

## Updating the package and uploading to pypi
Make sure the version information is updated before uploading. You cannot upload 2 copies with the same version.

```bash
sudo rm -r dist
python3.9 setup.py bdist_wheel --universal
twine upload dist/*
```

## Changelog

### 0.1.4
#### Fixed
- internalProxies in server.xml to be more generic and work no matter the internal rwp address.
- Added checks for `guacamole-compose --init` to not overwrite existing files.

### 0.1.3
#### Fixed
- create the ./shared folder with the --init command (without sudo). This fixes a permission issue where users would have to `sudo chown user:user ./shared` for file transfers.
- Updated README.md to remove `sudo` from in front of `guacamole-compose --init`
- Updated the internal proxies from 127.0.0.1 to the default. (as the rwp container will not be 127.0.0.1 to the guacamole container.) This is safe as the guacamole container does not have any exposed ports.

### 0.1.2
#### Added
- server.xml so that the guacamole webpage correctly shows the remote address via X-Forwarded-For.
- `option forwardfor` in the haproxy templates.
- code in the init section to create the server.xml file from the template in ./tomcat folder.
  
#### Fixed
- Updated nginx init conf with max body size of 10000 (for large file transfers.) Nginx configuration option already had this set.
- Duplicate documentation section in README.md on updating groups and connections.
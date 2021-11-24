# guacamole-compose

## This project has been archived. This was a great learning experience and helpful for automating some repetitive tasks. The mechanism of use is not ideal for further automation. I am replacing some functionality here with alphabet5/guacamole-users-docker with the intent to be a stateless mechanism for syncing ldap computers and groups to mysql, running in a container.

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
sudo apt update && \
    sudo apt upgrade -y && \
<<<<<<< Updated upstream
    sudo apt install docker docker-compose python3.9 -y && \
=======
    sudo apt install apt-transport-https ca-certificates curl software-properties-common && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && \
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable" && \
    sudo apt update && \
    sudo apt install docker-ce python3.9 -y && \
>>>>>>> Stashed changes
    sudo systemctl enable docker && \
    curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py && \
    sudo python3.9 ./get-pip.py
```

Using Podman:
```bash
source /etc/os-release
sudo sh -c "echo 'deb http://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${VERSION_ID}/ /' > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list"
sudo wget -nv https://download.opensuse.org/repositories/devel:kubic:libcontainers:stable/xUbuntu_${VERSION_ID}/Release.key -O- | sudo apt-key add -
sudo apt-get update -qq -y
sudo apt-get -qq --yes install podman
#TODO...
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
usage: guacamole-compose [-h] [--init] [--clean] [--deploy] [--nginx] [--haproxy] [--haproxy_cfg] [--ldap] [--version]

optional arguments:
  -h, --help     show this help message and exit
  --init         Initialize the directory and files required.
  --clean        Clean the directories automatically created during deployment.
  --deploy       Generate configurations and deploy guacamole using docker-compose.
  --nginx        Generate the nginx.conf file located at./nginx/conf/nginx.conf.
  --haproxy      Deploy with haproxy instead of nginx.
  --haproxy_cfg  Generate the haproxy .cfg file using values from parameters.yaml
  --ldap         Used to create/update connections, groups, and permissions using ldap.
  --version      Outputs version information.
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

<<<<<<< Updated upstream
=======
### 0.1.8
#### Changed
- Removed the command-line and pip packages. This is now only for linking to mysql and ldap as well as database initialization.
- 

### 0.1.7
#### Fixed
- docker-compose version (changed to v3.9)
- docker-compose requirement in setup.py

#### Other
- Added notes in the readme on errors caused by distutils version of pyyaml.
- Changes in the --clean command to only clean up specific folders for nginx, haproxy, etc.

### 0.1.6
#### Fixed
- Removed radius auth extension as it is no longer used.
- Removed unnecessary ./init folder removal in the clean command.

>>>>>>> Stashed changes
### 0.1.5
#### Fixed
- Added clarification to parameters.yaml template to specify an alphanumeric password for the mysql user.

#### Added
- Version information with the --version flag.
- Color printing for warnings and errors.
- Output a warning if --init is run as sudo. (Creates the ./shared directory with incorrect permissions.)
- client.image.prune after deploying to clean up unused images.

#### Other
- Removed duplicate import of shutil.
- Removed the 'ldap' section in parameters.yaml and instead use the ldap information within the guacamole-properties section.

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
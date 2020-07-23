#!/bin/bash

# Initialize MySQL database.
# Add this into the container via mount point.
# This should be in the same folder as the guacamole initdb.sql.script file.
# This file is executed before initdb.sql.script as files are executed in alphabetical order.

while ! mysqladmin -uroot -ppassword ping -hlocalhost --silent; do
    sleep 1
done

sleep 1

mysql -uroot -ppassword --force -e "FLUSH PRIVILEGES;" || true
mysql -uroot -ppassword --force -e "CREATE DATABASE guacamole_db;" || true
mysql -uroot -ppassword --force -e "CREATE USER 'guacamole_user'@'%' IDENTIFIED BY 'password';" || true
mysql -uroot -ppassword --force -e "GRANT SELECT,INSERT,UPDATE,DELETE ON guacamole_db.* TO 'guacamole_user'@'%';" || true
mysql -uroot -ppassword --force -e "FLUSH PRIVILEGES;" || true

mysql -uroot -ppassword --force guacamole_db < /docker-entrypoint-initdb.d/initdb.sql.script

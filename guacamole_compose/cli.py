def sql_insert(engine, conn, table, **kwargs):
    import sqlalchemy
    from sqlalchemy.dialects.mysql import insert
    metadata = sqlalchemy.MetaData()
    table_obj = sqlalchemy.Table(table, metadata, autoload=True, autoload_with=engine)
    insert_statement = insert(table_obj).values(**kwargs)
    on_duplicate = insert_statement.on_duplicate_key_update(**kwargs)
    return conn.execute(on_duplicate)


def check_container_status(container_name, timeout):
    import docker
    import time
    client = docker.from_env()
    active = False
    counter = 0
    while not active:
        try:
            container = client.containers.get(container_name)
            if container.attrs['State']['Health']['Status'] == 'healthy':
                active = True
            else:
                print("waiting for mysql...")
                time.sleep(10)
                counter += 1
        except:
            import traceback
            print(traceback.format_exc())
            counter += 1
            time.sleep(10)
        if counter > (timeout / 10):
            print("Timeout reached, container not available.")
            active = True


def check_port(ip, port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False


def main():
    import subprocess
    import yaml
    import shutil
    import docker
    import os
    import yamlarg
    import shutil
    import sys

    pkgdir = sys.modules['guacamole_compose'].__path__[0]
    print(pkgdir)
    print(os.listdir(pkgdir))
    args = yamlarg.parse(os.path.join(pkgdir, 'arguments.yaml'))

    if args['init']:
        print("Creating structure and paramters.yaml...")
        for folder in ['./guacamole_home',
                       './guacamole_home/extensions',
                       './nginx',
                       './nginx/conf',
                       './nginx/certs',
                       './nginx/auth']:
            if not os.path.exists(folder):
                os.makedirs(folder)
        shutil.copy(os.path.join(pkgdir, 'templates/parameters.yaml'), os.getcwd())
        shutil.copy(os.path.join(pkgdir, 'templates/nginx_init.conf'), './nginx/conf/nginx.conf')
    else:
        params = yaml.load(open('parameters.yaml', 'r'), Loader=yaml.FullLoader)
        client = docker.from_env()

        if args['clean']:
            print("Running docker-compose down...")
            try:
                docker_compose_cmd = subprocess.run(['docker-compose down'], shell=True)
            except:
                import traceback

                print(traceback.format_exc())
            print("Clearing generated directories...")
            client.containers.prune()
            client.volumes.prune()
            client.images.prune(filters={'dangling': False})
            for folder in ['./shared',
                           './mysql',
                           './init']:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
            if args['nginx']:
                if os.path.exists('./nginx/conf'):
                    shutil.rmtree('./nginx/conf')

        if args['deploy']:
            import string

            print("Generating configs...")
            if args['nginx']:
                nginx_conf_template = string.Template(open('templates/nginx_conf.template', 'r').read())
                with open('./nginx/conf/nginx.conf', 'w') as f:
                    f.write(nginx_conf_template.substitute(**params))
            with open('./guacamole_home/guacamole.properties', 'w') as f:
                yaml.dump(params['guacamole-properties'], open('./guacamole_home/guacamole.properties', 'w'))
            if 'ldap-hostname' in params['guacamole-properties']:
                # Copies the guacamole-auth-ldap if ldap is configured.
                shutil.copy(os.path.join(pkgdir, 'templates/guacamole-auth-ldap-1.3.0.jar'),
                            os.path.join(os.getcwd(), 'guacamole_home/extensions'))
            else:
                # Copies the guacamole-auth-radius if the new method is used without ldap - defaults to radius.
                shutil.copy(os.path.join(pkgdir, 'templates/guacamole-auth-radius-1.3.0.jar'),
                            os.path.join(os.getcwd(), 'guacamole_home/extensions'))

            docker_compose_template = string.Template(
                open(os.path.join(pkgdir, 'templates/docker-compose.yml.template'), 'r').read())
            with open('./docker-compose.yml', 'w') as f:
                f.write(docker_compose_template.substitute(**params))
            mysql_init_template = string.Template(
                open(os.path.join(pkgdir, 'templates/initdb.sh.template'), 'r').read())
            with open('./initdb.sh', 'w') as f:
                f.write(mysql_init_template.substitute(**params))
            shutil.copy(os.path.join(pkgdir, 'templates/initdb.sql.script'),'./initdb.sql.script')

        if args['deploy']:
            print("Deploying...")
            try:
                docker_compose_cmd = subprocess.run(['docker-compose pull'], shell=True)
            except:
                import traceback

                print(traceback.format_exc())
            try:
                docker_compose_cmd = subprocess.run(['docker-compose up -d'], shell=True)
            except:
                import traceback

                print(traceback.format_exc())
        if args['ldap']:
            # Connect to ldap
            from ldap3 import Server, Connection, ALL, NTLM, ALL_ATTRIBUTES
            import json
            from copy import deepcopyz
            import sqlalchemy

            server = Server(params['guacamole-properties']['ldap-hostname'],
                            get_info=ALL)
            ldap_conn = Connection(server=params['ldap']['ldap_server'],
                                   user=params['ldap']['ldap_domain'].split('.')[0] + '\\' + \
                                        params['ldap']['ldap_user'],
                                   password=params['ldap']['ldap_password'],
                                   auto_bind=True,
                                   auto_referrals=False,
                                   authentication=NTLM)
            domain_dn = ','.join(['DC=' + d for d in params['ldap']['ldap_domain'].split('.')])

            # Connect to MySQL
            engine = sqlalchemy.create_engine('mysql+pymysql://' +
                                              params['mysql_user'] + ':' +
                                              params['mysql_password'] + '@127.0.0.1:3306/guacamole_db')
            sql_conn = engine.connect()

            # Create connections
            connections = list()
            connection_ids = dict()
            ldap_conn.search(domain_dn,
                             '(&(objectCategory=' + 'Computer' +
                             ')(memberOf:1.2.840.113556.1.4.1941:=CN=' +
                             str(params['ldap']['ldap_group']) + ',CN=Users,' +
                             domain_dn + '))',
                             attributes=ALL_ATTRIBUTES)
            computers = json.loads(ldap_conn.response_to_json())
            connection_names = dict()
            for computer in computers['entries']:
                if params['auto_connection_dns']:
                    hostname = computer['attributes']['dNSHostName']
                    conn_name = hostname
                else:
                    import dns.resolver

                    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
                    dns.resolver.default_resolver.nameservers = [params['auto_connection_dns_resolver']]
                    hostname = dns.resolver.resolve(computer['attributes']['dNSHostName'], 'a').response.answer[0][
                        0].address
                    conn_name = computer['attributes']['dNSHostName'] + " - " + hostname
                connection = params['auto_connections']
                connection['connection']['connection_name'] = conn_name
                connection['parameters']['hostname'] = hostname
                connections.append(deepcopy(connection))
                connection_names[conn_name] = computer
            if 'manual_connections' in params.keys():
                for connection in params['manual_connections']:
                    connections.append(deepcopy(connection))
            for connection in connections:
                sql_insert(engine, sql_conn, 'guacamole_connection',
                           **connection['connection'])
                conn_name = connection['connection']['connection_name']
                connection_id = \
                engine.execute('SELECT connection_id from guacamole_connection WHERE connection_name = "' +
                               conn_name + '";').fetchone()['connection_id']
                for parameter_name, parameter_value in connection['parameters'].items():
                    sql_insert(engine, sql_conn, 'guacamole_connection_parameter',
                               connection_id=connection_id,
                               parameter_name=parameter_name,
                               parameter_value=parameter_value)
                connection_ids[connection_id] = conn_name

            # Clean up undefined connections.
            connections = engine.execute('SELECT * from guacamole_connection;').fetchall()
            for connection in connections:
                if connection['connection_id'] not in connection_ids:
                    engine.execute(
                        'DELETE from guacamole_connection WHERE connection_id = ' + connection['connection_id'] + ';')

            # Create user groups .
            ldap_conn.search(domain_dn,
                             '(&(objectCategory=' + 'Group' +
                             ')(memberOf:1.2.840.113556.1.4.1941:=CN=' +
                             str(params['ldap']['ldap_group']) + ',CN=Users,' +
                             domain_dn + '))',
                             attributes=ALL_ATTRIBUTES)
            ldap_groups = json.loads(ldap_conn.response_to_json())
            for group in ldap_groups['entries']:
                cn = group['attributes']['cn']
                dn = group['attributes']['distinguishedName']
                sql_insert(engine, sql_conn, 'guacamole_entity',
                           **{'name': cn, 'type': 'USER_GROUP'})
                entity_id = engine.execute('SELECT entity_id from guacamole_entity WHERE name = "' +
                                           cn + '";').fetchone()['entity_id']
                for conn_name, computer in connection_names.items():
                    sql_statement = 'SELECT connection_id from guacamole_connection WHERE connection_name = "' + \
                                    conn_name + '";'
                    connection_id = engine.execute(sql_statement).fetchone()['connection_id']
                    if dn in computer['memberOf']:
                        sql_insert(engine, sql_conn, 'guacamole_connection_permission',
                                   **{'entity_id': entity_id,
                                      'connection_id': connection_id,
                                      'permission': 'READ'})
                    else:
                        engine.execute('DELETE from guacamole_connection_permission WHERE entity_id = ' +
                                       str(entity_id) + ' AND connection_id = ' + connection_id + ';')
                for conn_name, groups in params['manual_permissions']:
                    sql_statement = 'SELECT connection_id from guacamole_connection WHERE connection_name = "' + \
                                    conn_name + '";'
                    connection_id = engine.execute(sql_statement).fetchone()['connection_id']
                    entity_ids = list()
                    for cn in groups:
                        entity_id = engine.execute('SELECT entity_id from guacamole_entity WHERE name = "' +
                                                   cn + '";').fetchone()['entity_id']
                        entity_ids.append(str(entity_id))

                    engine.execute(
                        'DELETE from guacamole_connection_permission WHERE connection_id = ' + str(connection_id) +
                        ' AND entity_id NOT IN (' + ','.join(entity_ids) + ');')
                    for entity_id in entity_ids:
                        sql_insert(engine, sql_conn, 'guacamole_connection_permission',
                                   **{'entity_id': entity_id,
                                      'connection_id': connection_id,
                                      'permission': 'READ'})
            # Give guacadmin user permission to all connections and user groups.
            sql_statement = 'SELECT entity_id FROM guacamole_entity WHERE name = "guacadmin"'
            guacadmin_entity_id = engine.execute(sql_statement).fetchone()['entity_id']
            for connection_id in connection_ids.keys():
                for permission in ['READ', 'UPDATE', 'DELETE', 'ADMINISTER']:
                    sql_insert(engine, sql_conn, 'guacamole_connection_permission',
                               entity_id=guacadmin_entity_id,
                               connection_id=connection_id,
                               permission=permission)
            groups = engine.execute('SELECT * from guacamole_entity WHERE type = "USER_GROUP"').fetchall()
            for group in groups:
                for permission in ['READ', 'UPDATE', 'DELETE', 'ADMINISTER']:
                    sql_insert(engine, sql_conn, 'guacamole_connection_permission',
                               entity_id=guacadmin_entity_id,
                               affected_user_group_id=group['entity_id'],
                               permission=permission)
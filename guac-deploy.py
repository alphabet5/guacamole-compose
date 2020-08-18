def sql_insert(engine, conn, table, **kwargs):
    import sqlalchemy
    from sqlalchemy.dialects.mysql import insert
    metadata = sqlalchemy.MetaData()
    table_obj = sqlalchemy.Table(table, metadata, autoload=True, autoload_with=engine)
    insert_statement = insert(table_obj).values(**kwargs)
    on_duplicate = insert_statement.on_duplicate_key_update(**kwargs)
    return conn.execute(on_duplicate)


def create_user(username, password, mysql_user, mysql_password):
    import sqlalchemy
    from datetime import datetime
    import hashlib
    import uuid
    engine = sqlalchemy.create_engine('mysql+pymysql://' +
                                      mysql_user + ':' +
                                      mysql_password + '@127.0.0.1:3306/guacamole_db')
    conn = engine.connect()
    metadata = sqlalchemy.MetaData()
    guacamole_entity = sqlalchemy.Table('guacamole_entity', metadata, autoload=True, autoload_with=engine)
    guacamole_user = sqlalchemy.Table('guacamole_user', metadata, autoload=True, autoload_with=engine)
    sql_insert(engine, conn, 'guacamole_entity',
               name=username,
               type='USER')
    entity_id = sqlalchemy.select([guacamole_entity]).where(guacamole_entity.columns.name == username)
    result = conn.execute(entity_id)
    entity_id_value = result.fetchone()[0]
    password_salt = hashlib.sha256(str(uuid.uuid1().bytes).encode('utf-8'))
    password_hash = hashlib.sha256((password + password_salt.hexdigest().upper()).encode('utf-8'))
    sql_insert(engine, conn, 'guacamole_user',
               entity_id=entity_id_value,
               password_hash=password_hash.digest(),
               password_salt=password_salt.digest(),
               password_date=datetime.now())


def update_user_permissions(mysql_user, mysql_password):
    import sqlalchemy
    engine = sqlalchemy.create_engine('mysql+pymysql://' +
                                      mysql_user + ':' +
                                      mysql_password + '@127.0.0.1:3306/guacamole_db')
    conn = engine.connect()
    connections = [row['connection_id'] for row in
                   engine.execute('SELECT connection_id FROM guacamole_connection').fetchall()]
    entities = [row['entity_id'] for row in engine.execute('SELECT entity_id FROM guacamole_entity').fetchall()]
    guacadmin_entity_id = engine.execute('SELECT entity_id FROM guacamole_entity WHERE name = "guacadmin"').fetchone()[
        'entity_id']
    for entity_id in entities:
        if entity_id == guacadmin_entity_id:
            for connection_id in connections:
                sql_insert(engine, conn, 'guacamole_connection_permission',
                           entity_id=entity_id,
                           connection_id=connection_id,
                           permission='UPDATE')
                sql_insert(engine, conn, 'guacamole_connection_permission',
                           entity_id=entity_id,
                           connection_id=connection_id,
                           permission='DELETE')
                sql_insert(engine, conn, 'guacamole_connection_permission',
                           entity_id=entity_id,
                           connection_id=connection_id,
                           permission='ADMINISTER')
            for affected_user_id in entities:
                sql_insert(engine, conn, 'guacamole_user_permission',
                           entity_id=entity_id,
                           affected_user_id=affected_user_id,
                           permission='UPDATE')
                sql_insert(engine, conn, 'guacamole_user_permission',
                           entity_id=entity_id,
                           affected_user_id=affected_user_id,
                           permission='ADMINISTER')
                sql_insert(engine, conn, 'guacamole_user_permission',
                           entity_id=entity_id,
                           affected_user_id=affected_user_id,
                           permission='DELETE')
        for connection_id in connections:
            sql_insert(engine, conn, 'guacamole_connection_permission',
                       entity_id=entity_id,
                       connection_id=connection_id,
                       permission='READ')
            sql_insert(engine, conn, 'guacamole_user_permission',
                       entity_id=entity_id,
                       affected_user_id=entity_id,
                       permission='READ')


def create_connection(mysql_user, mysql_password, connection):
    import sqlalchemy
    engine = sqlalchemy.create_engine('mysql+pymysql://' +
                                      mysql_user + ':' +
                                      mysql_password + '@127.0.0.1:3306/guacamole_db')
    conn = engine.connect()
    sql_insert(engine, conn, 'guacamole_connection',
               **connection['connection'])
    conn_name = connection['connection']['connection_name']
    connection_id = engine.execute('SELECT connection_id from guacamole_connection WHERE connection_name = "' +
                                   conn_name + '";').fetchone()['connection_id']
    for parameter_name, parameter_value in connection['parameters'].items():
        sql_insert(engine, conn, 'guacamole_connection_parameter',
                   connection_id=connection_id,
                   parameter_name=parameter_name,
                   parameter_value=parameter_value)


def random_string(stringLength=10):
    import string
    import random
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def get_group_members(ldap_server, ldap_user, ldap_password, ldap_domain, ldap_group, type='User', **kwargs):
    from ldap3 import Server, Connection, ALL, NTLM, ALL_ATTRIBUTES
    import json
    d1, d2 = ldap_domain.split('.')
    server = Server(ldap_server,
                    get_info=ALL)
    conn = Connection(server=server,
                      user=d1 + '\\' + ldap_user,
                      password=ldap_password,
                      auto_bind=True,
                      auto_referrals=False,
                      authentication=NTLM)
    conn.bind()
    conn.search('dc=' + d1 + ',dc=' + d2 + '',
                '(&(objectCategory=' + type +
                ')(memberOf:1.2.840.113556.1.4.1941:=CN=' +
                str(ldap_group) + ',CN=Users,DC=' + d1 + ',DC=' + d2 + '))',
                attributes=ALL_ATTRIBUTES)
    results = json.loads(conn.response_to_json())
    conn.unbind()
    return results


def parse_arguments(arguments_yaml_file='arguments.yaml'):
    import argparse
    from pydoc import locate
    with open(arguments_yaml_file, 'r') as y:
        data = yaml.load(y, Loader=yaml.FullLoader)
        parser = argparse.ArgumentParser()
        for argument, parameters in data.items():
            if 'type' in parameters.keys():
                parameters['type'] = locate(parameters['type'])
            parser.add_argument('--' + argument, **parameters)
        return parser.parse_args()


def check_container_status(container_name, timeout):
    import docker
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


def isOpen(ip,port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False


if __name__ == '__main__':
    import subprocess
    import yaml
    import shutil
    import docker
    import os

    args = vars(parse_arguments('arguments.yaml'))
    params = yaml.load(open('./parameters.yaml', 'r'), Loader=yaml.FullLoader)
    client = docker.from_env()

    if args['clean']:
        print("Running docker-compose down...")
        try:
            docker_compose_cmd = subprocess.run(['docker-compose down'], shell=True, check=True, capture_output=True)
            print(docker_compose_cmd.stdout.decode('utf-8'))
            print(docker_compose_cmd.stderr.decode('utf-8'))
        except:
            print(docker_compose_cmd.stdout.decode('utf-8'))
            print(docker_compose_cmd.stderr.decode('utf-8'))
        print("Clearing generated directories...")
        client.containers.prune()
        client.volumes.prune()
        client.images.prune()
        for folder in ['./shared',
                       './mysql',
                       './init']:
            if os.path.exists(folder):
                shutil.rmtree(folder)
        if args['nginx']:
            if os.path.exists('./nginx/conf'):
                shutil.rmtree('./nginx/conf')

    if args['configs'] or args['deploy']:
        import string

        print("Generating configs...")

        for folder in ['./guacamole_home',
                       './guacamole_home/extensions',
                       './nginx',
                       './nginx/conf',
                       './nginx/certs',
                       './nginx/auth']:
            if not os.path.exists(folder):
                os.makedirs(folder)
        if args['nginx']:
            nginx_conf_template = string.Template(open('./templates/nginx_conf.template', 'r').read())
            with open('./nginx/conf/nginx.conf', 'w') as f:
                f.write(nginx_conf_template.substitute(**params))
        guacamole_properties_template = string.Template(open('./templates/guacamole.properties.template', 'r').read())
        with open('./guacamole_home/guacamole.properties', 'w') as f:
            f.write(guacamole_properties_template.substitute(**params))
        docker_compose_template = string.Template(open('./templates/docker-compose.yml.template', 'r').read())
        with open('./docker-compose.yml', 'w') as f:
            f.write(docker_compose_template.substitute(**params))
        mysql_init_template = string.Template(open('./templates/initdb.sh.template', 'r').read())
        with open('./mysql_init/initdb.sh', 'w') as f:
            f.write(mysql_init_template.substitute(**params))

        #git_clone_cmd = subprocess.run('git clone https://github.com/apache/guacamole-client.git', shell=True, capture_output=True)
        #print(git_clone_cmd.stderr.decode('utf-8'))
        #print(git_clone_cmd.stdout.decode('utf-8'))
        #docker_build_cmd = subprocess.run('docker build guacamole-client', shell=True, capture_output=True)
        #print(docker_build_cmd.stderr.decode('utf-8'))
        #print(docker_build_cmd.stdout.decode('utf-8'))

    if args['deploy']:
        print("Deploying...")
        try:
            docker_compose_cmd = subprocess.run(['docker-compose pull'], shell=True, check=True, capture_output=True)
            print(docker_compose_cmd.stdout.decode('utf-8'))
            print(docker_compose_cmd.stderr.decode('utf-8'))
        except:
            print(docker_compose_cmd.stderr.decode('utf-8'))
        try:
            docker_compose_cmd = subprocess.run(['docker-compose up -d'], shell=True, check=True, capture_output=True)
            print(docker_compose_cmd.stdout.decode('utf-8'))
            print(docker_compose_cmd.stderr.decode('utf-8'))
        except:
            print(docker_compose_cmd.stderr.decode('utf-8'))

    if args['create_users']:
        import time
        import string
        import random
        print("Creating users...")
        print("Checking mysql availability...")
        check_container_status('mysql', 120)
        create_user(username='guacadmin',
                    password=params['guacadmin_password'],
                    mysql_user=params['mysql_user'],
                    mysql_password=params['mysql_password'])
        users = get_group_members(**params['ldap_servers']['users'], type='User')
        for user in users['entries']:
            create_user(username=user['attributes']['sAMAccountName'],
                        password=''.join(random.choice(string.ascii_lowercase) for i in range(25)),
                        mysql_user=params['mysql_user'],
                        mysql_password=params['mysql_password'])

    if args['create_connections']:
        import time
        print("Creating connections...")
        print("Checking mysql availability...")
        check_container_status('mysql', 120)
        computers = get_group_members(**params['ldap_servers']['connections'], type='Computer')
        for computer in computers['entries']:
            if params['auto_connection_dns']:
                hostname = computer['attributes']['dNSHostName']
                conn_name = hostname
            else:
                import dns.resolver
                dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
                dns.resolver.default_resolver.nameservers = [params['auto_connection_dns_resolver']]
                hostname = dns.resolver.resolve(computer['attributes']['dNSHostName'], 'a').response.answer[0][0].address
                conn_name = computer['attributes']['dNSHostName'] + " - " + hostname
            connection = params['auto_connections']
            connection['connection']['connection_name'] = conn_name
            connection['parameters']['hostname'] = hostname
            create_connection(mysql_user=params['mysql_user'],
                              mysql_password=params['mysql_password'],
                              connection=connection)
        if 'manual_connections' in params.keys():
            for connection in params['manual_connections']:
                create_connection(mysql_user=params['mysql_user'],
                                  mysql_password=params['mysql_password'],
                                  connection=connection)

    if args['create_connections'] or args['create_users'] or args['update_permissions']:
        update_user_permissions(mysql_user=params['mysql_user'],
                                mysql_password=params['mysql_password'])

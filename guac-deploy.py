import yaml
import shutil
import docker
from string import Template
import os


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


if __name__ == '__main__':
    args = vars(parse_arguments('arguments.yaml'))
    params = yaml.load(open('./parameters.yaml', 'r'), Loader=yaml.FullLoader)

    if args['clean']:
        print("Clearing generated directories...")
        client = docker.from_env()
        client.containers.prune()
        client.volumes.prune()
        client.images.prune()
        shutil.rmtree('./shared')
        shutil.rmtree('./mysql')
        shutil.rmtree('./nginx')
        shutil.rmtree('./init')
        shutil.rmtree('./mysql')

    if args['configs_only'] or args['deploy']:
        print("Generating configs...")

        for folder in ['./guacamole_home',
                     './guacamole_home/extensions',
                     './nginx',
                     './nginx/conf',
                     './nginx/certs',
                     './nginx/auth']:
            if not os.path.exists(folder):
                os.makedirs(folder)

        nginx_conf_template = Template(open('./templates/nginx_conf.template', 'r').read())
        with open('./nginx/conf/nginx.conf', 'w') as f:
            f.write(nginx_conf_template.substitute(**params))
        guac_properties_template = Template(open('./templates/guac_properties.template', 'r').read())
        with open('./guacamole_home/guacamole.properties' 'w') as f:
            f.write(guac_properties_template.substitute(**params))
        docker_compose_template = Template(open('./templates/docker_compose.template', 'r').read())
        with open('./docker-compose.yml', 'w') as f:
            f.write(docker_compose_template.substitute(**params))

    if args['deploy']:
        print("Deploying...")

    if args['create_users']:
        pass

    if args['create_connections']:
        pass
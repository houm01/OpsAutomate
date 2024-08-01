#!/usr/bin/env python3

import yaml
from pathlib import Path
from nb_log import get_logger

from jinja2 import FileSystemLoader, Environment


log = get_logger('build_config')

config_path = Path.cwd() / 'telegraf_config'
# log.debug(config_path)
jinja2_path = config_path / 'jinja2'
output_path = config_path / 'output'
config_yaml = config_path / 'edit' /'config.yaml'
resources_yaml = config_path / 'edit' / 'resources.yaml'


def render_config(location, monitor_type, config, instances):
    
    j2_loader = FileSystemLoader(jinja2_path)
    env = Environment(loader=j2_loader)
    j2_tmpl = env.get_template('telegraf_config.j2')

    result = j2_tmpl.render(config=config, monitor_type=monitor_type, instances=instances)
    
    with open(output_path / f'telegraf_{location}_{monitor_type}.conf', 'w') as f:
        f.write(result)


def get_resources_by_yaml():
    with open(resources_yaml, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f.read())
        

def get_config_by_yaml():
    with open(config_yaml, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f.read())

print(get_resources_by_yaml())

for monitor_type, values in get_resources_by_yaml().items():
    for location, instances in values.items():
        log.warning(location)
        render_config(location=location, monitor_type=monitor_type, config=get_config_by_yaml(), instances=instances)

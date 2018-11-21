import os
import yaml


def choose_sonnet_path(sonnet_path, version='', license_id=''):
    assert os.path.isdir(sonnet_path), "'{}' is not a directory".format(sonnet_path)
    assert os.path.isfile(os.path.join(sonnet_path, 'bin', 'em')), \
        "the sonnet directory has an unrecognizable format"
    directory = os.path.dirname(__file__)
    load_path = os.path.join(directory, 'default_configuration.yaml')
    with open(load_path, "r") as file_handle:
        default = yaml.load(file_handle)
    default['sonnet']['sonnet_path'] = sonnet_path
    default['sonnet']['version'] = version
    default['sonnet']['license_id'] = license_id

    with open('user_configuration.yaml') as file_handle:
        yaml.dump(default, file_handle, default_flow_style=False)
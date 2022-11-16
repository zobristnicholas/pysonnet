import os
import yaml
import psutil
import logging
import subprocess


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def test_sonnet(sonnet_path):
    """
    Test sonnet and output the version and license info.
    :param sonnet_path: The main sonnet folder path.
        The directory containing the sonnet program. Inside this
        directory should be a 'bin' folder with the 'em' routine.
    :return: a tuple of the sonnet version string and the license string
    """
    log.info("Testing sonnet")
    # Check to see if we have a valid path.
    em_path = os.path.join(sonnet_path, 'bin', 'em')
    if not os.path.isfile(em_path):
        raise ValueError("Invalid sonnet path")

    version = ''
    license_id = ''
    success = False
    with psutil.Popen([em_path, "-test"], stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE) as process:
        while True:
            output = process.stdout.readline()
            if not output and process.poll() is not None:
                break
            message = output.decode('utf-8').strip()
            if message:
                log.info(message)
            if message.lower().startswith("version"):
                # Grab the version number.
                version = message.lower().split("version", 1)[1].strip()
            if message.lower().startswith("run"):
                # Grab the license making sure to remove the trailing period.
                license_id = ".".join(message.split()[-1].split(".")[:-1])
            if message.lower().startswith("em simulation completed"):
                success = True
        while True:
            error = process.stderr.readline()
            if not error and process.poll() is not None:
                break
            message = error.decode('utf-8').strip()
            if message:
                log.error(message)

    if not success:
        raise RuntimeError("The sonnet test was unsuccessful.")
    if not version:
        raise RuntimeError("The sonnet version could not be determined.")
    if not license_id:
        raise RuntimeError("The sonnet license could not be determined.")

    return version, license_id


def configure_sonnet(sonnet_path):
    """
    Configure sonnet on this system. The changes made are global to this
    installation of pysonnet.

    :param sonnet_path: The main sonnet folder path.
        The directory containing the sonnet program. Inside this
        directory should be a 'bin' folder with the 'em' routine.
    :return:
    """
    # Load the default configuration.
    directory = os.path.dirname(__file__)
    load_path = os.path.join(directory, 'default_configuration.yaml')
    with open(load_path, "r") as file_handle:
        default = yaml.load(file_handle, Loader=yaml.FullLoader)

    version, license_id = test_sonnet(sonnet_path)

    # Overwrite the default configuration values.
    default['sonnet']['sonnet_path'] = sonnet_path
    default['sonnet']['version'] = version
    default['sonnet']['license_id'] = license_id
    with open(load_path, "w") as file_handle:
        yaml.dump(default, file_handle, default_flow_style=False)

import os
import abc
import yaml
import psutil
import logging
import subprocess
import pysonnet.blocks as b


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Configuration(dict):
    """Configuration management class for the Project class."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections = ['sonnet', 'header', 'dimensions', 'geometry', 'frequency',
                         'control', 'optimization', 'parameter_sweep', 'output_file',
                         'parameter_netlist', 'circuit', 'subdivider',
                         'quick_start_guide', 'component_data_files', 'translators']

    def load(self, config_path):
        log.debug("loading configuration from '{}'".format(config_path))
        self.clear()
        with open(config_path, "r") as file_handle:
            configuration = yaml.load(file_handle)
        for block in configuration.keys():
            if block not in self.sections:
                message = "{} is an unrecognized configuration section"
                raise ValueError(message.format(block))
        log.debug("configuration loaded")

    def save(self, config_path):
        log.debug("saving current configuration to '{}'".format(config_path))
        with open(config_path) as file_handle:
            yaml.dump(self, file_handle, default_flow_style=False)
        log.debug("configuration saved")

    def _check_geometry_project(self):
        log.debug("verifying geometry project")
        invalid_section_message = ("'{}' is an invalid configuration section for a "
                                   "geometry project")
        required_section_message = ("'{}' is a required configuration section for a "
                                    "geometry project")
        self._check_universal_sections(required_section_message)
        self._check_section('geometry', required_section_message)
        self._check_section('subdivider', required_section_message)
        self._check_section('quick_start_guide', required_section_message)

        self._check_not_section('parameter_netlist', invalid_section_message)
        self._check_not_section('circuit', invalid_section_message)
        log.debug("geometry project verified")

    def _check_netlist_project(self):
        log.debug("verifying netlist project")
        invalid_section_message = ("'{}' is an invalid configuration section for a "
                                   "netlist project")
        required_section_message = ("'{}' is a required configuration section for a "
                                    "netlist project")
        self._check_universal_sections(required_section_message)
        self._check_section('parameter_netlist', required_section_message)
        self._check_section('circuit', required_section_message)

        self._check_not_section('geometry', invalid_section_message)
        self._check_not_section('subdivider', invalid_section_message)
        self._check_not_section('quick_start_guide', invalid_section_message)
        log.debug("netlist project verified")

    def _check_universal_sections(self, required_section_message):
        required_field_message = "'{}' is a required field in the '{}' section"
        self._check_section('sonnet', required_section_message)
        self._check_field('sonnet', 'sonnet_path', required_field_message)
        self._check_field('sonnet', 'version', required_field_message)
        self._check_section('header', required_section_message)
        self._check_section('dimensions', required_section_message)
        self._check_section('frequency', required_section_message)
        self._check_section('optimization', required_section_message)
        self._check_section('parameter_sweep', required_section_message)
        self._check_section('output_file', required_section_message)
        self._check_section('component_data_files', required_section_message)
        self._check_section('translators', required_section_message)

    def _check_field(self, section, field, message):
        assert field in self[section], message.format(field, section)

    def _check_section(self, section, message):
        assert section in self.keys(), message.format(section)

    def _check_not_section(self, section, message):
        assert section not in self.keys(), message.format(section)


class Project(abc.ABC):
    """
    Abstract base class for the Geometry and Netlist Projects. It can not be instantiated.
    :param config_path: path to the configuration file for this project (optional)
    """
    def __init__(self, config_path=None):
        self.cfg = Configuration()
        self.project_file_path = None
        if config_path is not None:
            self.load(config_path)

    @abc.abstractmethod
    def make_sonnet_file(self, file_path):
        """
        Convert this project into a Sonnet file.
        :param file_path: path where the file will be saved.
        """
        pass

    @abc.abstractmethod
    def save(self, config_path):
        """
        Save the settings for this project into a yaml file.
        :param config_path: path where the settings will be saved.
        """
        pass

    @abc.abstractmethod
    def load(self, config_path):
        """
        Load the settings for this project from a yaml file.
        :param config_path: path where the settings will be saved.
        """
        pass

    def run(self, file_path=None):
        """
        Run the project simulation.
        :param file_path: path where the Sonnet file will be saved (optional if already
                          made)
        """
        if file_path is not None:
            self.make_sonnet_file(file_path)
        if self.project_file_path is None:
            message = ("run make_sonnet_file() or provide the 'file_path' argument "
                       "before running the simulation")
            raise ValueError(message)
        options = ''  # options not implemented
        external_frequency_file = ''  # external_frequency_file not implemented
        command = (os.path.join(self.cfg["sonnet_path"], "bin", "em ") + options +
                   self.project_file_path + external_frequency_file)
        with psutil.Popen(command, stdout=subprocess.PIPE) as process:
            log.info(process.stdout.read())


class GeometryProject(Project):
    """
    Class for creating and manipulating a Sonnet geometry project.
    """
    def make_sonnet_file(self, file_path):
        # convert cfg format to file_string
        file_string = (b.GEOMETRY_PROJECT.format(**self.cfg['sonnet']) +
                       b.HEADER.format(**self.cfg['header']) +
                       b.DIMENSIONS.format(**self.cfg['dimensions']) +
                       b.GEOMETRY.format(**self.cfg['geometry']) +
                       b.FREQUENCY.format(**self.cfg['frequency']) +
                       b.CONTROL.format(**self.cfg['control']) +
                       b.OPTIMIZATION.format(**self.cfg['optimization']) +
                       b.PARAMETER_SWEEP.format(**self.cfg['parameter_sweep']) +
                       b.OUTPUT_FILE.format(**self.cfg['output_file']) +
                       b.SUBDIVIDER.format(**self.cfg['subdivider']) +
                       b.QUICK_START_GUIDE.format(**self.cfg['quick_start_guide']) +
                       b.COMPONENT_DATA_FILES.format(**self.cfg['component_data_files']) +
                       b.TRANSLATORS.format(**self.cfg['translators']))

        log.debug("saving geometry project to '{}'".format(file_path))
        with open(file_path, "w") as file_handle:
            file_handle.write(file_string)
        log.debug("geometry project saved")
        self.project_file_path = file_path

    def save(self, config_path):
        self.cfg._check_geometry_project()
        self.cfg.save(config_path)

    def load(self, config_path):
        self.cfg.load(config_path)
        self.cfg._check_geometry_project()


class NetlistProject(Project):
    """
    Class for creating and manipulating a Sonnet netlist project.
    """
    def make_sonnet_file(self, file_path):
        file_string = (b.NETLIST_PROJECT.format(**self.cfg['sonnet']) +
                       b.HEADER.format(**self.cfg['header']) +
                       b.DIMENSIONS.format(**self.cfg['dimensions']) +
                       b.FREQUENCY.format(**self.cfg['frequency']) +
                       b.CONTROL.format(**self.cfg['control']) +
                       b.OPTIMIZATION.format(**self.cfg['optimization']) +
                       b.PARAMETER_SWEEP.format(**self.cfg['parameter_sweep']) +
                       b.OUTPUT_FILE.format(**self.cfg['output_file']) +
                       b.PARAMETER_NETLIST.format(**self.cfg['parameter_netlist']) +
                       b.CIRCUIT.format(**self.cfg['circuit']) +
                       b.QUICK_START_GUIDE.format(**self.cfg['quick_start_guide']) +
                       b.COMPONENT_DATA_FILES.format(**self.cfg['component_data_files']) +
                       b.TRANSLATORS.format(**self.cfg['translators']))
        log.debug("saving netlist project to '{}'".format(file_path))
        with open(file_path, "w") as file_handle:
            file_handle.write(file_string)
        log.debug("netlist project saved")
        self.project_file_path = file_path

    def save(self, config_path):
        self.cfg._check_netlist_project()
        self.cfg.save(config_path)

    def load(self, config_path):
        self.cfg.load(config_path)
        self.cfg._check_netlist_project()

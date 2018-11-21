import os
import yaml
import psutil
import logging
import subprocess
import pysonnet.blocks as b
from datetime import datetime


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Project(dict):
    """
    Abstract base class for the Geometry and Netlist Projects. It should not be
    instantiated.

    :param load_path: path to the yaml file for this project if it was saved (optional)
    """
    def __init__(self, load_path=None):
        super().__init__()
        self.project_file_path = None
        self.sections = ['sonnet', 'dimensions', 'frequency', 'geometry', 'control',
                         'optimization', 'parameter_sweep', 'output_file',
                         'parameter_netlist', 'circuit', 'subdivider',
                         'quick_start_guide', 'component_data_files', 'translators']
        if load_path is not None:
            self.load(load_path)
        else:
            directory = os.path.dirname(__file__)
            load_path = os.path.join(directory, 'user_configuration.yaml')
            if not os.path.isfile(load_path):
                load_path = os.path.join(directory, 'default_configuration.yaml')
            self.load(load_path)

    def make_sonnet_file(self, file_path):
        """
        Convert the current state of this project into a Sonnet file.

        :param file_path: path where the file will be saved.
        """
        raise NotImplementedError

    def load(self, load_path):
        log.debug("loading configuration from '{}'".format(load_path))
        self.clear()
        # load configuration
        with open(load_path, "r") as file_handle:
            configuration = yaml.load(file_handle)
        for block in configuration.keys():
            if block not in self.sections:
                message = "{} is an unrecognized configuration section"
                raise ValueError(message.format(block))
        # add configuration to the object
        self.update(configuration)
        # add date if it doesn't exist
        if self['sonnet']['date'] == '':
            self['sonnet']['date'] = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        log.debug("configuration loaded")

    def save(self, save_path):
        log.debug("saving current configuration to '{}'".format(save_path))
        self['sonnet']['date'] = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        with open(save_path) as file_handle:
            yaml.dump(dict(self), file_handle, default_flow_style=False)
        log.debug("configuration saved")

    def run(self, file_path=None, options='-v', external_frequency_file=None):
        """
        Run the project simulation.

        :param file_path: path where the Sonnet file will be saved (optional)
            This parameter is optional if a Sonnet file has already been made and is
            consistent with the current project state.
        :param options: extra command line options to pass to Sonnet em
            Valid options are given on page 414 of the sonnet_users_guide.pdf. Verbose
            is turned on by default and the output is sent to the program log.
        :param external_frequency_file: path to the frequency control file (optional)
        """
        # check to make sure there is a project file to run
        if file_path is not None:
            self.make_sonnet_file(file_path)
        if self.project_file_path is None:
            message = ("run make_sonnet_file() or provide the 'file_path' argument "
                       "before running the simulation")
            raise ValueError(message)
        # check to make sure that sonnet has been configured
        if self["sonnet_path"] == '':
            raise ValueError("configure sonnet before running")
        # collect the command to run
        command = [os.path.join(self["sonnet_path"], "bin", "em "), options,
                   self.project_file_path, external_frequency_file]
        command = [element for element in command
                   if (element != '' and element != '-' and element is not None)]
        # run the command
        with psutil.Popen(command, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as process:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    log.info(output.strip())

    def locate_sonnet(self, sonnet_path, version='', license_id=''):
        """
        Provide the project with the path to the Sonnet folder so that it can be run.

        :param sonnet_path: path to the Sonnet program
        :param version: Sonnet version number
        :param license_id: user license ID
        """
        assert os.path.isdir(sonnet_path), "'{}' is not a directory".format(sonnet_path)
        assert os.path.isfile(os.path.join(sonnet_path, 'bin', 'em')), \
            "the sonnet directory has an unrecognizable format"
        self['sonnet_path'] = sonnet_path
        self['version'] = version
        self['license_id'] = license_id

    def add_frequency_sweep(self):
        """Add a frequency sweep to the analysis for the project."""
        raise NotImplementedError

    def add_parameter_sweep(self):
        """Add a parameter sweep to the analysis for the project."""
        raise NotImplementedError

    def add_output_file(self):
        """Add an output file for the result of the analysis for the project."""
        raise NotImplementedError


class GeometryProject(Project):
    """
    Class for creating and manipulating a Sonnet geometry project.
    """
    def make_sonnet_file(self, file_path):
        # convert cfg format to file_string
        file_string = (b.GEOMETRY_PROJECT.format(**self['sonnet']) +
                       b.HEADER.format(**self['sonnet']) +
                       b.DIMENSIONS.format(**self['dimensions']) +
                       b.FREQUENCY.format(**self['frequency']) +
                       b.CONTROL.format(**self['control']) +
                       b.GEOMETRY.format(**self['geometry']) +
                       b.OPTIMIZATION.format(**self['optimization']) +
                       b.PARAMETER_SWEEP.format(**self['parameter_sweep']) +
                       b.OUTPUT_FILE.format(**self['output_file']) +
                       b.SUBDIVIDER.format(**self['subdivider']) +
                       b.QUICK_START_GUIDE.format(**self['quick_start_guide']) +
                       b.COMPONENT_DATA_FILES.format(**self['component_data_files']) +
                       b.TRANSLATORS.format(**self['translators']))

        log.debug("saving geometry project to '{}'".format(file_path))
        with open(file_path, "w") as file_handle:
            file_handle.write(file_string)
        log.debug("geometry project saved")
        self.project_file_path = file_path

    def configure_sonnet(self, sonnet_path):
        """Setup sonnet by providing the path to the enclosing folder"""

    def add_reference_plane(self):
        """Adds a reference plane to one side of the box."""
        raise NotImplementedError

    def define_metal(self):
        """Defines a metal that can be used in the project."""
        raise NotImplementedError

    def add_dimension(self):
        """Adds a dimension to the simulation geometry."""
        raise NotImplementedError

    def define_dielectric(self):
        """Defines a dielectric that can be used in the project."""
        raise NotImplementedError

    def add_variable(self, box_size_x=False, box_size_y=False):
        """Adds a variable to the project."""
        raise NotImplementedError

    def add_parameter(self):
        """Adds a dimension parameter to the project."""
        raise NotImplementedError

    def setup_box(self, box_width_x, box_width_y, x_cells, y_cells):
        """Set up box size and cell spacing.

        :param box_width_x: length of the box in the x direction (float)
        :param box_width_y: length of the box in the y direction (float)
        :param x_cells: number of cells in the x direction (int)
        :param y_cells: number of cells in the y direction (int)
        """
        self['box_width_x'] = float(box_width_x)
        self['box_width_y'] = float(box_width_y)
        self['x_cells2'] = 2 * int(x_cells)
        self['y_cells2'] = 2 * int(y_cells)

    def choose_layers(self):
        """Choose the dielectric layers to be used in the project."""
        raise NotImplementedError

    def define_technology_layer(self):
        """Defines a technology layer for the project."""
        raise NotImplementedError

    def add_edge_via(self):
        """Adds an edge via to the project."""
        raise NotImplementedError

    def set_origin(self):
        """Sets the origin for the project."""
        raise NotImplementedError

    def add_port(self):
        """Adds a port to the project."""
        raise NotImplementedError

    def add_calibration_group(self):
        """Adds a calibration group to the project."""
        raise NotImplementedError

    def add_component(self):
        """Adds a component to the project."""
        raise NotImplementedError

    def add_polygons(self):
        """Adds polygons to the project."""
        raise NotImplementedError


class NetlistProject(Project):
    """
    Class for creating and manipulating a Sonnet netlist project.
    """
    def make_sonnet_file(self, file_path):
        file_string = (b.NETLIST_PROJECT.format(**self['sonnet']) +
                       b.HEADER.format(**self['sonnet']) +
                       b.DIMENSIONS.format(**self['dimensions']) +
                       b.FREQUENCY.format(**self['frequency']) +
                       b.CONTROL.format(**self['control']) +
                       b.OPTIMIZATION.format(**self['optimization']) +
                       b.PARAMETER_SWEEP.format(**self['parameter_sweep']) +
                       b.OUTPUT_FILE.format(**self['output_file']) +
                       b.PARAMETER_NETLIST.format(**self['parameter_netlist']) +
                       b.CIRCUIT.format(**self['circuit']) +
                       b.QUICK_START_GUIDE.format(**self['quick_start_guide']) +
                       b.COMPONENT_DATA_FILES.format(**self['component_data_files']) +
                       b.TRANSLATORS.format(**self['translators']))
        log.debug("saving netlist project to '{}'".format(file_path))
        with open(file_path, "w") as file_handle:
            file_handle.write(file_string)
        log.debug("netlist project saved")
        self.project_file_path = file_path

    def create_circuit(self):
        raise NotImplementedError

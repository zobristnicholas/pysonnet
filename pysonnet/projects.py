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

    def run(self, sweep_type, file_path=None, options='-v', external_frequency_file=None):
        """
        Run the project simulation.

        :param sweep_type: type of sweep to compute
            Valid options are 'frequency', 'parameter', or 'optimize'. The sweep
            corresponding to the sweep_type must have already been added to the project
            using add_frequency_sweep(), add_parameter_sweep(), or add_optimization().
            All sweeps of the specified type will be computed.
        :param file_path: path where the Sonnet file will be saved (optional)
            This parameter is optional if a Sonnet file has already been made and is
            consistent with the current project state.
        :param options: extra command line options to pass to Sonnet em
            Valid options are given on page 414 of the sonnet_users_guide.pdf. Verbose
            is turned on by default and the output is sent to the program log.
        :param external_frequency_file: path to the frequency control file (optional)
        """
        # check sweep_type
        message = "sweep_type must be either 'frequency' or 'parameter'"
        assert sweep_type in ['frequency', 'parameter', 'optimize'], message
        message = "add a sweep to the project before running"
        assert (self['frequency']['sweeps'] != '' or
                self['parameter_sweeps']['parameter_sweep'] != '' or
                self['optimization']['optimization_goals'] != ''), message
        # set sweep type
        if sweep_type == 'frequency':
            self['control']['sweep_type'] = "STD"
        elif sweep_type == 'parameter':
            self['control']['sweep_type'] = "VARSWP"
        else:
            self['control']['sweep_type'] = "OPTIMIZE"
        # check to make sure there is a project file to run
        if file_path is not None:
            self.make_sonnet_file(file_path)
        if self.project_file_path is None:
            message = ("run make_sonnet_file() or provide the 'file_path' argument "
                       "before running the simulation")
            raise ValueError(message)
        # check to make sure that sonnet has been configured
        if self['sonnet']["sonnet_path"] == '':
            raise ValueError("configure sonnet before running")
        # collect the command to run
        command = [os.path.join(self['sonnet']["sonnet_path"], "bin", "em "), options,
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
        self['sonnet']['sonnet_path'] = sonnet_path
        self['sonnet']['version'] = version
        self['sonnet']['license_id'] = license_id

    def add_frequency_sweep(self, sweep_type, f1=None, f2=None, n_points=None,
                            f_step=None, frequency_list=None, s_parameter=None):
        """
        Add a frequency sweep to the analysis for the project. All added sweeps will be
        computed if the 'frequency' sweep_type is selected using run().

        :param sweep_type: sweep type to add to the project (str)
            Valid options are listed below with the additional arguments that can be used
            for each. Refer to the Sonnet documentation for details on the sweep types.
            linear:
                f1, f2, and (n_points or f_step)
            exponential:
                f1, f2, and n_points
            single:
                f1
            list:
                frequency_list
            dc:
                f1 (optional in units of kHz), if not specified a value is calculated for
                you by Sonnet
            abs:
                f1 and f2
            abs_min:
                s_parameter, f1, and f2
            abs_max:
                s_parameter, f1 and f2
        :param f1: a frequency (float)
        :param f2: a frequency (float)
        :param n_points: number of points in the sweep (int)
        :param f_step: frequency step in the sweep (float)
        :param frequency_list: list of frequencies for the sweep (list of floats)
        :param s_parameter: name of the scattering parameter (str), e.g. "S21"
        """
        # define some messages to be used throughout the function
        f1_f2_message = "'f1' and 'f2' must be defined for this sweep"
        f1_message = "'f1' must be defined for this sweep"
        n_points_message = "'n_points' must be defined for this sweep"
        frequency_list_message = "'frequency_list' must be defined for this sweep"
        s_parameter_message = "'s_parameter' must be defined for this sweep"
        # type check the input parameters
        type_message = "'{}' parameter must be of type '{}'"
        if f1 is not None:
            assert isinstance(f1, (int, float)), type_message.format('f1', 'float')
        if f2 is not None:
            assert isinstance(f2, (int, float)), type_message.format('f2', 'float')
        if n_points is not None:
            assert isinstance(n_points, int), type_message.format('n_points', 'int')
        if f_step is not None:
            assert isinstance(f_step, (int, float)), \
                type_message.format('f_step', 'float')
        if frequency_list is not None:
            assert isinstance(frequency_list, (tuple, list)), \
                type_message.format('frequency_list', 'list')
            for frequency in frequency_list:
                message = "each frequency in 'frequency_list' must be a float"
                assert isinstance(frequency, (int, float)), message
        if s_parameter is not None:
            assert isinstance(s_parameter, str), type_message.format('s_parameter', 'str')
        # format the sweep string depending on sweep type
        if sweep_type == 'linear':
            assert f1 is not None and f2 is not None, f1_f2_message
            if f_step is not None and n_points is None:
                sweep = b.SWEEP_FORMAT.format(f1=f1, f2=f2, f_step=f_step)
            elif f_step is None and n_points is not None:
                sweep = b.LSWEEP_FORMAT.format(f1=f1, f2=f2, n_points=n_points)
            else:
                message = ("one of 'f_step' or 'n_points' must be specified for a linear "
                           "sweep")
                raise ValueError(message)
        elif sweep_type == 'exponential':
            assert f1 is not None and f2 is not None, f1_f2_message
            assert n_points is not None, n_points_message
            sweep = b.ESWEEP_FORMAT.format(f1=f1, f2=f2, n_points=n_points)
        elif sweep_type == 'single':
            assert f1 is not None, f1_message
            sweep = b.STEP_FORMAT.format(f1=f1)
        elif sweep_type == 'list':
            assert frequency_list is not None, frequency_list_message
            sweep = b.LIST_FORMAT
            for frequency in frequency_list:
                sweep.append(str(frequency) + ' ')
        elif sweep_type == 'dc':
            if f1 is None:
                sweep = b.DC_FORMAT.format(fcalc="AUTO", frequency='')
            else:
                sweep = b.DC_FORMAT.format(fcalc="MAN", frequency=f1)
        elif sweep_type == 'abs':
            assert f1 is not None and f2 is not None, f1_f2_message
            sweep = b.ABS_FORMAT.format(f1=f1, f2=f2)
        elif sweep_type == 'abs_min':
            assert f1 is not None and f2 is not None, f1_f2_message
            assert s_parameter is not None, s_parameter_message
            sweep = b.ABS_MIN_FORMAT.format(s_parameter=s_parameter, f1=f1, f2=f2)
        elif sweep_type == 'abs_max':
            assert f1 is not None and f2 is not None, f1_f2_message
            assert s_parameter is not None, s_parameter_message
            sweep = b.ABS_MAX_FORMAT.format(s_parameter=s_parameter, f1=f1, f2=f2)
        else:
            message = ("'sweep_type' must be one of the following: 'linear', "
                       "'exponential', 'single', 'list', 'dc', 'abs', 'abs_min', "
                       "or 'abs_max'")
            raise ValueError(message)
        # add the sweep to the project
        if self['frequency']['sweeps']:
            self['frequency']['sweeps'].append(os.linesep + sweep)
        else:
            self['frequency']['sweeps'].append(sweep)

    def clear_frequency_sweeps(self):
        """Removes all added frequency sweeps from the project."""
        self['frequency']['sweeps'] = ''

    def add_parameter_sweep(self):
        """Add a parameter sweep to the analysis for the project."""
        raise NotImplementedError

    def clear_parameter_sweeps(self):
        """Removes all added parameter sweeps from the project."""
        self['parameter_sweep']['parameter_sweep'] = ''

    def add_optimization(self):
        """Add an optimization to the analysis for the project."""
        raise NotImplementedError

    def clear_optimizations(self):
        """Removes all added optimizations from the project."""
        self['optimization']['optimization_parameters'] = ''
        self['optimization']['optimization_goals'] = ''

    def add_output_file(self):
        """Add an output file for the result of the analysis for the project."""
        raise NotImplementedError


class GeometryProject(Project):
    """
    Class for creating and manipulating a Sonnet geometry project.
    """
    def make_sonnet_file(self, file_path):
        # convert the project format to the file format
        file_string = (b.GEOMETRY_PROJECT.format(**self['sonnet']) +
                       b.HEADER.format(**self['sonnet']) +
                       b.DIMENSIONS.format(**self['dimensions']) +
                       b.GEOMETRY.format(**self['geometry']) +
                       b.FREQUENCY.format(**self['frequency']) +
                       b.CONTROL.format(**self['control']) +
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
        self.project_file_path = file_path
        log.debug("geometry project saved")

    def add_reference_plane(self, position, plane_type='fixed', length=None):
        """
        Adds a reference plane to one side of the box.

        :param position: defines the box wall from which the reference plane extends.
            Valid values are 'left', 'right', 'top', and 'bottom'.
        :param plane_type: defines the method used to set the location of the plane
            Valid values are 'fixed' and 'linked'. Fixed reference planes must also
            specify the length parameter.
        :param length: number specifying the length of the reference plane
        """
        # check position parameter
        message = "valid values for the position are 'left', 'right', 'top', and 'bottom'"
        assert position in ['left', 'right', 'top', 'bottom'], message
        # check type parameter
        types = {"fixed": "FIX", "FIX": "FIX", "linked": "LINK", "LINK": "LINK"}
        message = "valid values for the plane_type are 'fixed' and 'linked'"
        assert plane_type in types.keys(), message
        # choose type
        if types[plane_type] == "FIX":
            # check length
            message = "length parameter must be defined for a fixed-type reference plane"
            assert length is not None, message
            message = "length parameter must be a float or an int"
            assert isinstance(length, (float, int)), message
            # format the plane
            plane = b.REFERENCE_PLANES_FORMAT.format(position=position,
                                                     type=types[plane_type],
                                                     length=length)
        else:
            raise NotImplementedError
        # add the reference plane to the geometry
        if self['geometry']['reference_planes']:
            self['geometry']['reference_planes'].append(os.linesep + plane)
        else:
            self['geometry']['reference_planes'].append(plane)

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
    # convert the project format to the file format
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
        self.project_file_path = file_path
        log.debug("netlist project saved")

    def create_circuit(self):
        raise NotImplementedError

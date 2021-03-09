import os
import yaml
import shlex
import psutil
import logging
import subprocess
import numpy as np
import pysonnet.blocks as b
from datetime import datetime


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def add_line(string, addition):
    """Append to string adding new line if empty."""
    if string:
        string += os.linesep + addition
    else:
        string += addition


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
            configuration = yaml.load(file_handle, Loader=yaml.FullLoader)
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

    def set_analysis(self, analysis_type):
        """
        Set what kind of analysis to run.
         :param analysis_type:
            Valid options are listed below
            'frequency sweep': Runs all the sweeps added by add_frequency_sweep()
            'parameter sweep': Runs all the sweeps added by add_parameter_sweep()
            'optimization': Runs all the sweeps added by add_optimization()
        """
        message = "'analysis_type' parameter must be in {}"
        assert analysis_type in b.ANALYSIS_TYPES.keys(), \
            message.format(list(b.ANALYSIS_TYPES.values()))
        self['control']['analysis_type'] = b.ANALYSIS_TYPES[analysis_type]

    def set_options(self, current_density=False, frequency_cache=False,
                    memory_save=False, box_resonance=False, deembed=True,
                    q_accuracy=False, resonance_detection=False, custom=""):
        """
        Set the Sonnet options. Old options are overridden.

        :param current_density: compute the current density (boolean)
        :param frequency_cache: multi-frequency caching (boolean)
        :param memory_save: memory saver (boolean)
        :param box_resonance: box resonance detection (boolean)
        :param deembed: deembeds the project ports (boolean)
        :param q_accuracy: accurate line widths for resonators (boolean)
        :param resonance_detection: better resonance detection (boolean)
        :param custom: custom options for sonnet (string)
        """
        # add the main options to a string
        options_dict = {"current_density": current_density,
                        "frequency_cache": frequency_cache, "memory_save": memory_save,
                        "box_resonance": box_resonance, "deembed": deembed}
        options = "-"
        for key, value in options_dict.items():
            if value:
                log.debug("{} option selected".format(key))
                options += b.OPTION_TYPES[key]
        if custom:
            options += custom
            log.debug("'{}' custom option selected".format(custom))
        # add the options to the project
        self['control']['options'] = options
        # add other options
        self['control']['q_accuracy'] = "Y" if q_accuracy else "N"
        self['control']['res_detection'] = "Y" if resonance_detection else "N"
        log.debug("q factor accuracy {}".format("on" if q_accuracy else "off"))

    def run(self, analysis_type=None, file_path=None, options='-v',
            external_frequency_file=None):
        """
        Run the project simulation.

        :param analysis_type: all sweeps of the specified type will be computed.
            If it is not specified, it must have been set previously with
            set_analysis(). Valid options are listed below.
            'frequency sweep': Runs all the sweeps added by add_frequency_sweep()
            'parameter sweep': Runs all the sweeps added by add_parameter_sweep()
            'optimization': Runs all the sweeps added by add_optimization()
        :param file_path: path where the Sonnet file will be saved (optional)
            This parameter is optional if a Sonnet file has already been made and is
            consistent with the current project state.
        :param options: extra command line options to pass to Sonnet em
            Valid options are given on page 414 of the sonnet_users_guide.pdf. Verbose
            is turned on by default and the output is sent to the program log.
        :param external_frequency_file: path to the frequency control file (optional)
        """
        # check analysis_type
        if analysis_type is not None:
            self.set_analysis(analysis_type)
        else:
            message = "an analysis has not been selected yet"
            assert self['control']['analysis_type'], message
        message = "add a sweep to the project before running"
        assert (self['frequency']['sweeps'] != '' or
                self['parameter_sweeps']['parameter_sweep'] != '' or
                self['optimization']['optimization_goals'] != ''), message
        # set analysis type
        self['control']['analysis_type'] = b.ANALYSIS_TYPES[analysis_type]
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
        command = [os.path.join(self['sonnet']["sonnet_path"], "bin", "em"), options,
                   self.project_file_path, external_frequency_file]
        command = [element for element in command
                   if (element != '' and element != '-' and element is not None)]
        log.debug("running a(n) {}".format(analysis_type))
        # run the command
        with psutil.Popen(command, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as process:
            while True:
                output = process.stdout.readline().decode('utf-8')
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
        log.debug("sonnet path set to '{}'".format(sonnet_path))
        self['sonnet']['version'] = version
        log.debug("sonnet version to '{}'".format(version))
        self['sonnet']['license_id'] = license_id
        log.debug("license id set to '{}'".format(license_id))

    def add_frequency_sweep(self, sweep_type, **kwargs):
        """
        Add a frequency sweep to the analysis for the project. All added sweeps will be
        computed if the 'frequency' sweep_type is selected using run().

        :param sweep_type: sweep type to add to the project (str)
            Valid options are listed below with the additional keyword arguments that may
            be needed for each. Refer to the Sonnet documentation for details on the sweep
            types.
            'linear': compute on a linear range between f1 and f2 with n_points (f_step)
                :keyword f1: lower frequency (float)
                :keyword f2: upper frequency (float)
                :keyword n_points: number of points in the sweep, optional (integer)
                :keyword f_step: frequency step in the sweep, optional (float)
            'exponential': compute on an exponential range between f1 and f2
                :keyword f1: lower frequency (float)
                :keyword f2: upper frequency (float)
                :keyword n_points: number of points in the sweep (integer)
            'single': compute at a single frequency point
                :keyword f1: frequency (float)
            'list': compute at a list of frequencies
                :keyword frequency_list: frequencies list for the sweep (list of floats)
            'dc': compute a dc point
                :keyword f1: frequency (float)
                    This keyword is optional for a dc point calculation, but must be in
                    units of kHz. If it is not specified, a value is calculated for you by
                    Sonnet.
            'abs': compute using the adaptive band synthesis (ABS) sweep
                :keyword f1: lower frequency (float)
                :keyword f2: upper frequency (float)
            'abs min': compute the minimum of the s_parameter using the ABS sweep
                :keyword f1: lower frequency (float)
                :keyword f2: upper frequency (float)
                :keyword s_parameter: name of the scattering parameter (str), e.g. "S21"
            'abs max': compute the maximum of the s_parameter using the ABS sweep
                :keyword f1: lower frequency (float)
                :keyword f2: upper frequency (float)
                :keyword s_parameter: name of the scattering parameter (str), e.g. "S21"
        """
        # pull out the needed keyword arguments. The rest are ignored
        f1 = kwargs.pop('f1', None)
        f2 = kwargs.pop('f2', None)
        n_points = kwargs.pop('n_points', None)
        f_step = kwargs.pop('f_step', None)
        frequency_list = kwargs.pop('frequency_list', None)
        s_parameter = kwargs.pop('s_parameter', None)
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
        elif sweep_type == 'abs min':
            assert f1 is not None and f2 is not None, f1_f2_message
            assert s_parameter is not None, s_parameter_message
            sweep = b.ABS_MIN_FORMAT.format(s_parameter=s_parameter, f1=f1, f2=f2)
        elif sweep_type == 'abs max':
            assert f1 is not None and f2 is not None, f1_f2_message
            assert s_parameter is not None, s_parameter_message
            sweep = b.ABS_MAX_FORMAT.format(s_parameter=s_parameter, f1=f1, f2=f2)
        else:
            message = ("'sweep_type' must be one of the following: 'linear', "
                       "'exponential', 'single', 'list', 'dc', 'abs', 'abs min', "
                       "or 'abs max'")
            raise ValueError(message)
        # add the sweep to the project
        self['frequency']['sweeps'] += sweep + os.linesep
        log.debug("{} frequency sweep added".format(sweep_type))

    def clear_frequency_sweeps(self):
        """Removes all added frequency sweeps from the project."""
        self['frequency']['sweeps'] = ''
        log.debug("all frequency sweeps removed")

    def add_parameter_sweep(self):
        """Add a parameter sweep to the analysis for the project."""
        raise NotImplementedError

    def clear_parameter_sweeps(self):
        """Removes all added parameter sweeps from the project."""
        self['parameter_sweep']['parameter_sweep'] = ''
        log.debug("all parameter sweeps removed")

    def add_optimization(self):
        """Add an optimization to the analysis for the project."""
        raise NotImplementedError

    def clear_optimizations(self):
        """Removes all added optimizations from the project."""
        self['optimization']['optimization_parameters'] = ''
        self['optimization']['optimization_goals'] = ''
        log.debug("all optimizations removed")

    def set_units(self, **kwargs):
        """
        Set the base units for the project. This method will not maintain the physical
        size of any parameters already specified. Allowed keywords are listed below. Fully
        spelled units are supported as well as unicode Greek letters.

        :keyword conductivity: 'uS/cm', 'mS/cm', 'S/m' (default), and 'S/cm'
        :keyword frequency: 'Hz', 'kHz', 'MHz', 'GHz' (default), 'THz', and 'PHz'
        :keyword resistivity: 'ohm cm' (default) and 'ohm m'
        :keyword sheet_resistance: 'mohm/sq' and 'ohm/sq' (default)
        :keyword inductance: 'fH', 'pH', 'nH' (default), 'uH', 'mH', and 'H'
        :keyword length: 'um', 'mil' (default), 'mm', 'cm', 'in', 'ft', and 'm'
        :keyword angle: 'deg' (default)
        :keyword conductance: '1/ohm' (default)
        :keyword capacitance: 'fF', 'pF' (default), 'nF', 'uF', 'mF', and 'F'
        :keyword resistance: 'mohm', 'ohm' (default), 'kohm', 'Mohm', 'Gohm' and 'Tohm'
        """
        # check inputs
        message = "'{}' is not in {}"
        for key in kwargs.keys():
            assert key in b.UNITS.keys(), \
                message.format(key, list(b.UNITS.keys()))
            assert kwargs[key] in b.UNITS[key].keys(), \
                message.format(kwargs[key], list(b.UNITS[key].keys()))
        # add unit to the project
        for key, value in kwargs.items():
            self['dimensions'][key] = b.UNITS[key][value]
            log.debug("set {} unit to {}".format(key, b.UNITS[key][value]))


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
        folder = os.path.join(os.path.dirname(self.project_file_path), 'sondata')
        if not os.path.isdir(folder):
            os.mkdir(folder)
        subfolder = os.path.join(folder,  os.path.basename(file_path).split('.')[0])
        if not os.path.isdir(subfolder):
            os.mkdir(subfolder)
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
        message = "valid values for the plane_type are 'fixed' and 'linked'"
        assert plane_type in b.REFERENCE_PLANE_TYPES.keys(), message
        # choose type
        if b.REFERENCE_PLANE_TYPES[plane_type] == "FIX":
            # check length
            message = "length parameter must be defined for a fixed-type reference plane"
            assert length is not None, message
            message = "length parameter must be a float or an int"
            assert isinstance(length, (float, int)), message
            # format the plane
            plane = b.REFERENCE_PLANES_FORMAT.format(
                position=position, plane_type=b.REFERENCE_PLANE_TYPES[plane_type],
                length=length)
        else:
            raise NotImplementedError
        # add the reference plane to the geometry
        self['geometry']['reference_planes'] += plane + os.linesep
        log.debug("{}, {} reference plane added with a length of"
                  .format(position, plane_type, length))

    def define_metal(self, metal_type, name, **kwargs):
        """
        Defines a metal that can be used in the project.

        :param metal_type: type of metal to add to the project (string)
            Valid types are listed below with any additional keyword arguments that may be
            used with them. Where ambiguous, the parameters' units are determined by the
            project level units.
            'normal': cannot be used for vias
            'resistor': cannot be used for vias
            'native': cannot be used for vias
            'general': cannot be used for vias. All keywords are set to zero by default
                :keyword r_dc: DC resistance [(m)Ω/sq] (float)
                :keyword r_rf: skin effect coefficient [Ω/sqrt(Hz)/sq] (float)
                :keyword x_dc: DC reactance [(m)ohms/sq] (float)
                :keyword ls: surface inductance [pH/sq] (float)
            'sense': cannot be used for vias
            'thick metal': cannot be used for vias or the top and bottom layers
            'rough metal': cannot be used for vias or the top and bottom layers
            'volume loss': only for vias
            'surface loss': only for vias
            'array loss': only for vias
        :param name: metal name that must be unique in the project (string)
            The name can not be 'lossless' as this is reserved for the default lossless
            Sonnet metal.
        """
        # check name parameter
        message = "the name 'lossless' is reserved for the default Sonnet lossless metal"
        assert name != 'lossless', message
        # determine the pattern id and set the location string
        metals = self['geometry']['metals'].splitlines()
        pattern_id = len(metals) - 2
        location = "MET"
        # format the new metal
        if metal_type == 'normal':
            raise NotImplementedError
        elif metal_type == 'resistor':
            raise NotImplementedError
        elif metal_type == 'native':
            raise NotImplementedError
        elif metal_type == 'general':
            r_dc = kwargs.pop('r_dc', 0)
            r_rf = kwargs.pop('r_rf', 0)
            x_dc = kwargs.pop('x_dc', 0)
            ls = kwargs.pop('ls', 0)
            metal = b.GENERAL_METAL_FORMAT.format(location=location, name=name,
                                                  pattern_id=pattern_id, r_dc=r_dc,
                                                  r_rf=r_rf, x_dc=x_dc, ls=ls)
        elif metal_type == 'sense':
            raise NotImplementedError
        elif metal_type == 'thick metal':
            raise NotImplementedError
        elif metal_type == 'rough metal':
            raise NotImplementedError
        elif metal_type == 'volume loss':
            raise NotImplementedError
        elif metal_type == 'surface loss':
            raise NotImplementedError
        elif metal_type == 'array loss':
            raise NotImplementedError
        else:
            metal_types = ['normal', 'resistor', 'native', 'general', 'sense',
                           'thick metal', 'rough metal', 'volume loss', 'surface loss',
                           'array loss']
            message = "'metal_type' must be one of {}".format(metal_types)
            raise ValueError(message)
        # add the new metal to the metals list replacing if needed
        defined_metals = metals[2:]
        defined_names = []
        for defined_metal in defined_metals:
            defined_names.append(shlex.split(defined_metal)[1])
        if name in defined_names:
            metal_index = np.where(name == np.array(defined_names))[0][0]
            metals[metal_index] = metal
        else:
            metals.append(metal)
        # add the metal definitions to the geometry
        metals = os.linesep.join(metals)
        self['geometry']['metals'] = metals
        log.debug("{} {} metal defined".format(metal_type, name))

    def set_box_cover(self, cover_type, top=False, bottom=False, **kwargs):
        """
        Set the Sonnet box cover.

        :param cover_type: type of cover to set (string)
            Valid types are listed below with any additional keyword arguments that may be
            used with them.
           'waveguide load': a waveguide load, useful for modeling infinite arrays
           'free space': no box cover, an open environment
           'lossless': default lossless metal for Sonnet
           'custom' a metal previously defined by define_metal()
                :keyword name: name of the metal used when it was defined
        One of top or bottom keywords must be True
        :param top: set the cover on the top of the box (boolean)
        :param bottom: set the cover on the bottom of the box (boolean)
        """
        # check inputs
        message = "set 'top', 'bottom', or both to be True"
        assert top or bottom, message
        # set top or bottom identifiers
        location = "TMET" if top else "BMET"
        location_index = 0 if top else 1
        run_again = True if top and bottom else False
        # pull out all the metals
        metals = self['geometry']['metals'].splitlines()
        # format metal string
        if cover_type == 'waveguide load':
            metal = b.WG_LOAD_FORMAT.format(location=location)
        elif cover_type == 'free space':
            metal = b.FREESPACE_FORMAT.format(location=location)
        elif cover_type == 'lossless':
            metal = b.LOSSLESS_FORMAT.format(location=location)
        elif cover_type == 'custom':
            # check name
            message = "'name' keyword must be defined for a custom metal"
            name = kwargs.pop('name', None)
            assert name is not None, message
            defined_metals = metals[2:]
            defined_names = []
            for defined_metal in defined_metals:
                defined_names.append(shlex.split(defined_metal)[1])
            message = "'{}' is not a defined metal".format(name)
            assert name in defined_names, message
            # reformat metal string
            metal_index = np.where(name == np.array(defined_names))[0][0]
            metal = shlex.split(defined_metals[metal_index])
            # check type
            message = "'{}' must be one of these metal types to put on the cover {}"
            assert metal[3] in b.COVER_TYPES.values(), \
                message.format(name, b.COVER_TYPES.keys())
            metal[0] = location
            metal = " ".join(metal)
        else:
            metal_types = ['waveguide load', 'free space', 'lossless', 'custom']
            message = "'metal_type' must be one of {}".format(metal_types)
            raise ValueError(message)
        # add the metal definition to the geometry
        metals[location_index] = metal
        metals = os.linesep.join(metals)
        self['geometry']['metals'] = metals
        log.debug("{} box cover added on the {}"
                  .format(cover_type, 'top' if top else 'bottom'))
        # run again if setting both top and bottom
        if run_again:
            self.set_box_cover(cover_type, top=False, bottom=True, **kwargs)

    def add_dimension(self):
        """Adds a dimension to the simulation geometry."""
        raise NotImplementedError

    def add_dielectric(self, name, level, thickness=0, epsilon=(1,), mu=(1,),
                       dielectric_loss=(0,), magnetic_loss=(0,), conductivity=(0,),
                       z_partitions=0):
        """
        Adds a dielectric layer to the project. Parameters input as length two lists are
        interpreted as [xy property, z property].

        :param name: name of the dielectric layer (str)
        :param level: level of the dielectric layer (integer)
        :param thickness: thickness of the layer in the project length units (float)
        :param epsilon: relative dielectric constant (float or length 2 list of floats)
        :param mu: relative permeability (float or length 2 list of floats)
        :param dielectric_loss: dielectric loss tangent (float or length 2 list of floats)
        :param magnetic_loss: magnetic loss tangent (float or length 2 list of floats)
        :param conductivity: bulk conductivity (float or length 2 list of floats)
        :param z_partitions: number of z-partitions for dielectric bricks (integer)
        """
        # check the inputs
        message = "'{}' parameter must be an integer"
        assert isinstance(level, int), message.format('level')
        assert isinstance(z_partitions, int), message.format('z_partitions')
        anisotropic = {'epsilon': epsilon, 'mu': mu, 'dielectric_loss': dielectric_loss,
                       'magnetic_loss': magnetic_loss, 'conductivity': conductivity}
        any_z = False
        for key, value in anisotropic.items():
            message = "'{}' must be a float or a length two list of floats"
            if not isinstance(value, (tuple, list)):
                assert isinstance(value, (int, float)), message.format(name)
                anisotropic[key] = [value]
            else:
                condition = (isinstance(value, (tuple, list)) and
                             (len(value) == 2 or len(value) == 1))
                if condition:
                    for element in value:
                        condition = condition and isinstance(element, (int, float))
                assert condition, message.format(name)
            any_z = (any_z or len(anisotropic[key]) == 2)
        epsilon = anisotropic['epsilon']
        mu = anisotropic['mu']
        dielectric_loss = anisotropic['dielectric_loss']
        magnetic_loss = anisotropic['magnetic_loss']
        conductivity = anisotropic['conductivity']
        # get the current layers
        layers = self['geometry']['layers'].splitlines()
        # add some unnamed layers if the level we are adding larger than the current size
        if level >= len(layers):
            unnamed = b.LAYER_FORMAT.format(name="Unnamed", thickness=0, xy_epsilon=1,
                                            xy_mu=1, xy_e_loss=0, xy_m_loss=0, xy_sigma=0,
                                            z_partitions=0, z_epsilon="", z_mu="",
                                            z_e_loss="", z_m_loss="", z_sigma="")
            layers += [unnamed] * (level + 1 - len(layers))
        # add the new number of metal levels to the project
        self['geometry']['n_metal_levels'] = len(layers) - 1
        # define xy layer parameters
        parameters = {'name': name, 'thickness': thickness, 'z_partitions': z_partitions,
                      'xy_epsilon': epsilon[0], 'xy_mu': mu[0],
                      'xy_e_loss': dielectric_loss[0], 'xy_m_loss': magnetic_loss[0],
                      'xy_sigma': conductivity[0]}
        # define z layer parameters
        if any_z:
            z_parameters = {'z_epsilon': epsilon[1] if len(epsilon) == 2 else epsilon[0],
                            'z_mu': mu[1] if len(mu) == 2 else mu[0],
                            'z_e_loss': (dielectric_loss[1] if len(dielectric_loss) == 2
                                         else dielectric_loss[0]),
                            'z_m_loss': (magnetic_loss[1] if len(magnetic_loss) == 2
                                         else magnetic_loss[0]),
                            'z_sigma': (conductivity[1] if len(conductivity) == 2
                                        else conductivity[0])}
        else:
            z_parameters = {'z_epsilon': "", 'z_mu': "", 'z_e_loss': "", 'z_m_loss': "",
                            'z_sigma': ""}
        # format the new dielectric layer
        parameters.update(z_parameters)
        layers[level] = b.LAYER_FORMAT.format(**parameters)
        # add the new dielectric layer to the geometry
        layers = os.linesep.join(layers)
        self['geometry']['layers'] = layers
        log.debug("{} dielectric added at level {}".format(name, level))

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
        :param x_cells: number of cells in the x direction (integer)
        :param y_cells: number of cells in the y direction (integer)
        """
        self['geometry']['box_width_x'] = float(box_width_x)
        self['geometry']['box_width_y'] = float(box_width_y)
        log.debug("box size set to ({}, {})".format(box_width_x, box_width_y))
        self['geometry']['x_cells2'] = 2 * int(x_cells)
        self['geometry']['y_cells2'] = 2 * int(y_cells)
        log.debug("number of cells set to ({}, {})".format(int(x_cells), int(y_cells)))

    def define_dielectric_bricks(self):
        """Defines a dielectric brick that can be used in the project."""
        raise NotImplementedError

    def define_technology_layer(self, layer_type, name, level, material,
                                fill_type='staircase', edge_mesh=True, **kwargs):
        """
        Defines a technology layer for the project.

        :param layer_type: type of technology layer (string)
            Valid types are listed below with any additional keyword arguments that may be
            used with them.
            'metal': a metal technology layer
            'via': a via technology layer
                :keyword to_level: the level to which the polygon extends (integer)
                :keyword via_fill_type: meshing used for the via polygon (string)
                    Valid options are 'ring' (default), 'center', 'vertices', 'solid',
                    and 'bar'.
                :keyword pads: metal pads over the via, default is False (boolean)
            'dielectric brick': a dielectric brick technology layer
        :param name: unique name of the layer (string)
        :param level: level of the layer (integer)
        :param material: layer material name (string)
            The name corresponds to the name used in define_metal() or
            define_dielectric_brick() for metals and vias or dielectric bricks
            respectively. The name can also be 'lossless' for metals and vias or 'air' for
            dielectric bricks.
        :param fill_type: layer fill type (string)
            Valid types are listed below with any additional keyword arguments that may be
            used with them.
            'staircase': a staircase mesh (default)
                The default minimum is 1 and maximum is 100 for these keywords.
                :keyword x_min: minimum subsection size in the x direction (integer)
                :keyword x_max: maximum subsection size in the x direction (integer)
                :keyword y_min: minimum subsection size in the y direction (integer)
                :keyword y_max: maximum subsection size in the y direction (integer)
            'diagonal': a diagonal mesh
                The default minimum is 1 and maximum is 100 for these keywords.
                :keyword x_min: minimum subsection size in the x direction (integer)
                :keyword x_max: maximum subsection size in the x direction (integer)
                :keyword y_min: minimum subsection size in the y direction (integer)
                :keyword y_max: maximum subsection size in the y direction (integer)
            'conformal': a conformal mesh
                :keyword conformal_max: maximum length for a conformal mesh subsection
                    If it is 0 or not specified, the length is computed by Sonnet.
        :param edge_mesh: use edge meshing (boolean)
        """
        # check inputs
        message = "'layer type' parameter must be one of {}"
        assert layer_type in b.LAYER_TYPES.keys(), \
            message.format(list(b.LAYER_TYPES.keys()))
        message = "'fill_type' parameter must be one of {}"
        assert fill_type in b.FILL_TYPES.keys(), message.format(list(b.FILL_TYPES.keys()))
        # determine the material index
        if layer_type == 'metal' or layer_type == 'via':
            if material == "lossless":
                material_index = -1
            else:
                metals = self['geometry']['metals'].splitlines()
                defined_metals = metals[2:]
                defined_names = []
                for defined_metal in defined_metals:
                    defined_names.append(shlex.split(defined_metal)[1])
                material_index = np.where(material == np.array(defined_names))[0][0]
                # check that we have a valid material
                material_value = shlex.split(defined_metals[material_index])[3]
                message = ("for a '{}' the 'material' parameter must be one of these "
                           "types from define_metal() {}")
                if layer_type == 'metal':
                    assert material_value in b.METAL_TYPES.values(), \
                        message.format('metal', list(b.METAL_TYPES.keys()))
                else:
                    assert material_value in b.VIA_TYPES.values(), \
                        message.format('via', list(b.VIA_TYPES.keys()))
        else:
            raise NotImplementedError
        # set the level format
        level_format = {"level": level, "n_vertices": 0, "material": material_index,
                        "fill_type": b.FILL_TYPES[fill_type],
                        "x_min": kwargs.pop("x_min", 1), "y_min": kwargs.pop("y_min", 1),
                        "x_max": kwargs.pop("x_max", 100),
                        "y_max": kwargs.pop("y_max", 100),
                        "conformal_max": kwargs.pop("conformal_max", 0),
                        "edge_mesh": "Y" if edge_mesh else "N"}
        level_string = b.LEVEL_FORMAT.format(**level_format)
        # set the via format
        if layer_type == 'via':
            message = "'to_level' keyword must be used for a via technology layer"
            assert 'to_level' in kwargs.keys(), message
            pads = kwargs.pop('pads', False)
            to_format = {"to_level": kwargs['to_level'],
                         'via_fill_type': kwargs.pop('via_fill_type', 'ring').upper(),
                         'pads': "COVERS" if pads else "NOCOVERS"}
            to_level_string = b.TO_LEVEL_FORMAT.format(**to_format)
        else:
            to_level_string = ''
        # combine all the formats
        full_format = {"layer_type": b.LAYER_TYPES[layer_type], "name": name,
                       "poly_type": b.POLYGON_TYPES[layer_type],
                       "level": level_string, "to_level": to_level_string}
        technology_layer = b.TECHLAYER_FORMAT.format(**full_format)
        # add the technology layer to the project replacing if necessary
        current_layers = self['geometry']['technology_layers']
        current_layers = ['TECHLAY' + c for c in current_layers.split('TECHLAY') if c]
        current_names = []
        for layer in current_layers:
            current_names.append(shlex.split(layer)[2])
        if name in current_names:
            layer_index = np.where(name == np.array(current_names))[0][0]
            current_layers[layer_index] = technology_layer
        else:
            current_layers.append(technology_layer)
        new_layers = os.linesep.join(current_layers)
        self['geometry']['technology_layers'] = new_layers
        log.debug("{} {} technology layer added on level {} with {}"
                  .format(layer_type, name, level, material))

    def add_edge_via(self):
        """Adds an edge via to the project."""
        raise NotImplementedError

    def set_origin(self, dx, dy, locked=True):
        """
        Sets the origin for the project.

        :param dx: distance from the left edge (float)
        :param dy: distance from the top edge (float)
        :param locked: sets whether the origin location is locked (boolean)
        """
        locked_values = {True: 'L', False: 'U'}
        # dy is backwards for some reason
        origin = b.ORIGIN_FORMAT.format(dx=dx, dy=-dy, locked=locked_values[locked])
        self['geometry']['origin'] = origin
        log.debug("origin set to ({}, {}) and is{} locked"
                  .format(dx, dy, " not" if not locked else ""))

    def add_port(self, port_type, number, x, y, resistance=0,
                 reactance=0, inductance=0, capacitance=0, **kwargs):
        """
        Adds a port to the project.

        :param port_type: type of port to add (string)
            Valid options are listed below with the additional keyword arguments that may
            be needed for each.
            'standard': a standard Sonnet port. (string)
                These keywords are only needed if the port is an independent port.
                :keyword independent: the port is independent, default False (boolean)
                    Only works if the port is on the box wall
                :keyword diagonal: allow the reference plane to be diagonal (boolean)
                    This keyword only works if the port is a box wall port and
                    independent.
                :keyword fixed_reference_plane: is the reference plane fixed (boolean)
                :keyword length: calibration length (float)
            'auto-grounded': a grounding port used in the interior of a geometry (string)
                These keywords are required.
                :keyword fixed_reference_plane: is the reference plane fixed (boolean)
                :keyword length: calibration length (float)
            'co-calibrated': a port that is part of a calibration group (string)
                :keyword independent: the port is independent, default False (boolean)
                :keyword fixed_reference_plane: is the reference plane fixed (boolean)
                :keyword length: calibration length (float)
                :keyword group_id: co-calibration group id, automatic by default (string)
        :param number: port number (non-zero integer)
        :param x: x position of the port (float)
        :param y: y position of the port (float)
        :param resistance: resistance of the port in ohms (float)
        :param reactance: reactance of the port in ohms (float)
        :param inductance: inductance of the port in nH (float)
        :param capacitance: capacitance of the port in pF (float)
        """
        # check inputs
        message = "'port_type' parameter must be one of {}"
        assert port_type in b.PORT_TYPES.keys(), message.format(list(b.PORT_TYPES.keys()))
        message = "'number' parameter can not be 0 and must be an integer"
        assert isinstance(number, int) and number != 0, message
        if port_type == "standard":
            independent = kwargs.pop("independent", False)
            on_wall = (x == 0 or y == 0 or x == self["geometry"]["box_width_x"] or
                       y == self["geometry"]["box_width_y"])
            message = "a standard port must be on the box wall to be independent"
            assert (independent and on_wall) or not independent, message
        elif port_type == "auto-grounded":
            independent = kwargs.pop("independent", True)
            message = "auto-grounded ports are always independent"
            assert independent, message
        else:  # co-calibrated
            independent = kwargs.pop("independent", False)
        # count the number of ports already made
        ports = ['POR1' + c for c in self['geometry']['ports'].split('POR1') if c]
        n_ports = len(ports)
        # get all the file_ids from the ports
        file_ids = []
        for port in ports:
            file_ids.append(port.split("POLY")[1].split()[0])
        # find the right polygon and vertex
        polygons = [c + "END" for c in self['geometry']['polygons'].split("END\n")
                    if c.strip()]
        min_value = np.inf
        min_index = 0
        polygon_index = 0
        position = np.array([x, y])
        new_position = position
        for index, polygon in enumerate(polygons):
            generator = (r for r in polygon.splitlines() if r and not r[0] in ('T', 'E'))
            polygon = np.genfromtxt(generator, skip_header=1)
            distance = np.linalg.norm(polygon - position, axis=1)
            trial_index = np.argmin(np.abs(distance))
            trial_value = np.abs(distance[trial_index])
            if trial_value < min_value:
                min_value = trial_value
                min_index = trial_index
                polygon_index = index
                # [:-1, :] removes the repeated point at the end of the file
                lower = polygon[:-1, :][min_index - 1, :]
                # % (polygon.shape[0] - 1) skips the repeated point at the end
                upper = polygon[(min_index + 1) % (polygon.shape[0] - 1), :]
                if np.linalg.norm(lower - position) < np.linalg.norm(upper - position):
                    new_position = (lower + polygon[min_index, :]) / 2
                    min_index = (min_index - 1) % (polygon.shape[0] - 1)
                else:
                    new_position = (upper + polygon[min_index, :]) / 2
        # set the debug_id equal to the port id
        polygon = polygons[polygon_index].splitlines()
        condition = (not polygon[0] or polygon[0][:3] == 'MET' or
                     polygon[0][:3] == 'BRI' or polygon[0][:3] == 'VIA')
        index = 1 if condition else 0
        level = polygon[index]
        level = level.split()
        if level[4] not in file_ids:
            file_id = str(n_ports + 1001)
            level[4] = file_id
            level = " ".join(level)
            polygon[index] = level
            polygon = os.linesep.join(polygon)
            polygons[polygon_index] = polygon
            polygons = os.linesep.join(polygons)
            self['geometry']['polygons'] = polygons
        else:
            file_id = level[4]
        # set the port format string
        diagonal = kwargs.pop("diagonal", None)
        diagonal_string = b.DIAGONAL_FORMAT.format(allowed="Y" if diagonal else "N")
        if independent:
            fixed_reference_plane = kwargs.pop("fixed_reference_plane", False)
            reference_type = "NONE" if fixed_reference_plane else "FIX"
            length = kwargs.pop("length", None)
            length_string = 0 if length is None else length
        else:
            reference_type = ""
            length_string = ""
        port_format = {"port_type": b.PORT_TYPES[port_type],
                       "group_id": "" if port_type != 'co-calibrated'
                       else kwargs.pop("group_id", "Auto"),
                       "diagonal": diagonal_string if diagonal is not None else "",
                       "number": number, "resistance": resistance, "reactance": reactance,
                       "inductance": inductance, "capacitance": capacitance,
                       "ref_type": reference_type, "length": length_string,
                       "file_id": file_id, "polygon_index": min_index,
                       "x": new_position[0], "y": new_position[1]}
        self['geometry']['ports'] += b.PORT_FORMAT.format(**port_format)
        log.debug("{} port {} added at ({}, {}) with parameters ({}, {}, {}, {})"
                  .format(port_type, number, new_position[0], new_position[1], resistance,
                          reactance, inductance, capacitance))

    def add_calibration_group(self):
        """Adds a calibration group to the project."""
        raise NotImplementedError

    def add_component(self):
        """Adds a component to the project."""
        raise NotImplementedError

    def add_gdstk_cell(self, polygon_type, cell, layer=None, datatype=None,
                       **kwargs):
        """
        Adds a GDSTK Cell to the project.

        :param polygon_type: type of polygon to add (string)
            Valid options are listed below with the additional keyword arguments that may
            be needed for each.
            'metal': a metal polygon
            'via': a via polygon
                :keyword to_level: the level to which the polygon extends (integer)
                :keyword via_fill_type: meshing used for the via polygon (string)
                    Valid options are 'ring' (default), 'center', 'vertices', 'solid',
                    and 'bar'.
                :keyword pads: metal pads over the via, default is False (boolean)
            'dielectric brick': a dielectric brick polygon
        :param cell: a gdstk cell (object)
        :param layer: the layer number to use (integer)
            The default is None and all layers are used.
        :param datatype: the datatype to use (integer)
            The default is None and all datatypes are used.

        Keywords to add_polygons are also included.

        Note: Flatten the cell if references are used.
        """
        points = []
        for polygon in cell.polygons:
            p_layer = polygon.layer if layer is not None else None
            p_datatype = polygon.datatype if datatype is not None else None
            if p_layer == layer and p_datatype == datatype:
                points.append(polygon.points)

        for path in cell.paths:
            polygons = path.to_polygons()
            for i in range(path.num_paths):
                p_layer = path.layers[i] if layer is not None else None
                p_datatype = path.datatype[i] if datatype is not None else None
                if p_layer == layer and p_datatype == datatype:
                    points.append(polygons[i].points)

        self.add_polygons(polygon_type, points, **kwargs)

    def add_polygons(self, polygon_type, polygons, tech_layer=None, **kwargs):
        """
        Adds polygons to the project.

        :param polygon_type: type of polygon to add (string)
            Valid options are listed below with the additional keyword arguments that may
            be needed for each.
            'metal': a metal polygon
            'via': a via polygon
                :keyword to_level: the level to which the polygon extends (integer)
                :keyword via_fill_type: meshing used for the via polygon (string)
                    Valid options are 'ring' (default), 'center', 'vertices', 'solid',
                    and 'bar'.
                :keyword pads: metal pads over the via, default is False (boolean)
            'dielectric brick': a dielectric brick polygon
        :param polygons: a list of N x 2 numpy arrays that define the polygons
        :param tech_layer: the technology layer name (string)
            The name must correspond to a name used in define_technology_layer(). The
            following keywords can be used with the tech_layer keyword.
            :keyword inherit: inherit the techlayer properties (boolean)
            If tech_layer is not specified or inherit=False, the keywords below can be
            used to determine the polygon properties
            :keyword level: level of the layer (integer)
            :keyword material: layer material name (string)
            The name corresponds to the name used in define_metal() or
            define_dielectric_brick() for metals and vias or dielectric bricks
            respectively. The name can also be 'lossless' for metals and vias or 'air' for
            dielectric bricks.
            :keyword fill_type: layer fill type (string)
                Valid types are listed below with any additional keyword arguments that
                may be used with them.
                'staircase': a staircase mesh (default)
                    The default minimum is 1 and maximum is 100 for these keywords.
                    :keyword x_min: minimum subsection size in the x direction (integer)
                    :keyword x_max: maximum subsection size in the x direction (integer)
                    :keyword y_min: minimum subsection size in the y direction (integer)
                    :keyword y_max: maximum subsection size in the y direction (integer)
                'diagonal': a diagonal mesh
                    The default minimum is 1 and maximum is 100 for these keywords.
                    :keyword x_min: minimum subsection size in the x direction (integer)
                    :keyword x_max: maximum subsection size in the x direction (integer)
                    :keyword y_min: minimum subsection size in the y direction (integer)
                    :keyword y_max: maximum subsection size in the y direction (integer)
                'conformal': a conformal mesh
                    :keyword conformal_max: maximum length for a conformal mesh subsection
                        If it is 0 or not specified, the length is computed by Sonnet.
            :keyword edge_mesh: use edge meshing (boolean)
        """
        # check inputs
        message = "'polygon type' parameter must be one of {}"
        assert polygon_type in b.POLYGON_TYPES.keys(), \
            message.format(list(b.POLYGON_TYPES.keys()))
        if tech_layer is None:
            message = "'{}' keyword must be used if 'tech_layer' is not specified"
            assert 'level' in kwargs.keys(), message.format('level')
            assert 'material' in kwargs.keys(), message.format('material')
        # set up the level format for the new polygons
        level_format = {"level": kwargs.pop("level", 1),
                        "fill_type": b.FILL_TYPES[kwargs.pop("fill_type", "staircase")],
                        "x_min": kwargs.pop("x_min", 1),
                        "y_min": kwargs.pop("y_min", 1),
                        "x_max": kwargs.pop("x_max", 100),
                        "y_max": kwargs.pop("y_max", 100),
                        "conformal_max": kwargs.pop("conformal_max", 0),
                        "edge_mesh": "Y" if kwargs.pop("edge_mesh", True) else "N"}
        name = kwargs.pop("material", "lossless")
        condition = (name == 'lossless' and (polygon_type == 'metal' or
                                             polygon_type == 'via') or
                     name == 'air' and polygon_type == 'dielectric brick')
        if condition:
            metal_index = -1
        else:
            defined_metals = self['geometry']['metals'].splitlines()[2:]
            defined_names = []
            for defined_metal in defined_metals:
                defined_names.append(shlex.split(defined_metal)[1])
            metal_index = np.where(name == np.array(defined_names))[0][0]
            # check that we have a valid material
            material_value = shlex.split(defined_metals[metal_index])[3]
            message = ("for a '{}' the 'material' parameter must be one of these "
                       "types from define_metal() {}")
            if polygon_type == 'metal':
                assert material_value in b.METAL_TYPES.values(), \
                    message.format('metal', list(b.METAL_TYPES.keys()))
            else:
                assert material_value in b.VIA_TYPES.values(), \
                    message.format('via', list(b.VIA_TYPES.keys()))
        level_format['material'] = metal_index
        # set up the to_level format for the new polygons
        if polygon_type == 'via':
            message = "'{}' keyword argument is required for via polygons"
            assert "to_level" in kwargs.keys(), message.format('to_level')
            via_fill_type = kwargs.pop("via_fill_type", "ring").upper()
            pads = kwargs.pop("pads", False)
            to_level_string = b.TO_LEVEL_FORMAT.format(
                to_level=kwargs["to_level"], via_fill_type=via_fill_type,
                pads="COVERS" if pads else "NOCOVERS")
        else:
            to_level_string = ""
        # get the technology layer format for the new polygons
        if tech_layer is not None:
            inherit = kwargs.pop("inherit", True)
            tech_layer_string = b.TECHLAYER_NAME_FORMAT.format(name=tech_layer,
                                                               inherit="INH"
                                                               if inherit else "NOH")
        else:
            tech_layer_string = ''
        # add each polygon to the project
        for index, polygon in enumerate(polygons):
            # add the last vertex to the end of each polygon if it isn't there
            if np.any(polygon[0, :] != polygon[-1, :]):
                polygon = np.vstack([polygon, polygon[0, :]])
            # update the level format
            level_format['n_vertices'] = polygon.shape[0]
            # add the polygon to the project
            level_string = b.LEVEL_FORMAT.format(**level_format)
            polygon_string = ''
            for vertex in polygon:
                polygon_string += "{:.8f} {:.8f}".format(*vertex) + os.linesep
            polygons_string = b.POLYGON_FORMAT.format(
                polygon_type=b.POLYGON_TYPES[polygon_type], level=level_string,
                to_level=to_level_string, tech_layer=tech_layer_string,
                polygon=polygon_string)
            self['geometry']['polygons'] += polygons_string
            self['geometry']['n_polygons'] += 1
            log.debug("polygon added")

    def add_output_file(self, file_type, output_folder=None, deembed=True,
                        include_abs=True, include_comments=True, high_precision=True,
                        file_name=None, parameter_type='S', parameter_form='RI'):
        """
        Add an output file for the response data from the analysis of the project.

        :param file_type: output file type (string)
            Valid options are 'touchstone', 'touchstone2', 'databank', 'scompact',
            'spreadsheet'/'csv', 'cadance', 'mdif_s2p'/'mdif', and 'mdif_ebridge'.
        :param output_folder: relative path to where the data is saved (string)
            If no folder is chosen, data will be saved in the top level of the project
            directory. This option can only be set once per Project, and it's value is
            overwritten if selected again.
        :param deembed: save the deembeded data, defaults to True (boolean)
        :param include_abs: include the abs calculated data, defaults to True (boolean)
        :param include_comments: include comments in the file, defaults to True (boolean)
        :param high_precision: use high precision numbers, defaults to True (boolean)
        :param file_name: output data file name, defaults to the sonnet file name (string)
        :param parameter_type: type of parameter to output (string)
            Valid options are 'S' for the scattering parameters, 'Y' for the Y-parameters,
            and 'Z' for the Z-parameters.
        :param parameter_form: form of the output parameters (string)
            Valid options are 'MA' for magnitude-angle, 'DB' for dB-angle, and 'RI' for
            real-imaginary.
        """
        # check inputs
        file_types = {'touchstone': 'TS', 'ts': 'TS',
                      'touchstone2': 'TOUCH2', 'touch2': 'TOUCH2',
                      'databank': 'DATA_BANK', 'data_bank': 'DATA_BANK',
                      'scompact': 'SC', 'sc': 'SC',
                      'spreadsheet': 'CSV', 'csv': 'CSV',
                      'cadance': 'CADANCE',
                      'mdif_s2p': 'MDIF', 'mdif': 'MDIF',
                      'mdif_ebridge': 'EBMDIF', 'ebmdif': 'EBMDIF'}
        message = "'file_type' parameter must be in {}".format(list(file_types.keys()))
        assert file_type in file_types.keys(), message
        file_type = file_types[file_type.lower()]
        message = "'parameter_type' parameter must be in {}".format(['S', 'Y', 'Z'])
        assert parameter_type in ['S', 'Y', 'Z'], message
        message = "'parameter_form' parameter must be in {}".format(['RI', 'MA', 'DB'])
        assert parameter_form in ['RI', 'MA', 'DB'], message
        # parse options
        deembed = 'D' if deembed else 'ND'
        include_abs = 'Y' if include_abs else 'N'
        include_comments = 'IC' if include_comments else 'NC'
        precision = 15 if high_precision else 8
        # create ports string
        port_dict = {}
        for port in self['geometry']['ports'].split("POR1"):
            if port:  # could be empty string
                data = port.split('\n')[4].split(" ")
                port_num = int(data[0])
                port_params = data[1:5]
                port_dict[port_num] = port_params
        if not port_dict:
            raise AttributeError("No ports have been defined.")

        port_string = "FTERM"
        for i in range(1, max(port_dict.keys()) + 1):
            try:
                port_string += (" " + " ".join(port_dict[i]))
            except KeyError:
                port_string += " 0 0 0 0"

        if file_name is None:
            file_name = '$BASENAME'
            if file_type == "TS":
                file_name += ".s{}p".format(len(port_dict.keys()))
            elif file_type == "TOUCH2":
                file_name += ".ts"

        # set the output folder if it was specified
        if output_folder is not None:
            self['output_file']['output_folder'] = output_folder
        # create output string
        output = b.RESPONSE_DATA_FORMAT.format(file_type=file_type,
                                               deembed=deembed,
                                               include_abs=include_abs,
                                               file_name=file_name,
                                               include_comments=include_comments,
                                               precision=precision,
                                               parameter_type=parameter_type,
                                               parameter_form=parameter_form,
                                               ports=port_string)
        # add the output file to the project
        self['output_file']['response_data'] += output + os.linesep
        log.debug("{} output file added here '{}'".format(file_type, output_folder))


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
        folder = os.path.join(os.path.dirname(self.project_file_path), 'sondata')
        if not os.path.isdir(folder):
            os.mkdir(folder)
        subfolder = os.path.join(folder, os.path.basename(file_path).split('.')[0])
        if not os.path.isdir(subfolder):
            os.mkdir(subfolder)
        log.debug("netlist project saved")

    def create_circuit(self):
        raise NotImplementedError

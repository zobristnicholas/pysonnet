import csv
import copy
import pathlib
import numpy as np
from matplotlib import colors
from matplotlib import pyplot as plt
from scipy.interpolate import interp2d
from scipy.constants import epsilon_0, mu_0


class NCoupledLines:
    """
    Class for loading in outputs saved with project.add_n_coupled_lines_file().
    Different formats can be loaded with the "from_" methods.
    """
    def __init__(self, frequencies, inductance, resistance, capacitance, conductance):
        self.frequencies = np.array(frequencies)[:, np.newaxis, np.newaxis]
        self.inductance = np.array(inductance, ndmin=3)
        self.resistance = np.array(resistance, ndmin=3)
        self.capacitance = np.array(capacitance, ndmin=3)
        self.conductance = np.array(conductance, ndmin=3)
        self.impedance = self.resistance + 1j * 2 * np.pi * self.frequencies * self.inductance
        self.admittance = self.conductance + 1j * 2 * np.pi * self.frequencies * self.capacitance

        # Find the propagation eigenvalues and basis
        propagation_constant_sq, transform = self._eig_sorted(self.admittance @ self.impedance)

        self.propagation_basis = transform
        transform_inv = np.linalg.inv(transform)

        self.propagation_constant = np.sqrt(propagation_constant_sq)

        # Determine characteristic impedance matrix and eigenvalues
        shape = self.propagation_constant.shape
        propagation_constant_inv = np.zeros(shape + shape[-1:], dtype=self.propagation_constant.dtype)
        diagonals = propagation_constant_inv.diagonal(axis1=-2, axis2=-1)
        diagonals.setflags(write=True)
        diagonals[:] = 1 / self.propagation_constant  # updates propagation_constant_inv
        self.characteristic_impedance_matrix = self.impedance @ transform @ propagation_constant_inv @ transform_inv

        self.characteristic_impedance, self.impedance_basis = self._eig_sorted(self.characteristic_impedance_matrix)

        self.effective_relative_permittivity = (
            self.propagation_constant / (2j * np.pi * self.frequencies[:, :, 0] * np.sqrt(epsilon_0 * mu_0))
        )**2

    @classmethod
    def from_spectre(cls, file_name):
        frequencies = []
        inductances = []
        resistances = []
        capacitances = []
        conductances = []
        dim = None
        with open(file_name) as fid:
            while True:
                line = fid.readline()

                # Exit the while loop if we run out of lines.
                if not line:
                    break
                    # raise IOError(f"Improper file format for '{file_name}")

                # Remove the comments, leading or trailing whitespace, and make
                # everything lowercase.
                line = line.split(';', 1)[0].strip().lower()

                # Skip the line if it was only comments.
                if len(line) == 0:
                    continue

                if line.startswith('format'):
                    number = line.count(":") - 1  # extra colon for after format
                    dim = int((np.sqrt(8 * number + 1) - 1) / 2)  # (dim + 1) * dim / 2 elements in upper triangle
                    for _ in range(3):  # discard next three lines
                        fid.readline()
                    continue
                # If we are here we should be reading the data and have parsed the header info
                if dim is None:
                    raise IOError(f"File '{file_name} doesn't have the required format line")
                f, inductance_line = line.split(":")
                frequencies.append(float(f))
                inductances.append(cls._spectre_str_to_matrix(inductance_line, dim))
                resistances.append(cls._spectre_str_to_matrix(fid.readline(), dim))
                capacitances.append(cls._spectre_str_to_matrix(fid.readline(), dim))
                conductances.append(cls._spectre_str_to_matrix(fid.readline(), dim))
        return cls(frequencies, inductances, resistances, capacitances, conductances)

    @classmethod
    def from_hspice(cls, file_name):
        raise NotImplementedError

    @classmethod
    def _spectre_str_to_matrix(cls, string, dimension):
        array = np.array(string.split(), dtype=float)
        matrix = np.empty((dimension, dimension), dtype=float)
        upper = np.triu_indices(dimension, k=0)
        matrix[upper] = array
        lower = np.tril_indices(dimension, k=-1)
        matrix[lower] = matrix.T[lower]
        return matrix

    @classmethod
    def _eig_sorted(cls, matrix):
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        sorted_indices = np.argsort(eigenvalues, axis=-1)  # sort by eigenvalue real part
        eigenvalues = np.take_along_axis(eigenvalues, sorted_indices, axis=-1)
        eigenvectors = np.take_along_axis(eigenvectors, sorted_indices[:, np.newaxis, :], axis=-1)
        return eigenvalues, eigenvectors


class SYZParameter:
    """
    Class for loading in outputs saved with project.add_syz_parameter_file().
    Different formats can be loaded with the "from_" methods.
    """
    def __init__(self, f, value, value_type="s"):
        self.f = f
        self.value = value
        self.value_type = value_type

    @classmethod
    def from_touchstone(cls, file_name):
        # Get the number of ports from the extension (version 1)
        version = 1.
        extension = pathlib.Path(file_name).suffix
        if (extension[1] == 's') and (extension[-1] == 'p'):  # sNp
            try:
                n_ports = int(extension[2:-1])
            except ValueError:
                message = ("The file name does not have a s-parameter extension. "
                           f"It is [{extension}] instead. Please, correct the "
                           "extension to the form: 'sNp', where N is the number of ports.")
                raise IOError(message)
        elif extension == '.ts':
            n_ports = None
        else:
            message = ('The filename does not have the expected Touchstone '
                       'extension (.sNp or .ts)')
            raise IOError(message)

        values = []
        flip_port_order = False
        matrix_format = 'full'
        with open(file_name) as fid:
            while True:
                line = fid.readline()

                # Exit the while loop if we run out of lines.
                if not line:
                    break

                # Remove the comments, leading or trailing whitespace, and make
                # everything lowercase.
                line = line.split('!', 1)[0].strip().lower()

                # Skip the line if it was only comments.
                if len(line) == 0:
                    continue

                if line.startswith('[version]'):
                    version = float(line.partition('[version]')[2])
                    continue

                if line.startswith('[number of ports]'):
                    n_ports = int(line.partition('[number of ports]')[2])
                    continue

                if line.startswith('[two-port data order]'):
                    order = line.partition('[two-port data order]')[2].strip()
                    if order == '21_12':
                        flip_port_order = True
                    continue

                # Skip the number of frequencies line.
                if line.startswith('[number of frequencies]'):
                    continue

                if line.startswith('[matrix format]'):
                    matrix_format = line.partition('[matrix format]')[2].strip()
                    continue

                if line.startswith('[mixed-mode order]'):
                    message = "The mixed-mode order data format is not supported."
                    raise IOError(message)

                # Skip the network data line.
                if line.startswith('[network data]'):
                    continue

                # Skip the end line.
                if line.startswith('[end]'):
                    continue

                # Note the options.
                if line[0] == '#':
                    options = line[1:].strip().split()
                    # fill the option line with the missing defaults
                    options.extend(['ghz', 's', 'ma', 'r', '50'][len(options):])
                    unit = options[0]
                    parameter_type = options[1]
                    data_format = options[2]
                    continue

                # Collect all the values.
                values.extend([float(v) for v in line.split()])

        # Version 1 files have weird port order for 2 port matrices
        if version < 2 and n_ports == 2:
            flip_port_order = True

        # Reshape into rows of f, s11, s12, s13, s21, s22, s23, ...
        if matrix_format == 'full':
            values = np.asarray(values).reshape((-1, 2 * n_ports ** 2 + 1))
        else:  # lower or upper
            values = np.asarray(values).reshape((-1, n_ports ** 2 + n_ports + 1))

        # Remove noise values
        noise = np.where(np.diff(values[:, 0]) < 0)[0]  # f should increase
        if len(noise) != 0:
            values = values[noise[0] + 1:, :]

        # Extract the frequency in GHz.
        multiplier = {'hz': 1.0, 'khz': 1e3, 'mhz': 1e6, 'ghz': 1e9}[unit]
        f = values[:, 0] * multiplier / 1e9  # always in GHz

        # Convert to a complex number.
        if data_format == "ri":
            z = values[:, 1::2] + 1j * values[:, 2::2]
        else:
            mag = values[:, 1::2]
            angle = np.pi / 180 * values[:, 2::2]
            if data_format == "ma":
                z = mag * np.exp(1j * angle)
            else:  # == "db"
                z = 10 ** (mag / 20.0) * np.exp(1j * angle)

        # Get the parameter matrix (f.size x n_ports x n_ports)
        if matrix_format == 'full':
            parameter = z.reshape(-1, n_ports, n_ports)
        else:
            parameter = np.empty((f.size, n_ports, n_ports))
            upper_indices = np.triu_indices(n_ports)
            lower_indices = np.tril_indices(n_ports)
            if matrix_format == 'upper':
                parameter[:, upper_indices[0], upper_indices[1]] = z
                parameter_t = parameter.transpose((0, 2, 1))
                parameter[:, lower_indices[0], lower_indices[1]] = parameter_t[:, lower_indices[0], lower_indices[1]]
            else:  # lower
                parameter[:, lower_indices[0], lower_indices[1]] = z
                parameter_t = parameter.transpose((0, 2, 1))
                parameter[:, upper_indices[0], upper_indices[1]] = parameter_t[:, upper_indices[0], upper_indices[1]]

        if flip_port_order:
            parameter = parameter.transpose((0, 2, 1))

        return cls(f, parameter, parameter_type)

    @classmethod
    def from_databank(cls, file_name):
        raise NotImplementedError

    @classmethod
    def from_cadence(cls, file_name):
        raise NotImplementedError

    @classmethod
    def from_spreadsheet(cls, file_name):
        raise NotImplementedError

    @classmethod
    def from_mdif_s2p(cls, file_name):
        raise NotImplementedError

    @classmethod
    def from_mdif_ebridge(cls, file_name):
        raise NotImplementedError


class CurrentDensity:
    """Class for handling the current density output from Sonnet."""
    def __init__(self, file_name=None, load_on_init=False):
        """
        :param file_name: .csv file name for the Sonnet current density output
        :param load_on_init: load data on object creation (True) or defer (False)
        """
        # check the inputs
        assert file_name is not None, "must specify a file_name"
        assert type(load_on_init) is bool, "load_on_init must be a boolean"

        # save inputs and hidden parameters
        self.file_name = file_name
        self.load_on_init = load_on_init
        self._header_lines = 9

        # load or defer loading
        if load_on_init:
            self._load_data()
            self._load_header()
        else:
            self._data_loaded = False
            self._header_loaded = False
            self._header = None
            self._data = None

    @property
    def version(self):
        """Sonnet current density csv file format version."""
        self._check_header_loaded()
        return self._header[0][0]

    @property
    def sonnet_file_path(self):
        """Path to the Sonnet file used to generate the current density."""
        self._check_header_loaded()
        return self._header[0][2]

    @property
    def sonnet_version(self):
        """Sonnet version used to generate the current density."""
        self._check_header_loaded()
        return self._header[1][1]

    @property
    def sonnet_file_name(self):
        """Sonnet file name used to generate the current density."""
        self._check_header_loaded()
        return self._header[1][3]

    @property
    def frequency(self):
        """Frequency [Hz] at which the current density data was evaluated."""
        self._check_header_loaded()
        return float(self._header[2][1])

    @property
    def ports(self):
        """Returns a list of Sonnet ports in the file"""
        self._check_header_loaded()
        ports = []
        for index, cell in enumerate(self._header[3]):
            if len(cell) > 4 and cell[:4] == 'Port':
                ports.append(int(cell[5:]))
        return ports

    def drive_voltage(self, port):
        """Voltage of the input sine wave in volts sent into the specified port during the
        simulation.
        :param port: port number requested (integer)
        :return: the voltage output (float)
        :raises ValueError if the specified port isn't in the file
        """
        assert type(port) is int, "port must be an integer not {}".format(type(port))
        self._check_header_loaded()
        ports = []
        for index, cell in enumerate(self._header[3]):
            if len(cell) > 4 and cell[:4] == 'Port':
                ports.append(int(cell[5:]))
            if len(ports) > 0 and port == ports[-1]:
                return float(self._header[3][index + 2])
        raise ValueError("{} is not a valid port number. Use one of: {}"
                         .format(port, ports))

    def drive_phase(self, port):
        """Phase of the input sine wave in degrees sent into the specified port during the
        simulation.
        :param port: port number requested (integer)
        :return: the voltage output unit (string)
        :raises ValueError if the specified port isn't in the file
        """
        assert type(port) is int, "port must be an integer not {}".format(type(port))
        self._check_header_loaded()
        ports = []
        for index, cell in enumerate(self._header[3]):
            if len(cell) > 4 and cell[:4] == 'Port':
                ports.append(int(cell[5:]))
            if len(ports) > 0 and port == ports[-1]:
                return float(self._header[3][index + 4])
        raise ValueError("{} is not a valid port number. Use one of: {}"
                         .format(port, ports))

    @property
    def level_string(self):
        """Returns the level string e.g. '1', '2a', '2b', '3', etc. Letter subscripts on
        correspond to thick metal model layers"""
        self._check_header_loaded()
        return self._header[4][1]

    @property
    def level(self):
        """Returns the level integer which is unique and may not correspond to the level
        selected in Sonnet if thick metal models are used."""
        self._check_header_loaded()
        return int(self._header[4][2])

    @property
    def position_unit_string(self):
        """Unit string for the x-y position of the data."""
        self._check_header_loaded()
        if self._header[5][1] == "UM":
            return "µm"
        else:
            return self._header[5][1]

    @property
    def position_unit(self):
        """Unit value in meters for the x-y position of the data.
         If the data is in microns, the output will be 1e-6."""
        self._check_header_loaded()
        return float(self._header[5][2])

    @property
    def dx(self):
        """x grid step of the data in units of self.position_unit()."""
        self._check_header_loaded()
        return float(self._header[6][1])

    @property
    def dy(self):
        """y grid step of the data in units of self.position_unit()."""
        self._check_header_loaded()
        return float(self._header[6][4])

    @property
    def area(self):
        """Metal area in units of self.area_unit_string()."""
        self._check_header_loaded()
        return float(self._header[6][9])

    @property
    def area_unit_string(self):
        """Unit string of the self.area()."""
        self._check_header_loaded()
        return self._header[6][10]

    @property
    def current_unit_string(self):
        """Unit string for the current density values."""
        self._check_header_loaded()
        if self._header[7][2] == "Amps/Meter":
            return "A/m"
        else:
            return self._header[7][2]

    @property
    def x_position(self):
        """Vector of x positions corresponding to the data rows."""
        self._check_data_loaded()
        return self._data[0, 1:]

    @property
    def y_position(self):
        """Vector of y positions corresponding to the data columns."""
        self._check_data_loaded()
        return self._data[1:, 0]

    def current_density(self, power=None, impedance=50):
        """RMS current density matrix in units of self.current_unit_string().
        :param power: Power in dBm input into the input port. Uses the impedance parameter
                      to find the voltage. May not make sense if more than one port has a
                      nonzero input. Defaults to None and the input voltage in the file
                      is used.
        :param impedance: Impedance in ohms of the input port. It defaults to 50 ohms and
                          is not used if power is None."""
        self._check_data_loaded()
        if power is None:
            return self._data[1:, 1:]

        # calculate the rms power used for the simulation
        voltages = []
        for port in self.ports:
            voltages.append(self.drive_voltage(port))
        voltage = np.max(voltages)
        power_data = voltage**2 / impedance / 2

        # convert dBm to Watts
        power = 1e-3 * 10**(power / 10)

        return self._data[1:, 1:] * np.sqrt(power / power_data)

    def current_density_function(self, power=None, impedance=50, **kwargs):
        """Returns a scipy interp2d function over the current density
        :param power: Power in dBm input into the input port. Uses the impedance parameter
                      to find the voltage. May not make sense if more than one port has a
                      nonzero input. Defaults to None and the input voltage in the file
                      is used.
        :param impedance: Impedance in ohms of the input port. It defaults to 50 ohms and
                          is not used if power is None.
        :keyword **kwargs: keyword arguments to pass to interp2d"""
        z = self.current_density(power=power, impedance=impedance)
        return interp2d(self.x_position, self.y_position, z, **kwargs)

    def trim_data(self, x_min=None, x_max=None, y_min=None, y_max=None):
        """Removes data outside of the bounds specified by x_min, x_max, y_min, and y_max.
        The bounds are inclusive.
        :param x_min: float for the minimum x value
        :param x_max: float for the maximum x value
        :param y_min: float for the minimum y value
        :param y_max: float for the maximum y value
        """
        if x_min is None and x_max is None and y_min is None and y_max is None:
            raise ValueError("one of x_min, x_max, y_min, or y_max must be specified")
        self._check_data_loaded()

        if x_min is None:
            x_min = -np.inf
        if x_max is None:
            x_max = np.inf
        if y_min is None:
            y_min = -np.inf
        if y_max is None:
            y_max = np.inf

        x = self.x_position
        y = self.y_position
        current_density = self.current_density()
        logic_x = np.logical_and(x >= x_min, x <= x_max)
        logic_y = np.logical_and(y >= y_min, y <= y_max)

        x = x[logic_x]
        y = y[logic_y]
        y = np.append(np.nan, y).reshape(y.size + 1, 1)
        current_density = current_density[logic_y, :][:, logic_x]

        data = np.vstack([x, current_density])
        data = np.hstack([y, data])
        self._data = data

    def plot_current(self, axis=None, power=None, impedance=50, scale=1, block=False):
        """Plots a density map of the current.
        :param axis: An axis object on which to plot. If none is given, a new figure will
                     be created.
        :param power: Power in dBm input into the input port. Uses the impedance parameter
                      to find the voltage. May not make sense if more than one port has a
                      nonzero input. Defaults to None and the input voltage in the file
                      is used.
        :param impedance: Impedance in ohms of the input port. It defaults to 50 ohms and
                          is not used if power is None.
        :param scale: Integer corresponding to the matplotlib.colors.PowerNorm scale.
                      For example, 2 scales the color proportional to the local response
                      of an MKID since the response goes as I^2. It defaults to 1.
        :param block: block kwarg passed to pyplot.show()
        """
        if axis is None:
            _, axis = plt.subplots()
        sx = np.sign(self.x_position[-1] - self.x_position[-2])
        sy = np.sign(self.y_position[-1] - self.y_position[-2])
        x_position = np.concatenate([self.x_position - self.dx / 2 * sx,
                                     np.array([self.x_position[-1] + self.dx / 2 * sx])])
        y_position = np.concatenate([self.y_position - self.dy / 2 * sy,
                                     np.array([self.y_position[-1] + self.dy / 2 * sy])])
        x, y = np.meshgrid(x_position, y_position)
        mappable = axis.pcolormesh(x, y, self.current_density(power=power,
                                                              impedance=impedance),
                                   norm=colors.PowerNorm(scale))
        axis.set_aspect('equal')
        axis.set_xlabel("position [{}]".format(self.position_unit_string))
        axis.set_ylabel("position [{}]".format(self.position_unit_string))
        min_current = self.current_density(power=power, impedance=impedance).min()
        max_current = self.current_density(power=power, impedance=impedance).max()
        ticks = np.linspace(min_current**scale, max_current**scale, 10)**(1 / scale)
        r = -int(np.floor(np.log10(ticks[1]))) + 1
        ticks = np.round(ticks, r)
        if ticks[-1] > max_current:
            ticks[-1] = np.round(max_current - 10**-r, r)
        color_bar = plt.colorbar(mappable, ax=axis, ticks=ticks)
        color_bar.set_label("current [{}]".format(self.current_unit_string),
                            va='bottom', rotation=270)
        plt.tight_layout()
        plt.show(block=block)

    def copy(self):
        """Returns a copy of the object"""
        return copy.copy(self)

    def deepcopy(self):
        """Returns a deep copy of the object"""
        return copy.deepcopy(self)

    def _check_header_loaded(self):
        if not self._header_loaded:
            self._load_header()

    def _load_header(self):
        header = []
        with open(self.file_name, 'r') as csv_file:
            reader = csv.reader(csv_file)
            for _ in range(self._header_lines):
                row = next(reader)
                header.append(row)
        self._header = header
        self._header_loaded = True

    def _check_data_loaded(self):
        if not self._data_loaded:
            self._load_data()

    def _load_data(self):
        self._data = np.genfromtxt(self.file_name, delimiter=',',
                                   skip_header=self._header_lines,
                                   missing_values=["", "X Position ->"])
        self._data = self._data[:, :-1]
        self._data_loaded = True

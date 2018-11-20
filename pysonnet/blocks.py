GEOMETRY_PROJECT = """\
FTYP SONPROJ 15 ! Sonnet Project File
VER {version}
"""

NETLIST_PROJECT = """\
FTYP SONNETPROJ 15 ! Sonnet Netlist Project File
VER {version}"""

HEADER = """\
HEADER
LIC {licence_id}
DAT {date}
BUILT_BY_CREATED unknown "unknown version" {date}
BUILT_BY_SAVED unknown "unknown version"
ANN Created by pysonnet
END HEADER
"""

DIMENSIONS = """\
DIM
CDVY {conductivity_unit}
FREQ {frequency_unit}
RSVY {resistivity_unit}
SRES {sheet_resistance_unit}
IND {inductance_unit}
LEN {length_unit}
ANG {angle_unit}
CON {conductance_unit}
RES {resistance_unit}
END DIM
"""

GEOMETRY = """\
GEO
{symmetry}
{auto_height_vias}
SNPANG {angle}
{parallel_subsections}
{reference_planes}
{metals}
{dimensions}
{dielectrics}
{variables}
{parameters}
BOX {n_metal_lev} {box_width_x} {box_width_y} {x_cells2} {y_cells2} 20 0
{layers}
{variable_cells}
{technology_layers}
{edge_vias}
LORGN {origin}
{ports}
{calibration_group}
{component}
NUM {n_polygons}
{polygons}
END GEO
"""

FREQUENCY = """\
FREQ
{sweeps}
END FREQ
"""

CONTROL = """\
CONTROL
{sweep_type}
{optimize}
OPTIONS  {options}
SUBSPLAM Y {subsections_per_wavelength}
{edge_checking}
{subsectioning_frequency}
{estimated_epsilon}
SPEED {speed}
{abs_resolution}
CACHE_ABS {caching_level}
TARG_ABS {abs_target_number}
Q_ACC {q_accuracy_on}
DET_ABS_RES {resonance_detection_on}
{hierarchy_sweep}
END CONTROL
"""

OPTIMIZATION = """\
OPT
MAX {n_max_optimize_iterations}
VARS
{optimization_parameters}
END
{optimization_goals}
END OPT
"""

PARAMETER_SWEEP = """\
VARSWP
{parameter_sweep}
END VARSWP
"""

OUTPUT_FILE = """
FILEOUT
{response_data}
{pi_spice}
{n_coupled_line_spice}
{broadband_spice}
{inductor_model}
FOLDER {output_directory}
END FILEOUT
"""

PARAMETER_NETLIST = """\
VAR
{parameters}
END VAR
"""

CIRCUIT = """\
CKT
{circuit_elements}
END CKT
"""

SUBDIVIDER = """\
SUBDIV
MAIN {netlist_name}
{reference_planes}
{geometry_names}
{subdivider_locations}
END SUBDIV
"""

QUICK_START_GUIDE = """\
QSG
IMPORT {imported}
EXTRA_METAL NO
UNITS {units_changed}
ALIGN {aligned_to_grid}
REF {reference_planes}
VIEW_RES NO
METALS {metals_defined}
USED YES
END QSG
"""

COMPONENT_DATA_FILES = """\
SMDFILES
{data_files}
END SMDFILES
"""

TRANSLATORS = """\
TRANSLATOR
END TRANSLATOR
"""
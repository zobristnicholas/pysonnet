# geometry project file identifier
GEOMETRY_PROJECT = """\
FTYP SONPROJ 15 ! Sonnet Project File
VER {version}
"""

# netlist project file identifier
NETLIST_PROJECT = """\
FTYP SONNETPROJ 15 ! Sonnet Netlist Project File
VER {version}"""

# header block
HEADER = """\
HEADER
LIC {license_id}
DAT {date}
BUILT_BY_CREATED unknown "unknown version" {date}
BUILT_BY_SAVED unknown "unknown version"
ANN Created by pysonnet
END HEADER
"""

# dimensions block
DIMENSIONS = """\
DIM
CDVY {conductivity}
FREQ {frequency}
RSVY {resistivity}
SRES {sheet_resistance}
IND {inductance}
LNG {length}
ANG {angle}
CON {conductance}
CAP {capacitance}
RES {resistance}
END DIM
"""

# geometry block for geometry project
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
BOX {n_metal_levels} {box_width_x} {box_width_y} {x_cells2} {y_cells2} 20 0
{layers}
{variable_cells}
{technology_layers}
{edge_vias}
{origin}
{ports}
{calibration_group}
{components}
NUM {n_polygons}
{polygons}
END GEO
"""
FREESPACE_FORMAT = '{location} “Free Space” 0 FREESPACE 376.7303136 0 0 0'
GENERAL_METAL_FORMAT = '{location} "{name}" {pattern_id} SUP {r_dc} {r_rf} {x_dc} {ls}'
LAYER_FORMAT = ('{thickness} {xy_epsilon} {xy_mu} {xy_e_loss} {xy_m_loss} {xy_sigma} '
                '{z_partitions} "{name}" {z_epsilon} {z_mu} {z_e_loss} {z_m_loss} '
                '{z_sigma}')
ORIGIN_FORMAT = "LORGN {dx} {dy} {locked}"
PORT_FORMAT = """\
POR1 {port_type} {group_id}
{diagonal}
POLY {file_id} 1
{polygon_index}
{number} {resistance} {reactance} {inductance} {capacitance} {x} {y} {ref_type} {length}
"""
DIAGONAL_FORMAT = "DIAGALLOWED {allowed}"

# frequency block
FREQUENCY = """\
FREQ
{sweeps}
END FREQ
"""
SWEEP_FORMAT = "SWEEP {f1} {f2} {f_step}"
LSWEEP_FORMAT = "LSWEEP {f1} {f2} {n_points}"
ESWEEP_FORMAT = "ESWEEP {f1} {f2} {n_points}"
STEP_FORMAT = "STEP {f1}"
LIST_FORMAT = "LIST {frequency_list}"
DC_FORMAT = "DC_FREQ {f_calc} {frequency}"
ABS_FORMAT = "ABS_ENTRY {f1} {f2}"
ABS_MIN_FORMAT = "ABS_FMIN NET= {s_parameter} {f1} {f2}"
ABS_MAX_FORMAT = "ABS_FMAX NET= {s_parameter} {f1} {f2}"

# control block
CONTROL = """\
CONTROL
{sweep_type}
OPTIONS  {options}
SUBSPLAM Y {subsections_per_wavelength}
{edge_checking}
{subsectioning_frequency}
{estimated_epsilon}
SPEED {speed}
{abs_resolution}
CACHE_ABS {caching_level}
TARG_ABS {abs_target_number}
Q_ACC {q_accuracy}
DET_ABS_RES {resonance_detection}
{hierarchy_sweep}
END CONTROL
"""

# optimization block
OPTIMIZATION = """\
OPT
MAX {n_max_optimize_iterations}
VARS
{optimization_parameters}
END
{optimization_goals}
END OPT
"""

# parameter sweep block
PARAMETER_SWEEP = """\
VARSWP
{parameter_sweep}
END VARSWP
"""

# output file block
OUTPUT_FILE = """
FILEOUT
{response_data}
{pi_spice}
{n_coupled_line_spice}
{broadband_spice}
{inductor_model}
FOLDER {output_folder}
END FILEOUT
"""
RESPONSE_DATA_FORMAT = ("{file_type} {deembed} {include_abs} {filename} "
                        "{include_comments} {precision} {parameter_type} "
                        "{parameter_form} {ports}")
RESPONSE_DATA_NETLIST_FORMAT = ("{file_type} NET={network} {deembed} {include_abs} "
                                "{file_name} {include_comments} {precision} "
                                "{parameter_type} {parameter_form} {ports}")
# parameter block for netlist project
PARAMETER_NETLIST = """\
VAR
{parameters}
END VAR
"""

# circuit block for netlist project
CIRCUIT = """\
CKT
{circuit_elements}
END CKT
"""

# subdivider block for geometry project
SUBDIVIDER = """\
SUBDIV
MAIN {netlist_name}
{reference_planes}
{geometry_names}
{subdivider_locations}
END SUBDIV
"""
REFERENCE_PLANES_FORMAT = "DRP1 {position} {type} {length}"

# quick start guide block for a geometry project
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

# component data files block
COMPONENT_DATA_FILES = """\
SMDFILES
{data_files}
END SMDFILES
"""

# translator block
TRANSLATORS = """\
TRANSLATOR
{translators}
END TRANSLATOR
"""
TRANSLATOR_FORMAT = """\
{translator_type}
{separate_object_layer}
{separate_material_layer}
{divide_vias}
{circle_vias}
{circle_type}
{circle_size}
{keep_metals}
{keep_vias}
{keep_via_pads}
{keep_bricks}
{keep_parent}
{keep_edge_vias}
{convert_parent}
{convert_metal_to_edge_via}
{n_gbr_whole_digits}
{n_gbr_decimal_digits}
{gbr_filename_prefix}
{gbr_filename_extension}
{gbr_filename_type}
{gbr_job_filename_type}
{gbr_job_prefix}
{gbr_units}"""
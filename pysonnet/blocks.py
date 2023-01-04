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
ANN Created by pysonnet {pysonnet_version}
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
UNITS = {'conductivity': {'microsiemens/centimeter': 'USCM', 'uS/cm': 'USCM',
                          'µS/cm': 'USCM',
                          'millisiemens/centimeter': 'MSCM', 'mS/cm': 'MSCM',
                          'siemens/meter': 'SM', 'S/m': 'SM',
                          'siemens/centimeter': 'SCM', 'S/cm': 'SCM'},
         'frequency': {"Hz": "HZ", "hertz": "HZ",
                       "kHz": "KHZ", "kilohertz": "KHZ",
                       "MHz": "MHZ", "megahertz": "MHZ",
                       "GHz": "GHZ", "gigahertz": "GHZ",
                       "THZ": "THZ", "terahertz": "THZ",
                       "PHz": "PHZ", "petahertz": "PHZ"},
         'resistivity': {"ohm centimeter": "OHCM", "ohm cm": "OHCM", "Ω cm": "OHCM",
                         "ohm meter": "OHMM", "ohm m": "OHMM", "Ω m": "OHMM"},
         'sheet_resistance': {"milliohm/square": "MOSQ", "mohm/sq": "MOSQ",
                              "mΩ/sq": "MOSQ",
                              "ohm/square": "OHSQ", "ohm/sq": "OHSQ", "Ω/sq": "OHSQ"},
         'inductance': {"femtohenry": "FH", "fH": "FH",
                        "picohenry": "PH", "pH": "PH",
                        "nanohenry": "NH", "nH": "NH",
                        "microhenry": "UH", "uH": "UH", "µH": "UH",
                        "millihenry": "MH", "mH": "MH",
                        "henry": "H", "H": "H"},
         'length': {"micrometer": "UM", "um": "UM", "µm": "UM",
                    "milliinch": "MIL", "min": "MIL", "mil": "MIL",
                    "millimeter": "MM", "mm": "MM",
                    "centimeter": "CM", "cm": "CM",
                    "inch": "IN", "in": "IN",
                    "foot": "FT", "ft": "FT",
                    "meter": "M", "m": "M"},
         'angle': {"degree": "DEG", "deg": "DEG"},
         'conductance': {"1/ohm": "/OH", "1/Ω": "/OH"},
         'capacitance': {"femtofarad": "FF", "fF": "FF",
                         "picofarad": "PF", "pF": "PF",
                         "nanofarad": "NF", "nF": "NF",
                         "microfarad": "UF", "uF": "UF", "µF": "UF",
                         "millifarad": "MF", "mf": "MF",
                         "farad": "F", "F": "F"},
         'resistance': {"milliohm": "WOH", "mohm": "WOH", "mΩ": "WOH",
                        "ohm": "OH", "Ω": "OH",
                        "kiloohm": "KOH", "kohm": "KOH", "kΩ": "KOH",
                        "megaohm": "MOH", "Mohm": "MOH", "MΩ": "MOH",
                        "gigaohm": "GOH", "Gohm": "GOH", "GΩ": "GOH",
                        "teraohm": "TOH", "Tohm": "TOH", "TΩ": "TOH"}}

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
COVER_TYPES = {'normal': "NOR", 'resistor': "RES", 'native': "NAT", 'general': "SUP",
               'sense': "SEN"}
VIA_TYPES = {'volume loss': "VOL", 'surface loss': "SFC", 'array loss': "ARR"}
METAL_TYPES = {'normal': "NOR", 'resistor': "RES", 'native': "NAT", 'general': "SUP",
               'sense': "SEN", 'thick metal': "TMM", 'rough metal': "RUF"}
WG_LOAD_FORMAT = '{location} "WG Load" 0 WGLOAD'
FREESPACE_FORMAT = '{location} "Free Space" 0 FREESPACE 376.7303136 0 0 0'
LOSSLESS_FORMAT = '{location} "Lossless" 0 SUP 0 0 0 0'
GENERAL_METAL_FORMAT = '{location} "{name}" {pattern_id} SUP {r_dc} {r_rf} {x_dc} {ls}'
ISOTROPIC_DIELECTRIC_BRICK_FORMAT = 'BRI "{name}" {pattern_id} {epsilon} {loss_tangent} {conductivity}'
LAYER_FORMAT = ('{thickness} {xy_epsilon} {xy_mu} {xy_e_loss} {xy_m_loss} {xy_sigma} '
                '{z_partitions} "{name}" {anisotropic} {z_epsilon} {z_mu} '
                '{z_e_loss} {z_m_loss} {z_sigma}')
ORIGIN_FORMAT = "LORGN {dx} {dy} {locked}"
PORT_FORMAT = """\
POR1 {port_type} {group_id}
{diagonal}
POLY {file_id} 1
{polygon_index}
{number} {resistance} {reactance} {inductance} {capacitance} {x} {y} {ref_type} {length}
"""
PORT_TYPES = {"standard": "STD", "auto-grounded": "AGND", "co-calibrated": "CUP"}
DIAGONAL_FORMAT = "DIAGALLOWED {allowed}"
CALIBRATION_GROUP_FORMAT = """\
CUPGRP {group_id}
ID {object_id}
GNDREF {ground}
TWTYPE {terminal_width}
END
"""
TERMINAL_WIDTH_TYPES = {"feedline": "FEED", "cell": "1CELL"}
GROUND_REFERENCE_TYPES = {"floating": "F", "polygon plane": "P", "box cover": "B"}
TERMINAL_WIDTH_VALUE = "CUST \nTWVALUE {value}"
TECHLAYER_FORMAT = """\
TECHLAY {layer_type} "{name}"  <UNSPECIFIED> -1 0
{poly_type}
{level}
{to_level}
END
END
"""
COMPONENT_FORMAT = """\
SMD {level} "{label}"
ID {object_id}
GNDREF {ground}
TWTYPE {terminal_width}
SBOX {symbol_left} {symbol_right} {symbol_top} {symbol_bottom}
PBSHW N
LPOS {label_x} {label_y}
TYPE IDEAL {component_type} {component_value}
SMDP {level} {port1_x} {port1_y} {port1_dir} {port1_num} 1
SMDP {level} {port2_x} {port2_y} {port2_dir} {port2_num} 2
END
"""
COMPONENT_TYPES = {"capacitor": "CAP", "inductor": "IND", "resistor": "RES"}
DIRECTION_TYPES = {"left": "L", "top": "T", "bottom": "B", "right": "R", "diagonal": "D"}
POLYGON_FORMAT = """\
{polygon_type}
{level}
{to_level}
{tech_layer}
{polygon}
END
"""
LAYER_TYPES = {'metal': "METAL", 'via': "VIA", 'dielectric brick': "BRICK"}
POLYGON_TYPES = {'metal': "", 'via': "VIA POLYGON", 'dielectric brick': "BRI POL"}
TECHLAYER_NAME_FORMAT = 'TLAYNAM "{name}" {inherit}'
LEVEL_FORMAT = ("{level} {n_vertices} {material} {fill_type} 0 {x_min} {y_min} {x_max} "
                "{y_max} {conformal_max} 0 0 {edge_mesh}")
TO_LEVEL_FORMAT = "TOLEVEL {to_level} {via_fill_type} {pads}"
FILL_TYPES = {'staircase': 'N', 'diagonal': 'T', 'conformal': 'V'}

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
{analysis_type}
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
DET_ABS_RES {res_detection}
{hierarchy_sweep}
END CONTROL
"""
ANALYSIS_TYPES = {"frequency sweep": "STD", "parameter sweep": "VARSWP",
                  "optimization": "OPTIMIZE"}
OPTION_TYPES = {"current_density": "j", "frequency_cache": "A", "memory_save": "m",
                "box_resonance": "b", "deembed": "d"}
SPEED_TYPES = {"high": 0, "medium": 1, "low": 2}
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
RESPONSE_DATA_FORMAT = ("{file_type} {deembed} {include_abs} {file_name} "
                        "{include_comments} {precision} {parameter_type} "
                        "{parameter_form} {ports}")
RESPONSE_DATA_NETLIST_FORMAT = ("{file_type} NET={network} {deembed} {include_abs} "
                                "{file_name} {include_comments} {precision} "
                                "{parameter_type} {parameter_form} {ports}")
N_COUPLED_LINE_FORMAT = "NCLINE {deembed} {include_abs} {file_name} {precision} {file_type}"
N_COUPLED_LINE_TYPES = {"spectre": "SPECTRE", "spice": "PSPICE"}

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
REFERENCE_PLANES_FORMAT = "DRP1 {position} {plane_type} {length}"
REFERENCE_PLANE_TYPES = {"fixed": "FIX", "FIX": "FIX", "linked": "LINK", "LINK": "LINK"}


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

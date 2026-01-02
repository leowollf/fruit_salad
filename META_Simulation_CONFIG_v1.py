"""
Configuration module for crate storage simulation.
Defines crate types, heights, and stack constraints.

KEY RULE: Stacks can contain mixed crate types, but ALL must be from the same family.
"""

# ============================================================================
# CRATE TYPE DEFINITIONS
# ============================================================================

# IFCO Crate Types (7 types)
IFCO_CRATE_TYPES = {
    "IFCO6408": 86,    # height in mm (slide-in discounted)
    "IFCO6410": 110,    # height in mm (slide-in discounted)
    "IFCO6413": 145,   # height in mm (slide-in discounted)
    "IFCO6416": 177,   # height in mm (slide-in discounted)
    "IFCO6418": 192,   # height in mm (slide-in discounted)
    "IFCO6420": 209,   # height in mm (slide-in discounted)
    "IFCO6424": 231,   # height in mm (slide-in discounted)
}

# Customer Tote Types (3 types)
CUSTOMER_TOTE_TYPES = {
    "CT120": 117.2,   # height in mm (slide-in discounted)
    "CT190": 167.2,   # height in mm (slide-in discounted)
    "CT250": 222.2,   # height in mm (slide-in discounted)
}

# Combined dictionary of all crate types
CRATE_HEIGHTS = {
    **IFCO_CRATE_TYPES,
    **CUSTOMER_TOTE_TYPES
}

# Crate categories for classification
CRATE_CATEGORIES = {
    "IFCO": list(IFCO_CRATE_TYPES.keys()),
    "CUSTOMER_TOTE": list(CUSTOMER_TOTE_TYPES.keys())
}

# ============================================================================
# STACK & PALLET CONSTRAINTS
# ============================================================================

# Stack configuration
STACKS_PER_PALLET = 4
MAX_STACK_HEIGHT_MM = 1750  # Maximum height per stack in millimeters
MIN_STACK_HEIGHT_MM = 1500  # Minimum height per stack in millimeters

# ============================================================================
# BASIC HELPER FUNCTIONS
# ============================================================================

"""
validation of input
"""
def validate_crate_type(crate_type):
    return crate_type in CRATE_HEIGHTS

"""
raise ValueError if some information is missing or incorrect
"""
def get_crate_family(crate_type):
    for family, types in CRATE_CATEGORIES.items():
        if crate_type in types:
            return family
    raise ValueError(f"Unknown crate type: '{crate_type}'")

def get_crate_height(crate_type):
    if crate_type not in CRATE_HEIGHTS:
        raise ValueError(f"Unknown crate type: '{crate_type}'. "
                        f"Available types: {list(CRATE_HEIGHTS.keys())}")
    return CRATE_HEIGHTS[crate_type]


# ============================================================================
# INFORMATION & DEBUGGING FUNCTIONS
# ============================================================================

"""
to receive basic information / summary about one crate type
"""
def get_crate_info(crate_type):
    return {
        "crate_type": crate_type,
        "height_mm": get_crate_height(crate_type),
        "category": get_crate_family(crate_type),
        "max_in_homogeneous_stack": MAX_STACK_HEIGHT_MM // get_crate_height(crate_type),
        "min_in_homogeneous_stack": -(-MIN_STACK_HEIGHT_MM // get_crate_height(crate_type))  # Ceiling division
    }


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
    "IFCO6408": 85,    # height in mm
    "IFCO6410": 95,    # height in mm
    "IFCO6413": 105,   # height in mm
    "IFCO6416": 115,   # height in mm
    "IFCO6418": 125,   # height in mm
    "IFCO6420": 135,   # height in mm
    "IFCO6424": 145,   # height in mm
}

# Customer Tote Types (3 types)
CUSTOMER_TOTE_TYPES = {
    "CT120": 120,   # height in mm
    "CT190": 190,   # height in mm
    "CT250": 250,   # height in mm
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

"""
validation of input
"""
def validate_crate_type(crate_type):
    return crate_type in CRATE_HEIGHTS


# ============================================================================
# STACK-SPECIFIC FUNCTIONS (for mixed crate types)
# ============================================================================

"""
sums up total stack height
"""
def calculate_stack_height(stack_contents):
    total_height = 0
    for crate_type, quantity in stack_contents:
        crate_height = get_crate_height(crate_type)
        total_height += crate_height * quantity
    return total_height

"""
validates that all crate types are from the same family
"""
def validate_stack_family_compatibility(stack_contents):
    if not stack_contents:
        return True  # Empty stack is valid
    
    # Get family of first crate type
    first_crate_type = stack_contents[0][0]
    required_family = get_crate_family(first_crate_type)
    
    # Check all other crate types
    for crate_type, _ in stack_contents:
        if get_crate_family(crate_type) != required_family:
            return False
    
    return True

"""
define stack family. if any crate type in the stack is not of the correct family, function raises error
"""
def get_stack_family(stack_contents):
    if not stack_contents:
        return None
    
    if not validate_stack_family_compatibility(stack_contents):
        raise ValueError("Stack contains mixed crate families - invalid state!")
    
    first_crate_type = stack_contents[0][0]
    return get_crate_family(first_crate_type)

"""
checks if crate can be added to a stack
"""
def can_add_crate_to_stack(stack_contents, crate_type_to_add, quantity_to_add):
    
    # Check family compatibility
    if stack_contents:
        stack_family = get_stack_family(stack_contents)
        new_crate_family = get_crate_family(crate_type_to_add)
        
        if stack_family != new_crate_family:
            return (False, f"Crate family mismatch: stack is {stack_family}, trying to add {new_crate_family}", 0)
    
    # Check height constraint
    current_height = calculate_stack_height(stack_contents)
    remaining_height = MAX_STACK_HEIGHT_MM - current_height
    
    if remaining_height <= 0:
        return (False, "Stack already at maximum height", 0)
    
    # Calculate how many crates fit
    crate_height = get_crate_height(crate_type_to_add)
    max_crates_that_fit = remaining_height // crate_height
    
    if max_crates_that_fit == 0:
        return (False, f"Insufficient height: need {crate_height}mm, only {remaining_height}mm available", 0)
    
    actual_quantity = min(quantity_to_add, max_crates_that_fit)
    return (True, "OK", actual_quantity)


"""
validates the correctness of a stack (all crates from same family, height within min-/max-limits)
"""
def is_valid_stack(stack_contents):
    if not stack_contents:
        return (False, "Stack is empty")
    
    # Check family compatibility
    if not validate_stack_family_compatibility(stack_contents):
        return (False, "Stack contains mixed crate families")
    
    # Check height constraints
    total_height = calculate_stack_height(stack_contents)
    
    if total_height < MIN_STACK_HEIGHT_MM:
        return (False, f"Stack too short: {total_height}mm < {MIN_STACK_HEIGHT_MM}mm minimum")
    
    if total_height > MAX_STACK_HEIGHT_MM:
        return (False, f"Stack too tall: {total_height}mm > {MAX_STACK_HEIGHT_MM}mm maximum")
    
    return (True, "Valid stack")


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


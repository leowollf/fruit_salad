
import pandas as pd
from META_Simulation_CONFIG_v1 import (
    STACKS_PER_PALLET,
    MAX_STACK_HEIGHT_MM,
    MIN_STACK_HEIGHT_MM,
    get_crate_family,
    get_crate_height
)

class Order:
    def __init__(self, OUT_ID, article_code, article_description, shop_destination, quantity):
        self.ID = OUT_ID
        self.article_code = str(article_code)
        self.article_description = article_description
        self.shop = shop_destination
        self.original_quantity = int(quantity)
        self.remaining_quantity = int(quantity)

def read_orders(file_path="Outfeed-Excel"):
    """
    Reads order list from Excel and returns a list of Order objects.
    Expected columns:
    - OUT_ID, article_code, article_description, shop_destination, OUT_quantity
    """
    df = pd.read_excel(file_path)
    order_list = []

    for idx, row in df.iterrows():
        if pd.isna(row['article_code']) or pd.isna(row['OUT_quantity']):
            continue

        order = Order(
            OUT_ID=row.get("OUT_ID", None),
            article_code=row["article_code"],
            article_description=row.get("article_description", ""),
            shop_destination=row["shop_destination"],
            quantity=row["OUT_quantity"]
        )
        order_list.append(order)
    return order_list


# ============================================================================
# STACK-SPECIFIC FUNCTIONS
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

# ====================================================================================================================================
# CORE OUTFEED FUNCTION
# ====================================================================================================================================

def try_outfeed(storage, orders):
    """
    Execute one outfeed pallet using height-based stack logic.
    
    Rules:
    - Pallet has 4 stacks
    - ALL 4 stacks must be valid: 1500-1750mm height (if pallet is used)
    - Mixed crate types allowed within stack, but must be same family (IFCO or CUSTOMER_TOTE)
    - Orders don't specify crate_type - use whatever is available in storage
    - Fill stacks sequentially
    
    Returns True if pallet was created, False otherwise.
    """
    
    # Get shops with unfulfilled orders
    shops_with_orders = set(order.shop for order in orders if order.remaining_quantity > 0)

    for shop in shops_with_orders:
        # Initialize 4 empty stacks
        stacks = [[] for _ in range(STACKS_PER_PALLET)]
        current_stack_idx = 0
        
        # Track what we're picking: list of (order, article_code, crate_type, quantity) tuples
        picks = []
        
        # Try to fill stacks with orders for this shop
        for order in orders:
            # Skip if wrong shop or already fulfilled
            if order.shop != shop or order.remaining_quantity <= 0:
                continue
            
            # Find ALL available crate_types for this article_code in storage
            available_crates = []
            for (stored_article, stored_crate_type), qty in storage.items():
                if stored_article == order.article_code and qty > 0:
                    available_crates.append((stored_crate_type, qty))
            
            if not available_crates:
                continue  # No crates available for this article

            # Try to pick from available crate types
            qty_still_needed = order.remaining_quantity

            # Work on a COPY so we can mutate safely
            available_crates_working = available_crates.copy()

            while available_crates_working and qty_still_needed > 0:
                crate_type, available_qty = available_crates_working.pop(0)

                qty_to_try = min(qty_still_needed, available_qty)

                # Try to add to current stack (or subsequent stacks)
                while qty_to_try > 0 and current_stack_idx < STACKS_PER_PALLET:
                    # Check if we can add to current stack
                    can_add, reason, max_qty = can_add_crate_to_stack(
                        stacks[current_stack_idx],
                        crate_type,
                        qty_to_try
                    )

                    if can_add and max_qty > 0:
                        # Add to current stack
                        stacks[current_stack_idx].append((crate_type, max_qty))
                        picks.append((order, order.article_code, crate_type, max_qty))
                        qty_to_try -= max_qty
                        qty_still_needed -= max_qty

                        # Check if stack reached minimum height to move to next
                        current_height = calculate_stack_height(stacks[current_stack_idx])
                        if current_height >= MIN_STACK_HEIGHT_MM: # MIN height reached ...
                            current_stack_idx += 1
                            continue # ... and move on to next stack
                    else:
                        # Can't add to current stack, move to next
                        current_stack_idx += 1
                    
                # Stop if all stacks are filled
                if current_stack_idx >= STACKS_PER_PALLET:
                    break

            # Stop filling if all stacks used
            if current_stack_idx >= STACKS_PER_PALLET:
                break
        
        # CRITICAL VALIDATION: ALL 4 STACKS MUST BE VALID
        # Count non-empty stacks
        non_empty_stacks = [i for i, stack in enumerate(stacks) if len(stack) > 0]
        
        # Checks that n° of stacks equals STACKS_PER_PALLET; if less, next shop is evaluated
        if len(non_empty_stacks) < STACKS_PER_PALLET:
            print(
            f"✗ Rejected pallet for shop {shop} "
            f"- only {len(non_empty_stacks)}/{STACKS_PER_PALLET} stacks built"
            )
            continue

        
        # Check if ALL non-empty stacks are valid (1500-1750mm)
        all_stacks_valid = True
        invalid_stacks = []
        
        for i in non_empty_stacks:
            is_valid, reason = is_valid_stack(stacks[i])
            if not is_valid:
                all_stacks_valid = False
                invalid_stacks.append((i, reason))
        
        # Only proceed if ALL stacks are valid
        if not all_stacks_valid:
            # Pallet rejected - at least one stack is invalid
            print(f"✗ Rejected pallet for shop {shop} - invalid stacks:")
            for stack_idx, reason in invalid_stacks:
                height = calculate_stack_height(stacks[stack_idx])
                print(f"  Stack {stack_idx+1}: {height}mm - {reason}")
            continue  # Try next shop
        
        # All stacks valid! Execute the outfeed
        # Remove from storage and update orders
        for order, article_code, crate_type, qty in picks:
            key = (article_code, crate_type)
            storage[key] -= qty
            if storage[key] == 0:
                del storage[key]
            order.remaining_quantity -= qty
        
        # Print pallet info
        total_crates = sum(qty for _, _, _, qty in picks)
        print(f"✓ Created outfeed pallet for shop {shop}: {total_crates} crates in {len(non_empty_stacks)} stacks")
        
        for i, stack in enumerate(stacks):
            if len(stack) > 0:
                height = calculate_stack_height(stack)
                family = get_crate_family(stack[0][0])
                print(f"  Stack {i+1}: {height}mm ({family})")
                for crate_type, qty in stack:
                    print(f"    - {qty}x {crate_type}")
        
        return True
    
    return False  # No pallet could be created
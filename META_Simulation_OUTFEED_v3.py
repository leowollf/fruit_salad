import pandas as pd
from META_Simulation_CONFIG_v1 import (
    STACKS_PER_PALLET,
    MAX_STACK_HEIGHT_MM,
    MIN_STACK_HEIGHT_MM,
    get_crate_family,
    get_crate_height,
    get_stack_family,
    validate_stack_family_compatibility
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

def calculate_stack_height(stack_contents):
    total_height = 0
    for _, crate_type, quantity in stack_contents:
        crate_height = int(get_crate_height(crate_type))
        total_height += crate_height * int(quantity)
    return total_height


def can_add_crate_to_stack(stack_contents, crate_type_to_add, quantity_to_add):
    if stack_contents:
        stack_family = get_stack_family(stack_contents)
        new_crate_family = get_crate_family(crate_type_to_add)

        if stack_family != new_crate_family:
            return (False, f"Crate family mismatch: stack is {stack_family}, trying to add {new_crate_family}", 0)

    current_height = int(calculate_stack_height(stack_contents))
    remaining_height = int(MAX_STACK_HEIGHT_MM) - current_height

    if remaining_height <= 0:
        return (False, "Stack already at maximum height", 0)

    crate_height = int(get_crate_height(crate_type_to_add))
    max_crates_that_fit = remaining_height // crate_height

    if max_crates_that_fit == 0:
        return (False, f"Insufficient height: need {crate_height}mm, only {remaining_height}mm available", 0)

    actual_quantity = int(min(int(quantity_to_add), int(max_crates_that_fit)))
    return (True, "OK", actual_quantity)


def is_valid_stack(stack_contents):
    if not stack_contents:
        return (False, "Stack is empty")

    if not validate_stack_family_compatibility(stack_contents):
        return (False, "Stack contains mixed crate families")

    total_height = calculate_stack_height(stack_contents)

    if total_height < MIN_STACK_HEIGHT_MM:
        return (False, f"Stack too short: {int(total_height)}mm < {MIN_STACK_HEIGHT_MM}mm minimum")

    if total_height > MAX_STACK_HEIGHT_MM:
        return (False, f"Stack too tall: {int(total_height)}mm > {MAX_STACK_HEIGHT_MM}mm maximum")

    return (True, "Valid stack")


# ============================================================================
# CORE OUTFEED FUNCTION
# ============================================================================

def try_outfeed(storage, orders):
    shops_with_orders = set(order.shop for order in orders if order.remaining_quantity > 0)

    for shop in shops_with_orders:
        stacks = [[] for _ in range(STACKS_PER_PALLET)]
        current_stack_idx = 0

        picks = []
        stack_pick_start_idx = 0  # NEW: start index of picks belonging to current stack

        for order in orders:
            if order.shop != shop or order.remaining_quantity <= 0:
                continue

            available_crates = []
            for (stored_article, stored_crate_type), qty in storage.items():
                if stored_article == order.article_code and qty > 0:
                    available_crates.append((stored_crate_type, int(qty)))

            if not available_crates:
                continue

            qty_still_needed = int(order.remaining_quantity)
            available_crates_working = available_crates.copy()

            while available_crates_working and qty_still_needed > 0:
                crate_type, available_qty = available_crates_working.pop(0)
                qty_to_try = min(int(qty_still_needed), int(available_qty))

                while qty_to_try > 0 and current_stack_idx < STACKS_PER_PALLET:
                    can_add, reason, max_qty = can_add_crate_to_stack(
                        stacks[current_stack_idx],
                        crate_type,
                        qty_to_try
                    )

                    if can_add and max_qty > 0:
                        max_qty = int(max_qty)

                        stacks[current_stack_idx].append((order.article_code, crate_type, max_qty))
                        picks.append((order, order.article_code, crate_type, max_qty))

                        qty_to_try -= max_qty
                        qty_still_needed -= max_qty

                        current_height = calculate_stack_height(stacks[current_stack_idx])
                        if current_height >= MIN_STACK_HEIGHT_MM:
                            current_stack_idx += 1
                            stack_pick_start_idx = len(picks)  # NEW: next stack starts here
                            continue

                    elif (
                        not can_add
                        and get_stack_family(stacks[current_stack_idx]) is not None  # NEW: guard
                        and get_crate_family(crate_type) != get_stack_family(stacks[current_stack_idx])
                        and calculate_stack_height(stacks[current_stack_idx]) < MIN_STACK_HEIGHT_MM
                    ):
                        stacks[current_stack_idx].clear()
                        del picks[stack_pick_start_idx:]  # NEW: rollback all picks of this stack
                        continue

                    else:
                        current_stack_idx += 1
                        stack_pick_start_idx = len(picks)  # NEW: next stack starts here

                if current_stack_idx >= STACKS_PER_PALLET:
                    break

            if current_stack_idx >= STACKS_PER_PALLET:
                break

        non_empty_stacks = [i for i, stack in enumerate(stacks) if len(stack) > 0]

        if len(non_empty_stacks) < STACKS_PER_PALLET:
            print(
                f"✗ Rejected pallet for shop {shop} "
                f"- only {len(non_empty_stacks)}/{STACKS_PER_PALLET} stacks built"
            )
            continue

        all_stacks_valid = True
        invalid_stacks = []

        for i in non_empty_stacks:
            is_valid, reason = is_valid_stack(stacks[i])
            if not is_valid:
                all_stacks_valid = False
                invalid_stacks.append((i, reason))

        if not all_stacks_valid:
            print(f"✗ Rejected pallet for shop {shop} - invalid stacks:")
            for stack_idx, reason in invalid_stacks:
                height = calculate_stack_height(stacks[stack_idx])
                print(f"  Stack {stack_idx+1}: {int(height)}mm - {reason}")
            continue

        # Execute outfeed (AGGREGATED & STRICT):
        # 1) Aggregate planned picks per storage key to avoid double-touching deleted keys.
        # 2) Validate feasibility against storage; reject pallet if infeasible (keeps balance).
        required_by_key = {}
        for order, article_code, crate_type, qty in picks:
            key = (article_code, crate_type)
            qty = int(qty)
            required_by_key[key] = required_by_key.get(key, 0) + qty

        invalid_plan = False
        for key, req in required_by_key.items():
            if key not in storage:
                print(f"✗ Rejected pallet for shop {shop} - planned key not in storage: {key}")
                invalid_plan = True
                break
            if int(storage[key]) < int(req):
                print(f"✗ Rejected pallet for shop {shop} - insufficient stock for {key}: have {storage[key]}, need {req}")
                invalid_plan = True
                break

        if invalid_plan:
            continue  # Try next shop

        # Apply storage updates once per key
        for key, req in required_by_key.items():
            storage[key] -= int(req)
            if storage[key] == 0:
                del storage[key]

        # Update order remaining quantities exactly as planned
        for order, article_code, crate_type, qty in picks:
            order.remaining_quantity -= int(qty)

        total_crates = sum(int(qty) for _, _, _, qty in picks)
        print(f"\n✓ Created outfeed pallet for shop {shop}: {int(total_crates)} crates in {len(non_empty_stacks)} stacks")

        for i, stack in enumerate(stacks):
            if len(stack) > 0:
                height = calculate_stack_height(stack)
                family = get_crate_family(stack[0][1])
                print(f"  Stack {i+1}: {int(height)}mm ({family})")
                for article_code, crate_type, qty in stack:
                    print(f"    - {int(qty):>2}x {crate_type} - {article_code}")

        return {
            "pallet_built": True,
            "shop": shop,
            "stacks": stacks
        }

    return {
        "pallet_built": False,
        "shop": None,
        "stacks": None
    }



## NOTES
#1 should shops be sequenced in function "try_outfeed"; currently randomly ordered
#2 should orderlines be sequenced in function "try_outfeed"; currently randomly ordered
#3 once an orderline is fulfilled and stack >=1500mm, stack is completed -> should be changed? can be removed or changed
#3...: it must be considered that there is a (small) tendency that a pallet is not produced even though enough crates would be available
#3...: can happen that stack 1-3 very high, but 4 not enough crates (but, also now this can happen)
#4 should we include the slide-in in stack height calculation?
#5 orders with qty "NULL" are skipped because no quantity. should this be the case or should there be an error?
#6 must have: sort storage by crate family; optional: sort crate family by crate height (see sceanrio 3 of test cases)
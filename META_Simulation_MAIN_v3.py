# before starting the simulation, check the following:
# 1: check imported Excel file name (infeed and outfeed) in main function
# 2: make sure that the column headers in the Excel file are according to predefined strings (see INFEED-file -> infeed_source)
# 3: make sure that in the main file, all the imports refer to the correct version of the sub-files


from META_Simulation_STORAGE_v1 import (
    create_empty_storage,
    add_crates_to_storage
)
from META_Simulation_INFEED_v1 import (
    infeed_source,
)
from META_Simulation_LOGGING_v1 import (
    kpi_storage_detail,
    kpi_total_crates,
    kpi_family_counts,
    IterationExcelLogger,
    log_infeed_iteration
)
from META_Simulation_OUTFEED_v3 import (
    try_outfeed,
    read_orders
)


def main():
    # create empty storage
    storage = create_empty_storage()

    # Excel iteration logger (created once)
    excel_logger = IterationExcelLogger(filepath="storage_iteration_log.xlsx")
    total_number_of_creates = 0  # cumulative across the whole simulation

    # defining Excel file for reading
    infeeds = infeed_source("Infeed_Test-michar.xlsx")
    # defining Excel file for orders
    orders = read_orders("Outfeed_Test.xlsx")

    iteration = 1
    infeed_index = 0
    total_infeeds = len(infeeds)

    # loop for sequence (infeed - outfeed - log)
    while True:
        print(f"\n=== ITERATION {iteration} ===")

        current_infeed = None

        # 1) Infeed exactly one pallet if available
        if infeed_index < total_infeeds:
            current_infeed = infeeds[infeed_index]
            add_crates_to_storage(storage, current_infeed)

            # update cumulative creates counter
            total_number_of_creates += current_infeed.quantity

            print(f"Infeed executed (pallet {infeed_index + 1})\t- {current_infeed.article_code}")
            infeed_index += 1
        else:
            print("No infeed left for this iteration")

        # 2) Try exactly one outfeed
        success = try_outfeed(storage, orders)
        if success:
            print("Outfeed executed")
        else:
            print("No outfeed possible")

        # === DEBUG: Print all orders and remaining quantities ===
#        print("\n=== Orders check ===")
#        for order in orders:
#            print(f"Order ID: {order.ID}, Shop: {order.shop}, SKU: {order.article_code}, "
#            f"Ordered: {order.original_quantity}, Remaining: {order.remaining_quantity}")
#        print("=== End of orders check ===\n")

        # 3 Log infeed activity (always one row per iteration)
        log_infeed_iteration(
            iteration=iteration,
            infeed_obj=current_infeed
        )

        # 4 Log current storage state
        print("\nTotal crates in storage:", kpi_total_crates(storage))
        print("Detailed storage status:")
        for article_code, crate_types in kpi_storage_detail(storage).items():
            for crate_type, quantity in crate_types.items():
                print(f"  {article_code} - {crate_type:>8} - {article_code}: {quantity:>3} crates")

        # 4) Excel logging at end of iteration
        ifco_in_storage, customer_in_storage = kpi_family_counts(storage)
        excel_logger.append_row(
            iteration=iteration,
            total_number_of_creates=total_number_of_creates,
            ifco_crates=ifco_in_storage,
            customer_crates=customer_in_storage
        )

        # 5 Stop Condition: Rule = stop if no infeed left AND no outfeed possible
        if infeed_index >= total_infeeds and not success:
            print("\nSimulation finished: no more infeed and no outfeed possible")
            break

        iteration += 1


if __name__ == "__main__":
    main()


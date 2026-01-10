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
    log_infeed_iteration,
    log_outfeed_iteration
)
from META_Simulation_OUTFEED_v3 import (
    try_outfeed,
    read_orders
)


def main():
    # create empty storage
    storage = create_empty_storage()

    # Excel iteration logger (created once)
    excel_logger = IterationExcelLogger(filepath="Storage_Log.xlsx")
    infeed_until_now = 0  # cumulative across the whole simulation

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

        # 1.1) Infeed exactly one pallet if available
        if infeed_index < total_infeeds:
            current_infeed = infeeds[infeed_index]
            add_crates_to_storage(storage, current_infeed)

            # update cumulative creates counter
            infeed_until_now += current_infeed.quantity

            print(f"Infeed executed (pallet {infeed_index + 1})\t- {current_infeed.article_code}")
            infeed_index += 1
        else:
            print("No infeed left for this iteration")

        # 1.2) Log infeed activity (always one row per iteration)
        log_infeed_iteration(
            iteration=iteration,
            infeed_obj=current_infeed
        )

        # 2.1) Try exactly one outfeed
        outfeed_result = try_outfeed(storage, orders)

        if outfeed_result["pallet_built"]:
            print("Outfeed executed")
        else:
            print("No outfeed possible")


        #2.2) Log outfeed activity (always one row per iteration) 
        log_outfeed_iteration(
            iteration=iteration,
            pallet_built=outfeed_result["pallet_built"],
            shop=outfeed_result["shop"],
            stacks=outfeed_result["stacks"]
        )


        # 3.1) Print current storage state
        print("\nTotal crates in storage:", kpi_total_crates(storage))
        print("Detailed storage status:")
        for article_code, crate_types in kpi_storage_detail(storage).items():
            for crate_type, quantity in crate_types.items():
                print(f"  {article_code} - {crate_type:>8} - {article_code}: {quantity:>3} crates")

        # 3.2) Log storage situation (always one row per iteration
        excel_logger.append_row(
            iteration=iteration,
            infeed_until_now=infeed_until_now,
            storage=storage
        )

        # 4) Stop Condition: Rule = stop if no infeed left AND no outfeed possible
        if infeed_index >= total_infeeds and not outfeed_result["pallet_built"]:
            print("\nSimulation finished: no more infeed and no outfeed possible")
            break

        iteration += 1


if __name__ == "__main__":
    main()


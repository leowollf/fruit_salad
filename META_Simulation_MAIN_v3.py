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
    kpi_total_crates
)
from META_Simulation_OUTFEED_v3 import (
    try_outfeed,
    read_orders
)



def main():
    # create empty storage
    storage = create_empty_storage()
    
    # defining Excel file for reading
    infeeds = infeed_source(
        "C:/Users/gatmichar/Documents/eiddpython/eidppython24w-code/lecture_01/Infeed_Test.xlsx"
    )
    # defining Excel file for orders
    orders = read_orders(
    "C:/Users/gatmichar/Documents/eiddpython/eidppython24w-code/lecture_01/Outfeed_Test.xlsx"
    )
    


    iteration = 1
    infeed_index = 0
    total_infeeds = len(infeeds)

    # loop for sequence (infeed - outfeed - log)
    while True:
        print(f"\n=== ITERATION {iteration} ===")

        # 1️ Infeed exactly one pallet if available
        if infeed_index < total_infeeds:
            current_infeed = infeeds[infeed_index]
            add_crates_to_storage(storage, current_infeed)
            print(f"Infeed executed (pallet {infeed_index + 1})")
            infeed_index += 1
        else:
            print("No infeed left for this iteration")

        # 2️ Try exactly one outfeed
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


        # 3️ Log current storage state
        print("Total crates in storage:", kpi_total_crates(storage))
        print("Detailed storage status:")
        for article_code, crate_types in kpi_storage_detail(storage).items():
            for crate_type, quantity in crate_types.items():
                print(f"  {article_code} - {crate_type}: {quantity} crates")

        iteration += 1

        # 4 Rule: stop if no infeed left AND no outfeed possible
        if infeed_index >= total_infeeds and not success:
            print("\nSimulation finished: no more infeed and no outfeed possible")
            break




if __name__ == "__main__":
    main()


import pandas as pd

class Order:
    def __init__(self, ID, article_code, article_description, shop, quantity, crate_type="IFCO"):
        self.ID = ID
        self.article_code = str(article_code)
        self.article_description = article_description
        self.shop = shop
        self.crate_type = crate_type
        self.original_quantity = int(quantity)
        self.remaining_quantity = int(quantity)

def read_orders(file_path="Outfeed-Excel"):
    """
    Reads order list from Excel and returns a list of Order objects.
    Expected columns:
    - OUT-ID, article_code, article_description, shop_destination, OUT-quantity
    """
    df = pd.read_excel(file_path)
    order_list = []

    for _, row in df.iterrows():
        if pd.isna(row['article_code']) or pd.isna(row['OUT-quantity']):
            continue

        order = Order(
            ID=row.get("OUT-ID", None),
            article_code=row["article_code"],
            article_description=row.get("article_description", ""),
            shop=row["shop_destination"],
            quantity=row["OUT-quantity"]
        )
        order_list.append(order)
    return order_list


def try_outfeed(storage, orders):
    """
    Execute one outfeed pallet.
    - Max 40 crates per pallet
    - Min 32 crates per pallet
    - Only crates available in storage can be used
    - Pallet can combine multiple order lines for the same shop
    - Crate type is ignored for decision-making but respected in storage
    Returns True if pallet was created, False otherwise.
    """
    MAX_CRATES = 40
    MIN_CRATES = 32

    # Track which shops have unfulfilled orders
    shops_with_orders = set(order.shop for order in orders if order.remaining_quantity > 0)

    for shop in shops_with_orders:
        pallet_crates = 0
        pallet_content = []  # list of tuples: (order, qty)

        # Iterate over all orders for this shop
        for order in orders:
            if order.shop != shop or order.remaining_quantity <= 0:
                continue

            # Calculate total available crates for this article_code in storage (ignore crate_type)
            available = sum(qty for (code, crate_type), qty in storage.items() if code == order.article_code)
            if available <= 0:
                continue

            remaining_space = MAX_CRATES - pallet_crates
            pick_qty = min(order.remaining_quantity, available, remaining_space)

            if pick_qty > 0:
                pallet_content.append((order, pick_qty))
                pallet_crates += pick_qty

            if pallet_crates >= MAX_CRATES:
                break

        # Only create pallet if minimum requirement is met
        if pallet_crates >= MIN_CRATES:
            # Reduce quantities in storage respecting crate_type
            for order, qty_to_pick in pallet_content:
                remaining_to_pick = qty_to_pick
                # iterate over all matching keys in storage
                for (code, crate_type), available_qty in list(storage.items()):
                    if code != order.article_code:
                        continue
                    take = min(available_qty, remaining_to_pick)
                    storage[(code, crate_type)] -= take
                    remaining_to_pick -= take
                    if storage[(code, crate_type)] == 0:
                        del storage[(code, crate_type)]
                    if remaining_to_pick == 0:
                        break
                order.remaining_quantity -= qty_to_pick

            print(f"Created outfeed pallet for shop {shop}: {pallet_crates} crates")
            print("  Pallet contents:")
            for order, qty in pallet_content:
                print(f"    {order.article_code} - {qty} crates")
            return True

    return False  # no pallet could be created


# is a function to return the detailed structure of the current situation of the storage: {article_code, crate_type, quantity}
def kpi_storage_detail(storage):
    """
    Returns a detailed overview of all crates in the storage area.

    Output format:
    {
        article_code: {
            crate_type: quantity
        }
    }
    """
    result = {}

    for (article_code, crate_type), quantity in storage.items():
        if article_code not in result:
            result[article_code] = {}

        result[article_code][crate_type] = quantity

    return result

# is a function to return the total n° of crates in the current storage
def kpi_total_crates(storage):
    return sum(storage.values())

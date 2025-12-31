import pandas as pd
from META_Simulation_CONFIG_v1 import validate_crate_type

class Infeed:
    def __init__(self, ID, article_code, article_description, crate_type, quantity):
        self.ID = ID
        self.article_code = article_code
        self.article_description = article_description
        self.crate_type = crate_type
        self.quantity = quantity


def infeed_source(file_path="Infeed-Excel"):
    """
    Reads infeed pallets from an Excel file and returns a list of Infeed objects.

    Excel columns:
        - IN-ID
        - SKU_code (article_code)
        - SKU_description
        - crate_type
        - IN-quantity
    """
    df = pd.read_excel(file_path)

    infeed_list = []

    for idx, row in df.iterrows():
        # Skip rows with missing article_code or quantity
        if pd.isna(row['article_code']) or pd.isna(row['IN-quantity']):
            continue

        # Validate crate_type
        crate_type = row["crate_type"]
        if not validate_crate_type(crate_type):
            print(f"ERROR: Invalid crate_type '{crate_type}' in row {idx+2}")
            print(f"Please use one of: IFCO6408, IFCO6410, IFCO6413, IFCO6416, IFCO6418, IFCO6420, IFCO6424, CT120, CT190, CT250")
            raise ValueError(f"Invalid crate_type: {crate_type}")

        infeed_row = Infeed(
            ID=row.get("IN-ID", None),
            article_code=str(row["article_code"]),
            article_description=row.get("article_description", ""),
            crate_type=row["crate_type"],
            quantity=int(row["IN-quantity"])
        )
        infeed_list.append(infeed_row)

    return infeed_list
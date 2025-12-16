class Infeed:
    def __init__(self, ID, article_code, article_description, crate_type, quantity):
        self.ID = ID
        self.article_code = article_code
        self.article_description = article_description
        self.crate_type = crate_type
        self.quantity = quantity

import pandas as pd

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

    for _, row in df.iterrows():
        # Skip rows with missing article_code or quantity
        if pd.isna(row['article_code']) or pd.isna(row['IN-quantity']):
            continue

        infeed_row = Infeed(
            ID=row.get("IN-ID", None),
            article_code=str(row["article_code"]),
            article_description=row.get("article_description", ""),
            crate_type=row["crate_type"],
            quantity=int(row["IN-quantity"])
        )
        infeed_list.append(infeed_row)

    return infeed_list
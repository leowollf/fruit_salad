import pandas as pd
from dataclasses import dataclass


# -----------------------------
# Data object
# -----------------------------
@dataclass(frozen=True)
class InfeedEvent:
    article_code: str
    crate_id: str
    family: str
    crate_height: float
    quantity: int


# -----------------------------
# Loader
# -----------------------------
def load_crate_master(path: str) -> dict:
    """
    Loads crate master data.
    Returns dict: crate_id -> {family, height}
    """
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    required = {"Crate_ID", "family", "Height"}
    if not required.issubset(df.columns):
        raise ValueError(f"Crate master missing columns: {required - set(df.columns)}")

    crate_master = {}
    for _, row in df.iterrows():
        crate_master[row["Crate_ID"]] = {
            "family": row["family"],
            "height": float(row["Height"])
        }

    return crate_master


def load_infeed(path: str, crate_master: dict) -> list[InfeedEvent]:
    """
    Loads infeed Excel and returns list of InfeedEvents.
    """
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    required = {"article_code", "Crate_ID", "ToteQty"}
    if not required.issubset(df.columns):
        raise ValueError(f"Infeed file missing columns: {required - set(df.columns)}")

    events = []

    for _, row in df.iterrows():
        if pd.isna(row["article_code"]) or pd.isna(row["ToteQty"]):
            continue

        crate_id = row["Crate_ID"]

        if crate_id not in crate_master:
            raise ValueError(f"Unknown Crate_ID in infeed: {crate_id}")

        spec = crate_master[crate_id]

        events.append(
            InfeedEvent(
                article_code=str(row["article_code"]),
                crate_id=crate_id,
                family=spec["family"],
                crate_height=spec["height"],
                quantity=int(row["ToteQty"])
            )
        )

    return events




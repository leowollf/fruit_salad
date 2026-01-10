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



"""
Storage Logging 
"""

from pathlib import Path
from datetime import datetime
from openpyxl import Workbook, load_workbook
from META_Simulation_CONFIG_v1 import get_crate_family


def kpi_family_counts(storage):
    """
    Returns totals by family based on current storage.
    Output: (ifco_total, customer_total)
    """
    ifco = 0
    customer = 0

    for (article_code, crate_type), qty in storage.items():
        family = get_crate_family(crate_type)
        if family == "IFCO":
            ifco += qty
        elif family == "CUSTOMER_TOTE":
            customer += qty

    return ifco, customer


class IterationExcelLogger:
    def __init__(self, filepath="storage_iteration_log.xlsx", sheet_name="log"):
        self.filepath = Path(filepath)
        self.sheet_name = sheet_name
        self._ensure_file()

    def _ensure_file(self):
        if self.filepath.exists():
            return

        wb = Workbook()
        ws = wb.active
        ws.title = self.sheet_name

        ws.append([
            "timestamp",
            "iteration",
            "total_number_of_creates",
            "ifco_crates_in_storage",
            "customer_crates_in_storage",
        ])

        wb.save(self.filepath)

    def append_row(self, iteration, total_number_of_creates, ifco_crates, customer_crates):
        wb = load_workbook(self.filepath)
        ws = wb[self.sheet_name]

        ws.append([
            datetime.now().isoformat(timespec="seconds"),
            int(iteration),
            int(total_number_of_creates),
            int(ifco_crates),
            int(customer_crates),
        ])

        wb.save(self.filepath)

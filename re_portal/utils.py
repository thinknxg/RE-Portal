import frappe
from frappe.utils import fmt_money


def money(amount, currency=None):
    """Template helper: OMR renders with 3 decimals via Currency settings."""
    if amount is None:
        return ""
    return fmt_money(amount, currency=currency or
                     frappe.db.get_single_value("RE Portal Settings", "currency_label") or "OMR")

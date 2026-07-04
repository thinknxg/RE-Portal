import frappe
from re_portal.api.tenant import _active_lease
from re_portal.utils import money
from re_portal.www.tenant_portal_common import require_tenant_context


def get_context(context):
    tenant = require_tenant_context(context)
    lease = _active_lease(tenant)
    context.lease = lease
    context.money = money
    if lease:
        context.unit_title = frappe.db.get_value("Unit", lease.unit, "unit_title")
        context.charges = frappe.get_all(
            "Lease Charge", filters={"parent": lease.name},
            fields=["charge_type", "description", "amount"], order_by="idx asc")
        deposit = lease.security_deposit and frappe.db.get_value(
            "Security Deposit", lease.security_deposit,
            ["amount", "status"], as_dict=True)
        context.deposit = deposit
        context.contract_pdf = (
            "/api/method/frappe.utils.print_format.download_pdf"
            f"?doctype=Lease%20Contract&name={lease.name}")
    context.title = "My Lease"
    return context

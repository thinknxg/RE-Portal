"""Tenant self-service APIs. Identity is always resolved from the session user;
tenant IDs are never accepted from the client."""

import frappe
from frappe import _
from frappe.utils import fmt_money, getdate, nowdate


def _require_tenant():
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in."), frappe.PermissionError)
    from re_core.re_core.doctype.tenant.tenant import get_tenant_for_user
    tenant = get_tenant_for_user()
    if not tenant:
        frappe.throw(_("No tenant profile is linked to your account."),
                     frappe.PermissionError)
    return tenant


def _active_lease(tenant):
    return frappe.db.get_value(
        "Lease Contract",
        {"tenant": tenant, "docstatus": 1, "status": ["in", ["Active", "Expiring"]]},
        ["name", "unit", "property", "start_date", "end_date", "status",
         "total_contract_value", "payment_frequency", "rent_schedule",
         "security_deposit"],
        as_dict=True, order_by="end_date desc")


@frappe.whitelist()
def dashboard():
    tenant = _require_tenant()
    tenant_doc = frappe.db.get_value("Tenant", tenant, ["tenant_name"], as_dict=True)
    lease = _active_lease(tenant)
    out = {"tenant": tenant, "tenant_name": tenant_doc.tenant_name, "lease": lease,
           "next_installment": None, "open_requests": 0, "overdue_count": 0}
    if lease:
        out["unit_title"] = frappe.db.get_value("Unit", lease.unit, "unit_title")
        out["next_installment"] = frappe.db.get_value(
            "Rent Installment",
            {"parent": lease.rent_schedule,
             "status": ["in", ["Pending", "Invoiced", "Overdue"]]},
            ["due_date", "amount", "status"], as_dict=True, order_by="due_date asc")
        out["overdue_count"] = frappe.db.count(
            "Rent Installment", {"parent": lease.rent_schedule, "status": "Overdue"})
    out["open_requests"] = frappe.db.count(
        "Maintenance Request",
        {"tenant": tenant, "status": ["in", ["Open", "In Progress", "On Hold"]]})
    return out


@frappe.whitelist()
def installments():
    tenant = _require_tenant()
    lease = _active_lease(tenant)
    if not lease:
        return {"lease": None, "installments": []}
    rows = frappe.get_all(
        "Rent Installment",
        filters={"parent": lease.rent_schedule},
        fields=["installment_no", "due_date", "amount", "status",
                "sales_invoice", "pdc"],
        order_by="installment_no asc")
    for row in rows:
        row["invoice_pdf"] = (
            f"/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice"
            f"&name={row.sales_invoice}" if row.sales_invoice else None)
    return {"lease": lease, "installments": rows}


@frappe.whitelist()
def maintenance_list():
    tenant = _require_tenant()
    return frappe.get_all(
        "Maintenance Request", filters={"tenant": tenant},
        fields=["name", "unit", "category", "priority", "status",
                "description", "creation", "resolution_notes"],
        order_by="creation desc", page_length=50)


@frappe.whitelist(methods=["POST"])
def create_maintenance(category, description, priority="Medium"):
    tenant = _require_tenant()
    lease = _active_lease(tenant)
    if not lease:
        frappe.throw(_("No active lease found; maintenance requests need an active lease."))
    request = frappe.new_doc("Maintenance Request")
    request.unit = lease.unit
    request.tenant = tenant
    request.category = category
    request.priority = priority if priority in ("Low", "Medium", "High", "Emergency") \
        else "Medium"
    request.description = frappe.utils.strip_html(description or "")[:2000]
    request.insert()  # Tenant role has create perm; validate() re-checks unit ownership
    return {"ok": True, "name": request.name}

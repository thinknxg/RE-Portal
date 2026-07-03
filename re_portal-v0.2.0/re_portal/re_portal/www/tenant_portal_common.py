"""Shared context guard for tenant portal pages."""

import frappe
from frappe import _


def require_tenant_context(context):
    """Redirect guests to login; block non-tenant users; return tenant name."""
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=" + frappe.local.request.path
        raise frappe.Redirect
    from re_core.re_core.doctype.tenant.tenant import get_tenant_for_user
    tenant = get_tenant_for_user()
    if not tenant:
        frappe.throw(_("No tenant profile is linked to your account. "
                       "Please contact the leasing office."), frappe.PermissionError)
    context.no_cache = 1
    context.tenant = tenant
    return tenant

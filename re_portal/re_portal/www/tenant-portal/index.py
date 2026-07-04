import frappe
from re_portal.api.tenant import dashboard
from re_portal.utils import money
from re_portal.www.tenant_portal_common import require_tenant_context


def get_context(context):
    require_tenant_context(context)
    context.update(dashboard())
    context.money = money
    context.title = "My Tenancy"
    return context

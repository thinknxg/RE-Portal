from re_portal.api.tenant import installments
from re_portal.utils import money
from re_portal.www.tenant_portal_common import require_tenant_context

BADGE = {"Paid": "success", "Invoiced": "info", "Pending": "secondary",
         "Overdue": "danger", "Bounced": "danger", "Cancelled": "light"}


def get_context(context):
    require_tenant_context(context)
    context.update(installments())
    context.money = money
    context.badge = BADGE
    context.title = "Payments"
    return context

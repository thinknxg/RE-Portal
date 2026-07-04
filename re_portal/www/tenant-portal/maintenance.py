from re_portal.api.tenant import maintenance_list
from re_portal.www.tenant_portal_common import require_tenant_context

BADGE = {"Open": "secondary", "In Progress": "info", "On Hold": "warning",
         "Completed": "success", "Rejected": "danger", "Cancelled": "light"}


def get_context(context):
    require_tenant_context(context)
    context.requests = maintenance_list()
    context.badge = BADGE
    context.categories = ["Plumbing", "Electrical", "AC", "Civil",
                          "Appliances", "Pest Control", "Other"]
    context.title = "Maintenance"
    return context

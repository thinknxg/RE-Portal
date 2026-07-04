import frappe


def get_context(context):
    context.no_cache = 1
    settings = frappe.get_cached_doc("RE Portal Settings")
    context.contact_whatsapp = settings.contact_whatsapp
    context.contact_email = settings.contact_email
    context.title = "Contact Us"
    return context

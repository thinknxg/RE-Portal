import time

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

MIN_FORM_SECONDS = 3  # time-trap: bots submit instantly


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=3600)
def create(full_name, mobile, listing=None, email=None, message=None,
           interest_type="Rent", website=None, form_ts=None):
    """Public inquiry endpoint. `website` is a honeypot field — must stay empty."""
    if website:  # honeypot tripped
        return {"ok": True}
    if form_ts:
        try:
            if time.time() - float(form_ts) < MIN_FORM_SECONDS:
                return {"ok": True}
        except (TypeError, ValueError):
            pass

    full_name = frappe.utils.strip_html(frappe.utils.cstr(full_name))[:140].strip()
    mobile = frappe.utils.cstr(mobile).strip()[:20]
    if not (full_name and mobile):
        frappe.throw(_("Name and mobile number are required."))
    if not frappe.utils.validate_phone_number(mobile, throw=False):
        frappe.throw(_("Please provide a valid mobile number."))
    if email and not frappe.utils.validate_email_address(email):
        email = None
    if listing and not frappe.db.exists("Listing", {"name": listing, "is_published": 1}):
        listing = None

    inquiry = frappe.get_doc({
        "doctype": "Listing Inquiry",
        "full_name": full_name,
        "mobile": mobile,
        "email": email,
        "listing": listing,
        "message": frappe.utils.strip_html(frappe.utils.cstr(message))[:1000],
        "interest_type": interest_type if interest_type in ("Rent", "Buy", "General") else "Rent",
        "source_ip": frappe.local.request_ip,
    })
    inquiry.insert(ignore_permissions=True)
    return {"ok": True, "reference": inquiry.name}

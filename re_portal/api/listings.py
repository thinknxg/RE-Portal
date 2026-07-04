"""Guest-facing listing APIs. All endpoints rate-limited and read-only except inquiries."""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, flt, now_datetime, get_datetime

PUBLIC_FIELDS = [
    "name", "title", "route", "listing_type", "headline_price", "price_period",
    "unit_type", "bedrooms", "bathrooms", "area_sqm", "furnishing",
    "city", "locality", "featured", "published_on",
]


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=120, seconds=3600)
def search(listing_type=None, unit_type=None, city=None, bedrooms=None,
           min_price=None, max_price=None, furnishing=None, page=1, page_size=None):
    settings = frappe.get_cached_doc("RE Portal Settings")
    page_size = min(cint(page_size) or cint(settings.page_size) or 9, 30)
    page = max(cint(page), 1)

    filters = {"is_published": 1}
    if listing_type in ("Rent", "Sale"):
        filters["listing_type"] = listing_type
    if unit_type:
        filters["unit_type"] = unit_type
    if city:
        filters["city"] = city
    if cint(bedrooms):
        filters["bedrooms"] = [">=", cint(bedrooms)]
    if flt(min_price) and flt(max_price):
        filters["headline_price"] = ["between", [flt(min_price), flt(max_price)]]
    elif flt(min_price):
        filters["headline_price"] = [">=", flt(min_price)]
    elif flt(max_price):
        filters["headline_price"] = ["<=", flt(max_price)]
    if furnishing:
        filters["furnishing"] = furnishing

    total = frappe.db.count("Listing", filters)
    rows = frappe.get_all("Listing", filters=filters, fields=PUBLIC_FIELDS,
                          order_by="featured desc, published_on desc",
                          start=(page - 1) * page_size, page_length=page_size)
    for row in rows:
        row["cover"] = frappe.db.get_value(
            "Listing Photo", {"parent": row["name"]}, "image", order_by="idx asc")
    return {"total": total, "page": page, "page_size": page_size, "results": rows,
            "currency": settings.currency_label or "OMR"}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=240, seconds=3600)
def get(route):
    name = frappe.db.get_value("Listing", {"route": route, "is_published": 1})
    if not name:
        frappe.throw(_("Listing not found."), frappe.DoesNotExistError)
    doc = frappe.get_doc("Listing", name)
    out = {k: doc.get(k) for k in PUBLIC_FIELDS}
    out["description"] = doc.description
    out["photos"] = [p.image for p in doc.photos]
    return out


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="inquiry", limit=20, seconds=3600)
def submit_inquiry(full_name, mobile, listing=None, email=None, message=None,
                   website_url=None, form_ts=None):
    """Create a Listing Inquiry. Guards: honeypot (website_url must stay empty),
    time-trap (form rendered >= 3s before submit), mobile sanity check."""
    if website_url:
        return {"ok": True}  # honeypot hit: pretend success, store nothing
    if form_ts:
        try:
            if (now_datetime() - get_datetime(form_ts)).total_seconds() < 3:
                return {"ok": True}
        except Exception:
            pass

    mobile = (mobile or "").strip()
    digits = mobile.lstrip("+").replace(" ", "")
    if not (digits.isdigit() and 7 <= len(digits) <= 15):
        frappe.throw(_("Please enter a valid mobile number."))

    if listing and not frappe.db.exists("Listing", {"name": listing, "is_published": 1}):
        listing = None

    inquiry = frappe.new_doc("Listing Inquiry")
    inquiry.full_name = frappe.utils.strip_html((full_name or "").strip())[:120]
    inquiry.mobile = mobile
    inquiry.email = (email or "").strip() or None
    inquiry.listing = listing
    inquiry.message = frappe.utils.strip_html(message or "")[:1000]
    inquiry.client_meta = f"{frappe.local.request_ip} | {frappe.get_request_header('User-Agent', '')[:180]}"
    inquiry.flags.ignore_permissions = True
    inquiry.insert(ignore_permissions=True)

    _maybe_create_lead(inquiry)
    return {"ok": True, "inquiry": inquiry.name}


def _maybe_create_lead(inquiry):
    """Bridge to Phase 3: create an RE Lead when re_crm is installed."""
    if not frappe.db.exists("DocType", "RE Lead"):
        return
    try:
        lead = frappe.new_doc("RE Lead")
        lead.full_name = inquiry.full_name
        lead.mobile = inquiry.mobile
        lead.email = inquiry.email
        lead.source = "Website"
        if inquiry.unit:
            lead.unit_of_interest = inquiry.unit
        lead.insert(ignore_permissions=True)
        inquiry.db_set("re_lead", lead.name)
        inquiry.db_set("status", "Converted")
    except Exception:
        frappe.log_error(title="re_portal: RE Lead creation failed",
                         message=f"Inquiry {inquiry.name}")

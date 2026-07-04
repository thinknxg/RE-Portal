import frappe
from re_portal.api.listings import search
from re_portal.utils import money


def get_context(context):
    context.no_cache = 1
    args = frappe.form_dict
    result = search(
        listing_type=args.get("listing_type"),
        unit_type=args.get("unit_type"),
        city=args.get("city"),
        bedrooms=args.get("bedrooms"),
        min_price=args.get("min_price"),
        max_price=args.get("max_price"),
        page=args.get("page") or 1,
    )
    context.update(result)
    context.money = money
    context.args = args
    context.total_pages = -(-result["total"] // result["page_size"])
    context.cities = frappe.get_all("Listing", filters={"is_published": 1},
                                    distinct=True, pluck="city")
    settings = frappe.get_cached_doc("RE Portal Settings")
    context.portal_title = settings.portal_title
    context.portal_tagline = settings.portal_tagline
    context.title = "Properties"
    return context

"""
re_portal/sync.py

Bridges Property.is_live -> Listing.is_published.

Rules (confirmed with Sanjay 2026-07-26):
- Property.is_live checked -> every Vacant/Reserved Unit under it gets a
  published Listing, auto-created if one doesn't exist yet.
- Price is pulled from Unit.annual_rent (required — if missing, we skip
  and log rather than publish a listing with no price).
- Property.is_live unchecked, or a unit's status leaves Vacant/Reserved,
  or annual_rent is blank -> listing gets unpublished (never deleted).
- This only ever touches is_published/published_on — it never overwrites
  a manager's photos, description, or manually-edited headline_price on
  an existing Listing.

Copy to: apps/re_portal/re_portal/sync.py
"""

import frappe
from frappe import _
from frappe.utils import nowdate

ELIGIBLE_STATUSES = ("Vacant", "Reserved")


def sync_property_on_update(doc, method=None):
    """doc_events hook: Property on_update -> re-sync all its units when is_live changes."""
    if not doc.has_value_changed("is_live"):
        return
    _sync_property(doc.name, doc.is_live)


def sync_unit_on_update(doc, method=None):
    """doc_events hook: Unit on_update -> re-check this unit's listing eligibility."""
    if not doc.property:
        return
    is_live = frappe.db.get_value("Property", doc.property, "is_live")
    _sync_unit(doc.name, doc.status, is_live)


def _sync_property(property_name, is_live):
    units = frappe.get_all("Unit", filters={"property": property_name}, fields=["name", "status"])
    for u in units:
        _sync_unit(u.name, u.status, is_live)


def _existing_listing(unit_name):
    """Most relevant existing Listing for a unit, if any (published one wins ties)."""
    rows = frappe.get_all(
        "Listing", filters={"unit": unit_name}, fields=["name", "is_published"],
        order_by="is_published desc, modified desc", limit=1,
    )
    return rows[0] if rows else None


def _sync_unit(unit_name, unit_status, property_is_live):
    eligible = bool(property_is_live) and unit_status in ELIGIBLE_STATUSES
    existing = _existing_listing(unit_name)

    if not eligible:
        if existing and existing.is_published:
            frappe.db.set_value("Listing", existing.name, "is_published", 0)
            frappe.get_doc("Listing", existing.name).add_comment(
                "Comment",
                _("Auto-unpublished: property not live or unit not Vacant/Reserved."),
            )
        return

    rent = frappe.db.get_value("Unit", unit_name, "annual_rent")
    if not rent:
        if existing and existing.is_published:
            frappe.db.set_value("Listing", existing.name, "is_published", 0)
            frappe.get_doc("Listing", existing.name).add_comment(
                "Comment", _("Auto-unpublished: Unit.annual_rent is blank."),
            )
        else:
            frappe.log_error(
                title="re_portal: listing auto-publish skipped",
                message=f"Unit {unit_name} is eligible but has no annual_rent set.",
            )
        return

    if existing:
        if not existing.is_published:
            frappe.db.set_value("Listing", existing.name, "is_published", 1)
            frappe.db.set_value("Listing", existing.name, "published_on", nowdate())
        return

    # No listing yet for this unit — auto-create and publish.
    unit_title = frappe.db.get_value("Unit", unit_name, "unit_title") or unit_name
    property_name = frappe.db.get_value("Unit", unit_name, "property")
    city, area = frappe.db.get_value("Property", property_name, ["city", "area"])
    listing = frappe.new_doc("Listing")
    listing.title = unit_title
    listing.unit = unit_name
    listing.listing_type = "Rent"
    listing.headline_price = rent
    listing.price_period = "Per Year"  # matches Unit.annual_rent's period
    listing.city = city
    listing.locality = area
    listing.is_published = 1
    listing.published_on = nowdate()
    listing.flags.ignore_permissions = True

    photos = frappe.get_all(
        "Property Photo",
        filters={"parent": property_name},
        fields=["image", "caption", "idx"],
        order_by="is_cover desc, idx asc",
    )
    for p in photos:
        listing.append("photos", {"image": p.image, "caption": p.caption})

    listing.insert(ignore_permissions=True)

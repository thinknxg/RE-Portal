"""Assembles feed rows from Listings. The credential gate lives here:
no rows are produced unless Listing Feed Settings confirms the brokerage
license, the portal is enabled, and each listing opts in with a permit."""

import frappe
from frappe.utils import get_datetime, get_url


def get_feed_rows(portal):
    """portal: 'property_finder' | 'bayut'. Returns (rows, agent, settings)."""
    settings = frappe.get_cached_doc("Listing Feed Settings")
    flag = "syndicate_property_finder" if portal == "property_finder" else "syndicate_bayut"

    listings = frappe.get_all(
        "Listing",
        filters={"is_published": 1, flag: 1, "permit_number": ["!=", ""]},
        fields=["name", "title", "listing_type", "headline_price", "unit",
                "unit_type", "bedrooms", "bathrooms", "area_sqm", "furnishing",
                "city", "locality", "description", "permit_number",
                "property_ref", "modified"],
        order_by="modified desc")

    rows = []
    for listing in listings:
        photos = [get_url(image) for image in frappe.get_all(
            "Listing Photo", filters={"parent": listing.name},
            order_by="idx asc", pluck="image")]
        geo = frappe.db.get_value("Property", listing.property_ref,
                                  ["latitude", "longitude"], as_dict=True) or {}
        rows.append({
            "reference": listing.name,
            "permit_number": listing.permit_number,
            "listing_type": listing.listing_type,
            "unit_type": listing.unit_type,
            "price": listing.headline_price,
            "cheques": None,
            "city": listing.city,
            "locality": listing.locality,
            "title": listing.title,
            "description": frappe.utils.strip_html(listing.description or ""),
            "area_sqm": listing.area_sqm,
            "bedrooms": listing.bedrooms,
            "bathrooms": listing.bathrooms,
            "furnishing": listing.furnishing,
            "photos": photos,
            "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"),
            "last_update": get_datetime(listing.modified).strftime("%Y-%m-%d %H:%M:%S"),
        })

    if portal == "property_finder":
        agent = {"id": settings.pf_agent_id, "name": settings.pf_agent_name,
                 "email": settings.pf_agent_email, "phone": settings.pf_agent_phone}
    else:
        agent = {"name": settings.bayut_agent_name,
                 "email": settings.bayut_agent_email,
                 "phone": settings.bayut_agent_phone}
    return rows, agent, settings

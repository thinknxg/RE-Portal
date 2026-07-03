"""Pure XML builders for portal syndication feeds.

Both functions take plain dicts so they can be tested without a Frappe site.
Mappings follow each portal's published bulk-upload schema; verify against the
portal's current documentation during brokerage onboarding — schemas change.
"""

from xml.etree.ElementTree import Element, SubElement, tostring

SQM_TO_SQFT = 10.7639

# Property Finder codes
PF_PROPERTY_TYPE = {
    "Studio": "AP", "1BR": "AP", "2BR": "AP", "3BR": "AP", "4BR+": "AP",
    "Penthouse": "PH", "Shop": "SH", "Office": "OF", "Warehouse": "WH",
}
PF_FURNISHED = {"Fully Furnished": "Yes", "Semi Furnished": "Partly",
                "Unfurnished": "No"}

BAYUT_PROPERTY_TYPE = {
    "Studio": "Apartment", "1BR": "Apartment", "2BR": "Apartment",
    "3BR": "Apartment", "4BR+": "Apartment", "Penthouse": "Penthouse",
    "Shop": "Shop", "Office": "Office", "Warehouse": "Warehouse",
}


def _offering_type(listing_type, unit_type):
    residential = unit_type not in ("Shop", "Office", "Warehouse")
    if listing_type == "Rent":
        return "RR" if residential else "CR"
    return "RS" if residential else "CS"


def _sqft(area_sqm):
    return int(round(float(area_sqm or 0) * SQM_TO_SQFT)) or None


def _text(parent, tag, value, **attrs):
    el = SubElement(parent, tag, **attrs)
    el.text = "" if value is None else str(value)
    return el


def build_property_finder_xml(rows, agent, last_update):
    """rows: list of dicts with keys: reference, permit_number, listing_type,
    unit_type, price, cheques, city, locality, title, description, area_sqm,
    bedrooms, bathrooms, furnishing, photos (list of absolute URLs),
    latitude, longitude, last_update."""
    root = Element("list", last_update=last_update, listing_count=str(len(rows)))
    for row in rows:
        prop = SubElement(root, "property",
                          last_update=row.get("last_update") or last_update)
        _text(prop, "reference_number", row["reference"])
        _text(prop, "permit_number", row["permit_number"])
        _text(prop, "offering_type",
              _offering_type(row["listing_type"], row.get("unit_type")))
        _text(prop, "property_type",
              PF_PROPERTY_TYPE.get(row.get("unit_type"), "AP"))
        price = SubElement(prop, "price")
        if row["listing_type"] == "Rent":
            _text(price, "yearly", int(row["price"]))
        else:
            price.text = str(int(row["price"]))
        if row.get("cheques"):
            _text(prop, "cheques", row["cheques"])
        _text(prop, "city", row.get("city") or "")
        _text(prop, "community", row.get("locality") or "")
        _text(prop, "title_en", row.get("title") or "")
        _text(prop, "description_en", row.get("description") or "")
        sqft = _sqft(row.get("area_sqm"))
        if sqft:
            _text(prop, "size", sqft)
        if row.get("bedrooms") is not None:
            _text(prop, "bedroom", row["bedrooms"])
        if row.get("bathrooms") is not None:
            _text(prop, "bathroom", row["bathrooms"])
        furnished = PF_FURNISHED.get(row.get("furnishing"))
        if furnished:
            _text(prop, "furnished", furnished)
        if row.get("latitude") and row.get("longitude"):
            _text(prop, "geopoints", f"{row['longitude']},{row['latitude']}")
        agent_el = SubElement(prop, "agent")
        _text(agent_el, "id", agent.get("id") or "")
        _text(agent_el, "name", agent.get("name") or "")
        _text(agent_el, "email", agent.get("email") or "")
        _text(agent_el, "phone", agent.get("phone") or "")
        if row.get("photos"):
            photo = SubElement(prop, "photo")
            for url in row["photos"]:
                _text(photo, "url", url,
                      last_update=row.get("last_update") or last_update)
    return tostring(root, encoding="unicode", xml_declaration=False)


def build_bayut_xml(rows, agent, last_update):
    root = Element("Properties")
    for row in rows:
        prop = SubElement(root, "Property")
        _text(prop, "Property_Ref_No", row["reference"])
        _text(prop, "Permit_Number", row["permit_number"])
        _text(prop, "Property_purpose",
              "For Rent" if row["listing_type"] == "Rent" else "For Sale")
        _text(prop, "Property_Type",
              BAYUT_PROPERTY_TYPE.get(row.get("unit_type"), "Apartment"))
        _text(prop, "City", row.get("city") or "")
        _text(prop, "Locality", row.get("locality") or "")
        _text(prop, "Property_Title", row.get("title") or "")
        _text(prop, "Property_Description", row.get("description") or "")
        _text(prop, "Price", int(row["price"]))
        if row["listing_type"] == "Rent":
            _text(prop, "Rent_Frequency", "Yearly")
        if row.get("bedrooms") is not None:
            _text(prop, "Bedrooms", row["bedrooms"])
        if row.get("bathrooms") is not None:
            _text(prop, "Bathrooms", row["bathrooms"])
        sqft = _sqft(row.get("area_sqm"))
        if sqft:
            _text(prop, "Property_Size", sqft)
            _text(prop, "Property_Size_Unit", "SQFT")
        _text(prop, "Furnished",
              "Yes" if row.get("furnishing") == "Fully Furnished" else "No")
        if row.get("photos"):
            images = SubElement(prop, "Images")
            for url in row["photos"]:
                _text(images, "Image", url)
        _text(prop, "Agent_Name", agent.get("name") or "")
        _text(prop, "Agent_Email", agent.get("email") or "")
        _text(prop, "Agent_Phone", agent.get("phone") or "")
        _text(prop, "Last_Updated", row.get("last_update") or last_update)
    return tostring(root, encoding="unicode", xml_declaration=False)

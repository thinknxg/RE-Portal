#!/usr/bin/env python3
"""re_portal DocType JSON generator. Controllers are hand-maintained."""
import json, os, re

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODULE = "RE Portal"
DOCTYPE_DIR = os.path.join(APP_ROOT, "re_portal", "re_portal", "doctype")
TS = "2026-01-01 00:00:00.000000"


def scrub(n): return re.sub(r"[\s-]+", "_", n.strip().lower())


def f(fieldname, fieldtype="Data", label=None, **kw):
    d = {"fieldname": fieldname, "fieldtype": fieldtype,
         "label": label or fieldname.replace("_", " ").title()}
    d.update(kw); return d


def sb(fieldname, label="", **kw): return f(fieldname, "Section Break", label, **kw)
def cb(i): return f(f"col_break_{i}", "Column Break", "")


def perm(role, **kw):
    base = {"role": role, "read": 1, "write": 1, "create": 1, "email": 1,
            "print": 1, "report": 1, "export": 1, "share": 1}
    base.update(kw); return base


def dt(name, fields, autoname=None, istable=0, issingle=0, title_field=None,
       perms=None, has_web_view=0, route=None, is_published_field=None):
    doc = {
        "actions": [], "allow_rename": 0, "autoname": autoname or "",
        "creation": TS, "doctype": "DocType", "editable_grid": 1, "engine": "InnoDB",
        "field_order": [x["fieldname"] for x in fields], "fields": fields,
        "has_web_view": has_web_view, "index_web_pages_for_search": has_web_view,
        "is_submittable": 0, "issingle": issingle, "istable": istable,
        "links": [], "modified": TS, "modified_by": "Administrator",
        "module": MODULE, "name": name, "owner": "Administrator",
        "naming_rule": "Expression" if (autoname or "").startswith("format:") else "",
        "permissions": [] if istable else (perms or [
            perm("RE Manager", delete=1), perm("System Manager", delete=1)]),
        "sort_field": "modified", "sort_order": "DESC", "states": [], "track_changes": 1,
    }
    if title_field: doc["title_field"] = title_field
    if has_web_view:
        doc["allow_guest_to_view"] = 1
        doc["is_published_field"] = is_published_field or "is_published"
        if route: doc["route"] = route
    folder = os.path.join(DOCTYPE_DIR, scrub(name))
    os.makedirs(folder, exist_ok=True)
    init = os.path.join(folder, "__init__.py")
    if not os.path.exists(init): open(init, "w").close()
    with open(os.path.join(folder, f"{scrub(name)}.json"), "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True); fh.write("\n")
    print(f"  wrote {name}")


def gen_listing_photo():
    dt("Listing Photo", istable=1, fields=[
        f("image", "Attach Image", reqd=1, in_list_view=1),
        f("caption", "Data", in_list_view=1),
    ])


def gen_listing():
    dt("Listing",
       autoname="format:LST-{#####}",
       title_field="title",
       has_web_view=1, route="property", is_published_field="is_published",
       fields=[
           sb("basic_sb", "Listing"),
           f("title", "Data", reqd=1, in_list_view=1),
           f("route", "Data", read_only=1, unique=1,
             description="Public URL path, e.g. property/sea-view-2br-qurum"),
           f("unit", "Link", options="Unit", reqd=1, in_list_view=1),
           f("listing_type", "Select", options="Rent\nSale", default="Rent",
             reqd=1, in_standard_filter=1),
           cb(1),
           f("is_published", "Check", label="Published", in_list_view=1),
           f("featured", "Check"),
           f("published_on", "Date", read_only=1),
           sb("denorm_sb", "Unit Snapshot (auto)"),
           f("property_ref", "Link", options="Property", label="Property",
             fetch_from="unit.property", read_only=1),
           f("unit_type", "Data", fetch_from="unit.unit_type", read_only=1,
             in_standard_filter=1),
           f("bedrooms", "Int", fetch_from="unit.bedrooms", read_only=1),
           f("bathrooms", "Int", fetch_from="unit.bathrooms", read_only=1),
           cb(2),
           f("area_sqm", "Float", fetch_from="unit.area_sqm", read_only=1),
           f("furnishing", "Data", fetch_from="unit.furnishing", read_only=1),
           f("city", "Data", fetch_from="unit.property.city", read_only=1,
             in_standard_filter=1),
           f("locality", "Data", label="Area", fetch_from="unit.property.area",
             read_only=1),
           sb("price_sb", "Price"),
           f("headline_price", "Currency", reqd=1, in_list_view=1),
           cb(3),
           f("price_period", "Select", options="Per Year\nPer Month\nTotal",
             default="Per Year"),
           sb("content_sb", "Content"),
           f("description", "Text Editor"),
           f("photos", "Table", options="Listing Photo"),
           sb("seo_sb", "SEO", collapsible=1),
           f("meta_title", "Data"),
           f("meta_description", "Small Text"),
           sb("synd_sb", "Portal Syndication", collapsible=1),
           f("syndicate_property_finder", "Check", label="Include in Property Finder Feed"),
           f("syndicate_bayut", "Check", label="Include in Bayut Feed"),
           cb(4),
           f("permit_number", "Data",
             description="RERA / Trakheesi advertising permit — required by both portals "
                         "for UAE listings; the feed skips listings without it"),
       ],
       perms=[perm("RE Manager", delete=1), perm("Property Manager"),
              perm("Leasing Officer"),
              perm("Guest", write=0, create=0, email=0, print=0, report=0,
                   export=0, share=0)])


def gen_listing_inquiry():
    dt("Listing Inquiry",
       autoname="format:INQ-{#####}",
       title_field="full_name",
       fields=[
           sb("who_sb", "Inquirer"),
           f("full_name", "Data", reqd=1, in_list_view=1),
           f("mobile", "Data", options="Phone", reqd=1, in_list_view=1),
           f("email", "Data", options="Email"),
           cb(1),
           f("status", "Select", options="New\nContacted\nConverted\nClosed",
             default="New", in_list_view=1, in_standard_filter=1),
           f("source", "Data", default="Website", read_only=1),
           sb("what_sb", "Interest"),
           f("listing", "Link", options="Listing", in_list_view=1),
           f("unit", "Link", options="Unit", fetch_from="listing.unit", read_only=1),
           cb(2),
           f("re_lead", "Data", label="RE Lead", read_only=1,
             description="Set automatically when re_crm is installed"),
           sb("msg_sb", ""),
           f("message", "Small Text"),
           f("client_meta", "Small Text", read_only=1, hidden=1,
             description="IP / user agent captured for audit"),
       ],
       perms=[perm("RE Manager", delete=1), perm("Property Manager"),
              perm("Leasing Officer")])


def gen_portal_settings():
    dt("Portal Settings", issingle=1, fields=[
        sb("brand_sb", "Branding"),
        f("portal_title", "Data", default="Find Your Next Home"),
        f("portal_tagline", "Data", default="Apartments, villas and offices across Oman"),
        cb(1),
        f("contact_whatsapp", "Data", options="Phone",
          description="Shown on listing pages as the WhatsApp CTA"),
        f("contact_email", "Data", options="Email"),
        sb("display_sb", "Display"),
        f("currency_label", "Data", default="OMR"),
        f("page_size", "Int", default=9, description="Listings per page on /properties"),
        cb(2),
        f("inquiry_hourly_limit", "Int", default=20,
          description="Max guest inquiries per IP per hour"),
    ], perms=[perm("RE Manager"), perm("System Manager")])


def gen_listing_feed_settings():
    dt("Listing Feed Settings", issingle=1, fields=[
        sb("gate_sb", "Brokerage Credential Gate"),
        f("brokerage_confirmed", "Check",
          label="I confirm we hold a valid brokerage license and signed portal "
                "agreements (Property Finder / Bayut) covering these listings",
          description="Both portals only accept feeds from licensed, contracted "
                      "brokerages. The feed endpoints stay disabled until this is "
                      "confirmed."),
        f("feed_token", "Data", reqd=0,
          description="Shared secret appended to the feed URL (?token=...). "
                      "Generate a long random value and register the full URL "
                      "with the portal."),
        sb("pf_sb", "Property Finder"),
        f("pf_enabled", "Check", label="Enable Property Finder Feed"),
        cb(1),
        f("pf_agent_id", "Data", label="PF Agent ID"),
        f("pf_agent_name", "Data", label="Agent Name"),
        f("pf_agent_email", "Data", label="Agent Email", options="Email"),
        f("pf_agent_phone", "Data", label="Agent Phone", options="Phone"),
        sb("bayut_sb", "Bayut"),
        f("bayut_enabled", "Check", label="Enable Bayut Feed"),
        cb(2),
        f("bayut_agent_name", "Data", label="Agent Name"),
        f("bayut_agent_email", "Data", label="Agent Email", options="Email"),
        f("bayut_agent_phone", "Data", label="Agent Phone", options="Phone"),
        sb("notes_sb", "", collapsible=1),
        f("mapping_notes", "Small Text",
          description="Field mappings follow each portal's published bulk-upload "
                      "schema; verify against the portal's current spec during "
                      "onboarding — schemas change without notice."),
    ], perms=[perm("RE Manager"), perm("System Manager")])


if __name__ == "__main__":
    os.makedirs(DOCTYPE_DIR, exist_ok=True)
    init = os.path.join(DOCTYPE_DIR, "__init__.py")
    if not os.path.exists(init): open(init, "w").close()
    for gen in (gen_listing_photo, gen_listing, gen_listing_inquiry,
                gen_portal_settings, gen_listing_feed_settings):
        gen()
    print("Done.")

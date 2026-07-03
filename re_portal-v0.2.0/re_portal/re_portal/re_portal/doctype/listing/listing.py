import frappe
from frappe import _
from frappe.utils import nowdate
from frappe.website.website_generator import WebsiteGenerator


class Listing(WebsiteGenerator):
    website = frappe._dict(
        condition_field="is_published",
        page_title_field="title",
        template="templates/generators/listing.html",
    )

    def validate(self):
        if not self.route:
            self.route = "property/" + self.scrub(self.title)
        if self.is_published:
            status = frappe.db.get_value("Unit", self.unit, "status")
            if status not in ("Vacant", "Reserved"):
                frappe.throw(
                    _("Unit {0} is {1}; only Vacant or Reserved units can be published.")
                    .format(self.unit, status))
            if not self.published_on:
                self.published_on = nowdate()
        other = frappe.db.exists(
            "Listing", {"unit": self.unit, "is_published": 1, "name": ["!=", self.name]})
        if self.is_published and other:
            frappe.throw(_("Unit {0} already has a published listing ({1}).")
                         .format(self.unit, other))

    def get_context(self, context):
        context.no_cache = 1
        context.parents = [{"route": "properties", "label": _("Properties")}]
        settings = frappe.get_cached_doc("Portal Settings")
        context.currency = settings.currency_label or "OMR"
        context.contact_whatsapp = settings.contact_whatsapp
        context.cover = (self.photos[0].image if self.photos else None)
        context.gallery = [p.image for p in self.photos]
        context.amenities = _unit_amenities(self.unit)
        prop = frappe.db.get_value(
            "Property", self.property_ref,
            ["latitude", "longitude", "address_line"], as_dict=True) or frappe._dict()
        context.update(prop)
        context.metatags = {
            "title": self.meta_title or self.title,
            "description": self.meta_description or frappe.utils.strip_html(
                self.description or "")[:150],
        }
        return context


def _unit_amenities(unit):
    prop = frappe.db.get_value("Unit", unit, "property")
    if not prop:
        return []
    return frappe.get_all("Property Amenity", filters={"parent": prop}, pluck="amenity")


def unpublish_unit_listings(doc, method=None):
    """doc_events hook: Lease Contract on_submit -> take the unit off the market."""
    for name in frappe.get_all("Listing",
                               filters={"unit": doc.unit, "is_published": 1},
                               pluck="name"):
        frappe.db.set_value("Listing", name, "is_published", 0)
        frappe.get_doc("Listing", name).add_comment(
            "Comment", _("Auto-unpublished: lease {0} submitted.").format(doc.name))

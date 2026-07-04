app_name = "re_portal"
app_title = "RE Portal"
app_publisher = "Kreatao"
app_description = "GCC Real Estate Platform — Public Listings & Tenant Self-Service"
app_email = "dev@kreatao.com"
app_license = "MIT"

required_apps = ["erpnext", "re_core"]

doc_events = {
    "Lease Contract": {
        "on_submit": "re_portal.re_portal.doctype.listing.listing.unpublish_unit_listings",
    },
}

jinja = {
    "methods": ["re_portal.utils.money"],
}

# Portal menu entries for logged-in tenants
standard_portal_menu_items = [
    {"title": "My Tenancy", "route": "/tenant-portal", "role": "Tenant"},
]

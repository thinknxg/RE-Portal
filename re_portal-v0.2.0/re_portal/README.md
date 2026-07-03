# RE Portal — Public Listings & Tenant Self-Service (Phase 2)

Rides on `re_core` (Phase 1). Requires it to be installed first.

## Included
- **Listing** (WebsiteGenerator): marketing wrapper over a `re_core` Unit; publishes at
  `/property/<route>`; only Vacant/Reserved units publishable; auto-unpublished when a
  lease on the unit is submitted (doc_events hook)
- **Listing Inquiry**: guest submissions with honeypot + time-trap anti-spam and rate
  limiting; auto-creates an RE Lead when `re_crm` (Phase 3) is installed
- **Public pages**: `/properties` (filterable, paginated browse) and `/contact`;
  listing detail rendered from `templates/generators/listing.html`
- **Tenant portal** (role: Tenant, provisioned by re_core): `/tenant-portal` dashboard,
  `/tenant-portal/lease`, `/tenant-portal/payments`, `/tenant-portal/maintenance`
- **Guest API**: `re_portal.api.listings.search`, `.get`, `.submit_inquiry`
- **Tenant API**: `re_portal.api.tenant.*` — all identity resolved server-side from the
  session; the client never passes tenant IDs
- **Portal Settings** (Single): branding, contact WhatsApp, currency label

- **Portal syndication feeds** (Property Finder / Bayut): token-gated XML endpoints
  behind an explicit brokerage-credential gate

## Portal Syndication (scope boundary)
Property Finder and Bayut only accept listings from licensed, contracted brokerages —
this app therefore exposes *feeds a credentialed brokerage can register*, not a direct
API push. The gate is enforced in code: both endpoints return 403 unless
**Listing Feed Settings** has the brokerage confirmation checked, the specific portal
enabled, and a matching `?token=` (constant-time compared). Listings are only included
when individually opted in (`Include in ... Feed`) **and** carrying a permit number
(RERA/Trakheesi). Field mappings follow each portal's published bulk-upload schema —
verify against the portal's current spec during onboarding, as schemas change.

Feed URLs to register with the portal:
```
/api/method/re_portal.api.feeds.property_finder?token=<feed_token>
/api/method/re_portal.api.feeds.bayut?token=<feed_token>
```

## Install
```bash
bench get-app /path/to/re_portal
bench --site yoursite.local install-app re_portal
bench --site yoursite.local migrate && bench build
```

## Regenerating DocType JSONs
```bash
python3 scripts/generate_doctypes.py
```

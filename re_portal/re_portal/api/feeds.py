"""Token-gated XML feed endpoints for portal syndication.

Register with the portal as e.g.:
  https://yoursite/api/method/re_portal.api.feeds.property_finder?token=<feed_token>
  https://yoursite/api/method/re_portal.api.feeds.bayut?token=<feed_token>

The endpoints return 403 unless: brokerage confirmation is checked, the specific
portal is enabled, a feed token is configured, and the presented token matches
(constant-time comparison)."""

import hmac

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime
from werkzeug.wrappers import Response

from re_portal.feeds.builders import build_bayut_xml, build_property_finder_xml
from re_portal.feeds.data import get_feed_rows


def _guard(settings, portal_enabled, token):
    if not settings.brokerage_confirmed:
        frappe.throw(_("Feed disabled: brokerage credentials not confirmed in "
                       "Listing Feed Settings."), frappe.PermissionError)
    if not portal_enabled:
        frappe.throw(_("This portal feed is not enabled."), frappe.PermissionError)
    expected = (settings.feed_token or "").strip()
    if not expected or not hmac.compare_digest(expected, (token or "").strip()):
        frappe.throw(_("Invalid feed token."), frappe.PermissionError)


def _xml_response(xml):
    return Response('<?xml version="1.0" encoding="UTF-8"?>\n' + xml,
                    mimetype="application/xml")


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=3600)
def property_finder(token=None):
    settings = frappe.get_cached_doc("Listing Feed Settings")
    _guard(settings, settings.pf_enabled, token)
    rows, agent, settings = get_feed_rows("property_finder")
    stamp = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
    return _xml_response(build_property_finder_xml(rows, agent, stamp))


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=3600)
def bayut(token=None):
    settings = frappe.get_cached_doc("Listing Feed Settings")
    _guard(settings, settings.bayut_enabled, token)
    rows, agent, settings = get_feed_rows("bayut")
    stamp = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
    return _xml_response(build_bayut_xml(rows, agent, stamp))

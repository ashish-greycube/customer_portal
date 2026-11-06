# Copyright (c) 2026, Greycube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.sessions import get_csrf_token

no_cache = 1


def get_context(context):
	frappe.db.commit()  # get_csrf_token may write the session
	context.csrf_token = get_csrf_token() if frappe.session.user != "Guest" else ""
	context.site_name = frappe.local.site
	return context

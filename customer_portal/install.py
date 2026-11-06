# Copyright (c) 2026, Greycube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Categories offered when a customer raises a query
QUERY_CATEGORIES = ["Delivery", "Documents", "Quantity or quality", "Commercial", "Other"]


def after_install():
	setup()


def after_migrate():
	setup()


def setup():
	create_custom_fields(
		{
			"Issue": [
				{
					"fieldname": "custom_portal_reference_doctype",
					"label": "Portal Reference Type",
					"fieldtype": "Link",
					"options": "DocType",
					"insert_after": "issue_type",
					"read_only": 1,
				},
				{
					"fieldname": "custom_portal_reference_name",
					"label": "Portal Reference",
					"fieldtype": "Dynamic Link",
					"options": "custom_portal_reference_doctype",
					"insert_after": "custom_portal_reference_doctype",
					"read_only": 1,
				},
			]
		},
		update=True,
	)
	for category in QUERY_CATEGORIES:
		if not frappe.db.exists("Issue Type", category):
			frappe.new_doc("Issue Type").insert(ignore_permissions=True, set_name=category)

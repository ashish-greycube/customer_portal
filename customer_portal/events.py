# Copyright (c) 2026, Greycube Technologies and contributors
# For license information, please see license.txt

"""Doc events that keep the customer portal in step with ERPNext.

Every handler is best effort: a failure is logged and never blocks the
Refteck user who is saving the document.
"""

import functools

import frappe
from frappe import _
from frappe.utils import strip_html_tags


def safe(fn):
	@functools.wraps(fn)
	def wrapper(doc, method=None):
		try:
			fn(doc)
		except Exception:
			frappe.log_error(title=f"Customer portal: {fn.__name__} failed for {doc.doctype} {doc.name}")

	return wrapper


def portal_users(customer, contact=None):
	"""Website users to notify: the document's contact and the customer's main contact."""
	if not customer:
		return []
	primary = frappe.db.get_value("Customer", customer, "customer_primary_contact")
	users = set()
	for c in {contact, primary} - {None, ""}:
		user = frappe.db.get_value("Contact", c, "user")
		if user:
			users.add(user)
	# Refteck staff are sometimes linked as customer contacts; only notify customer logins
	return [u for u in users if frappe.db.exists("User", {"name": u, "enabled": 1, "user_type": "Website User"})]


def notify(users, doc, subject, body):
	for user in users:
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"type": "Alert",
				"document_type": doc.doctype,
				"document_name": doc.name,
				"subject": subject,
				"email_content": body,
				"from_user": frappe.session.user,
			}
		).insert(ignore_permissions=True)


def first_item(doc):
	items = doc.get("items") or []
	if not items:
		return ""
	return items[0].item_name + (f" + {len(items) - 1} more" if len(items) > 1 else "")


@safe
def quotation_on_submit(doc):
	if doc.quotation_to != "Customer":
		return
	valid = f", valid till {frappe.format(doc.valid_till, 'Date')}" if doc.valid_till else ""
	notify(
		portal_users(doc.party_name, doc.contact_person),
		doc,
		_("Quotation {0} received").format(doc.name),
		f"{first_item(doc)}{valid}.",
	)


def _po_submission_for(so):
	quotations = {i.prevdoc_docname for i in so.items if i.prevdoc_docname}
	if not quotations:
		return None
	return frappe.db.get_value(
		"Customer PO Submission",
		{"quotation": ["in", list(quotations)], "status": "Pending confirmation"},
		["name", "customer_po_no", "po_date", "contact"],
		as_dict=True,
		order_by="creation desc",
	)


@safe
def sales_order_before_validate(doc):
	"""Carry the customer's PO number into a new Sales Order made from the quotation."""
	if doc.docstatus != 0 or doc.po_no:
		return
	pos = _po_submission_for(doc)
	if pos:
		doc.po_no = pos.customer_po_no
		doc.po_date = pos.po_date


@safe
def sales_order_on_submit(doc):
	pos = _po_submission_for(doc)
	if pos:
		frappe.db.set_value("Customer PO Submission", pos.name, {"status": "Confirmed", "sales_order": doc.name})
	notify(
		portal_users(doc.customer, doc.contact_person or (pos and pos.contact)),
		doc,
		_("PO confirmed, {0} created").format(doc.name)
		if pos
		else _("Sales order {0} confirmed").format(doc.name),
		_("{0} is now in processing.").format(first_item(doc)),
	)


@safe
def sales_order_on_cancel(doc):
	for name in frappe.get_all("Customer PO Submission", {"sales_order": doc.name}, pluck="name"):
		frappe.db.set_value("Customer PO Submission", name, {"status": "Pending confirmation", "sales_order": None})


@safe
def sales_invoice_after_insert(doc):
	if doc.is_return:
		return
	notify(
		portal_users(doc.customer, doc.contact_person),
		doc,
		_("{0} ready for dispatch").format(doc.name),
		_("{0} is packed and awaiting pickup.").format(first_item(doc)),
	)


@safe
def sales_invoice_on_submit(doc):
	if doc.is_return:
		return
	carrier = (doc.get("transporter_name") or doc.get("custom_mode_of_shipment") or "").strip()
	awb = (doc.get("lr_no") or "").strip()
	via = f" via {carrier}" if carrier else ""
	awb = f", AWB {awb}" if awb else ""
	notify(
		portal_users(doc.customer, doc.contact_person),
		doc,
		_("{0} dispatched").format(doc.name),
		f"{first_item(doc)} shipped{via}{awb}.",
	)


@safe
def communication_after_insert(doc):
	"""A Refteck reply on a portal query: mark it Replied and tell the customer."""
	if doc.reference_doctype != "Issue" or doc.sent_or_received != "Sent" or doc.communication_type != "Communication":
		return
	issue = frappe.db.get_value(
		"Issue", doc.reference_name, ["name", "customer", "contact", "status", "via_customer_portal"], as_dict=True
	)
	if not issue or not issue.via_customer_portal:
		return
	if issue.status == "Open":
		frappe.db.set_value("Issue", issue.name, "status", "Replied")
	issue_doc = frappe._dict(doctype="Issue", name=issue.name)
	text = strip_html_tags(doc.content or "").strip()
	notify(
		portal_users(issue.customer, issue.contact),
		issue_doc,
		_("Refteck replied on {0}").format(issue.name),
		text[:140] + ("…" if len(text) > 140 else ""),
	)

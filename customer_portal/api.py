# Copyright (c) 2026, Greycube Technologies and contributors
# For license information, please see license.txt

"""Endpoints for the Refteck customer portal SPA (/customer-portal).

A portal user is a Website User whose Contact is linked to a Customer. The
customer's primary contact is the customer admin and sees every record of the
customer. Other contacts see the records where they are the contact person.
"""

from collections import defaultdict
from html import unescape

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate, strip_html_tags
from frappe.utils.data import escape_html

STEPS = 6

# Portal slug → ERPNext doctype
DOCTYPES = {
	"opportunity": "Opportunity",
	"quotation": "Quotation",
	"po-submission": "Customer PO Submission",
	"sales-order": "Sales Order",
	"sales-invoice": "Sales Invoice",
}
SLUGS = {v: k for k, v in DOCTYPES.items()}

# Print format used for "Download PDF". Missing or disabled formats fall back to Standard.
PRINT_FORMATS = {
	"Quotation": "Client Offer Quotation",
	"Sales Order": "PO Acceptance",
	"Sales Invoice": "Refteck-SI",
}

# Issue status → portal query status
QUERY_STATUS = {
	"Open": "Awaiting Refteck",
	"On Hold": "Awaiting Refteck",
	"Replied": "Awaiting you",
	"Resolved": "Resolved",
	"Closed": "Resolved",
}

ROW_LIMIT = 500

# Refteck users with these roles open the portal in staff view: they pick any
# customer and see it the way that customer's admin does, read-only.
STAFF_ROLES = ("System Manager", "Sales Manager")
STAFF_CUSTOMER_KEY = "customer_portal_customer"


# ---------------------------------------------------------------- session


def is_staff(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	if frappe.db.get_value("User", user, "user_type") != "System User":
		return False
	return bool(set(frappe.get_roles(user)) & set(STAFF_ROLES))


def _staff_customer(user):
	customer = frappe.defaults.get_user_default(STAFF_CUSTOMER_KEY, user)
	if customer and frappe.db.exists("Customer", customer):
		return customer
	# Default to the customer with the latest sales order
	return frappe.db.get_value("Sales Order", {"docstatus": 1}, "customer", order_by="creation desc") or frappe.db.get_value(
		"Customer", {"disabled": 0}, "name", order_by="customer_name asc"
	)


def get_portal_context(user=None):
	"""Customer, contacts and admin flag of the user, or None if not a portal user."""
	user = user or frappe.session.user
	if user == "Guest":
		return None

	if not getattr(frappe.local, "customer_portal_ctx", None):
		frappe.local.customer_portal_ctx = {}
	cache = frappe.local.customer_portal_ctx
	if user in cache:
		return cache[user]

	if is_staff(user):
		customer = _staff_customer(user)
		ctx = (
			frappe._dict(user=user, customer=customer, contacts=[], contact=None, is_admin=True, staff=True)
			if customer
			else None
		)
		cache[user] = ctx
		return ctx

	ctx = None
	contacts = frappe.get_all("Contact", filters={"user": user}, pluck="name")
	links = (
		frappe.get_all(
			"Dynamic Link",
			filters={"parenttype": "Contact", "parent": ["in", contacts], "link_doctype": "Customer"},
			fields=["parent", "link_name"],
		)
		if contacts
		else []
	)
	if links:
		customer = links[0].link_name
		my_contacts = [l.parent for l in links if l.link_name == customer]
	else:
		customer = frappe.db.get_value("Portal User", {"parenttype": "Customer", "user": user}, "parent")
		my_contacts = []

	if customer:
		primary = frappe.db.get_value("Customer", customer, "customer_primary_contact")
		ctx = frappe._dict(
			user=user,
			customer=customer,
			contacts=my_contacts,
			contact=my_contacts[0] if my_contacts else None,
			# A portal user listed on the customer without a contact is a company level user
			is_admin=(primary in my_contacts) if my_contacts else True,
			staff=False,
		)

	cache[user] = ctx
	return ctx


def _one_line(html):
	text = strip_html_tags((html or "").replace("<br>", "\n").replace("<br/>", "\n"))
	parts = [p.strip() for line in text.splitlines() for p in line.split(",")]
	return ", ".join(p for p in parts if p)


def _ctx(write=False):
	ctx = get_portal_context()
	if not ctx:
		frappe.throw(_("Your login is not linked to a customer. Please contact Refteck."), frappe.PermissionError)
	if write and ctx.staff:
		frappe.throw(_("Staff view is read-only. Make this change from the desk."), frappe.PermissionError)
	return ctx


@frappe.whitelist()
def get_customers():
	"""Customers a staff user can switch between."""
	if not is_staff():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return [
		{"label": c.customer_name if c.customer_name == c.name else f"{c.customer_name} ({c.name})", "value": c.name}
		for c in frappe.get_all(
			"Customer",
			filters={"disabled": 0},
			fields=["name", "customer_name"],
			order_by="customer_name asc",
			limit_page_length=0,
		)
	]


@frappe.whitelist()
def set_customer(customer: str):
	if not is_staff():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer {0} not found").format(customer))
	frappe.defaults.set_user_default(STAFF_CUSTOMER_KEY, customer)
	return customer


def _contact_names(customer):
	rows = frappe.db.sql(
		"""select c.name, c.full_name, c.first_name, c.last_name, c.email_id, c.designation, c.user
		from `tabContact` c join `tabDynamic Link` dl on dl.parent = c.name and dl.parenttype = 'Contact'
		where dl.link_doctype = 'Customer' and dl.link_name = %s
		order by c.full_name""",
		customer,
		as_dict=True,
	)
	for r in rows:
		r.label = r.full_name or " ".join(filter(None, [r.first_name, r.last_name])) or r.name
	return rows


@frappe.whitelist(allow_guest=True)
def get_session():
	if frappe.session.user == "Guest":
		return {"user": None}

	ctx = get_portal_context()
	user = frappe.get_cached_doc("User", frappe.session.user)
	if not ctx:
		return {"user": {"email": user.name, "name": user.full_name}, "customer": None}

	customer = frappe.get_cached_doc("Customer", ctx.customer)
	contacts = _contact_names(ctx.customer)
	primary = customer.customer_primary_contact
	me = next((c for c in contacts if c.name == ctx.contact), None)

	manager = None
	if customer.account_manager:
		am = frappe.get_cached_doc("User", customer.account_manager)
		manager = {
			"name": am.full_name,
			"title": frappe.db.get_value("Employee", {"user_id": am.name}, "designation") or "Account manager",
			"email": am.email,
			"phone": am.mobile_no or am.phone or "",
			"location": am.location or "",
		}

	return {
		"user": {
			"id": ctx.contact or user.name,
			"name": (me and me.label) or user.full_name,
			"role": "Refteck staff" if ctx.staff else (me and me.designation) or "",
			"email": user.email,
			"isMainContact": ctx.is_admin,
		},
		"staff": ctx.staff,
		"customer": {
			"id": customer.name,
			"name": customer.customer_name,
			"address": _one_line(customer.primary_address),
			"currency": customer.default_currency or "",
		},
		"accountManager": manager,
		"contacts": [
			{
				"id": c.name,
				"name": c.label,
				"role": c.designation or "",
				"email": c.email_id or "",
				"isMainContact": c.name == primary,
			}
			for c in contacts
		],
		"company": _company_line(),
		"unread": unread_count(),
	}


def _company_line():
	company = frappe.db.get_default("Company")
	if not company:
		return {"name": "Refteck", "line": ""}
	address = frappe.db.sql(
		"""select a.city, a.country, a.email_id from `tabAddress` a
		join `tabDynamic Link` dl on dl.parent = a.name and dl.parenttype = 'Address'
		where dl.link_doctype = 'Company' and dl.link_name = %s and a.disabled = 0
		order by a.is_primary_address desc limit 1""",
		company,
		as_dict=True,
	)
	parts = [company]
	if address:
		parts += [address[0].city, address[0].email_id]
	return {"name": company, "line": " · ".join(filter(None, parts))}


# ---------------------------------------------------------------- workflow chain


class Chain:
	"""Opportunity → Quotation → PO submission → Sales Order → Sales Invoice links of one customer."""

	def __init__(self, customer):
		self.quotes = {
			q.name: q
			for q in frappe.get_all(
				"Quotation",
				filters={"quotation_to": "Customer", "party_name": customer, "docstatus": 1},
				fields=["name", "opportunity", "valid_till", "status"],
			)
		}
		self.pos = frappe.get_all(
			"Customer PO Submission",
			filters={"customer": customer, "status": ["!=", "Returned"]},
			fields=["name", "quotation", "status"],
			order_by="creation desc",
		)
		so_rows = frappe.db.sql(
			"""select distinct soi.parent, soi.prevdoc_docname from `tabSales Order Item` soi
			join `tabSales Order` so on so.name = soi.parent
			where so.customer = %s and so.docstatus = 1""",
			customer,
			as_dict=True,
		)
		si_rows = frappe.db.sql(
			"""select distinct sii.parent, sii.sales_order, si.docstatus from `tabSales Invoice Item` sii
			join `tabSales Invoice` si on si.name = sii.parent
			where si.customer = %s and si.docstatus < 2 and si.is_return = 0""",
			customer,
			as_dict=True,
		)

		self.opp_quotes = defaultdict(list)
		for q in self.quotes.values():
			if q.opportunity:
				self.opp_quotes[q.opportunity].append(q.name)
		self.quote_pos = defaultdict(list)
		for p in self.pos:
			self.quote_pos[p.quotation].append(p.name)
		self.quote_sos, self.so_quotes = defaultdict(list), defaultdict(list)
		for r in so_rows:
			if r.prevdoc_docname:
				self.quote_sos[r.prevdoc_docname].append(r.parent)
				self.so_quotes[r.parent].append(r.prevdoc_docname)
		self.so_sis, self.si_sos, self.si_status = defaultdict(list), defaultdict(list), {}
		for r in si_rows:
			self.si_status[r.parent] = 6 if r.docstatus == 1 else 5
			if r.sales_order:
				self.so_sis[r.sales_order].append(r.parent)
				self.si_sos[r.parent].append(r.sales_order)

	def si_step(self, si):
		return self.si_status.get(si, 5)

	def so_step(self, so):
		return max([4] + [self.si_step(si) for si in self.so_sis.get(so, [])])

	def quote_step(self, q):
		step = 3 if self.quote_pos.get(q) else 2
		return max([step] + [self.so_step(so) for so in self.quote_sos.get(q, [])])

	def opp_step(self, opp):
		return max([1] + [self.quote_step(q) for q in self.opp_quotes.get(opp, [])])

	def links(self, doctype, name):
		"""Document name behind each of the six steps, or None when not reached."""
		opp = quote = pos = so = si_draft = si_done = None
		if doctype == "Sales Invoice":
			so = _first(self.si_sos.get(name))
		elif doctype == "Sales Order":
			so = name
		if so:
			quote = _first(self.so_quotes.get(so))
		if doctype == "Quotation":
			quote = name
		if doctype == "Customer PO Submission":
			pos = name
			quote = frappe.db.get_value("Customer PO Submission", name, "quotation")
		if quote:
			opp = self.quotes.get(quote, {}).get("opportunity")
			pos = pos or _first(self.quote_pos.get(quote))
			so = so or _first(self.quote_sos.get(quote))
		if doctype == "Opportunity":
			opp = name
			quote = _best(self.opp_quotes.get(name), self.quote_step)
			if quote:
				pos = _first(self.quote_pos.get(quote))
				so = _first(self.quote_sos.get(quote))
		if so:
			sis = self.so_sis.get(so, [])
			if doctype == "Sales Invoice":
				sis = [name]
			si_done = next((s for s in sis if self.si_step(s) == 6), None)
			si_draft = next((s for s in sis if self.si_step(s) == 5), None) or si_done

		refs = [
			("opportunity", opp),
			("quotation", quote),
			("po-submission", pos),
			("sales-order", so),
			("sales-invoice", si_draft),
			("sales-invoice", si_done),
		]
		return [f"/print/{slug}/{docname}" if docname else None for slug, docname in refs]


def _first(xs):
	return xs[0] if xs else None


def _best(xs, key):
	return max(xs, key=key) if xs else None


# ---------------------------------------------------------------- list rows


def _first_items(child_doctype, parents):
	"""Short title from the first item of each parent: 'Item name + 2 more'."""
	if not parents:
		return {}
	rows = frappe.get_all(
		child_doctype,
		filters={"parent": ["in", list(parents)]},
		fields=["parent", "item_name", "idx"],
		order_by="idx asc",
		limit_page_length=0,
	)
	first, count = {}, defaultdict(int)
	for r in rows:
		count[r.parent] += 1
		first.setdefault(r.parent, r.item_name)
	return {p: first[p] + (f" + {count[p] - 1} more" if count[p] > 1 else "") for p in first}


def _plants(addresses, customer_name):
	addresses = {a for a in addresses if a}
	if not addresses:
		return {}
	out = {}
	for a in frappe.get_all(
		"Address", filters={"name": ["in", list(addresses)]}, fields=["name", "address_title", "city"]
	):
		title = a.address_title if a.address_title and a.address_title != customer_name else None
		out[a.name] = title or a.city or ""
	return out


def _visibility(ctx, field="contact_person"):
	return {} if ctx.is_admin else {field: ["in", ctx.contacts or ["__none__"]]}


def get_rows(slug, ctx, name=None, light=False, limit=ROW_LIMIT):
	doctype = DOCTYPES.get(slug)
	if not doctype:
		frappe.throw(_("Unknown document type"))

	chain = getattr(frappe.local, "customer_portal_chain", None)
	if not chain or chain[0] != ctx.customer:
		frappe.local.customer_portal_chain = (ctx.customer, Chain(ctx.customer))
	chain = frappe.local.customer_portal_chain[1]

	extra = {"name": name} if name else {}
	limit = 1 if name else (0 if light else limit)
	customer_name = frappe.db.get_value("Customer", ctx.customer, "customer_name")
	contacts = {c.name: c.label for c in _contact_names(ctx.customer)}
	today = getdate(nowdate())
	rows = []

	if slug == "opportunity":
		meta = frappe.get_meta("Opportunity")
		ref = "custom_customer_opportunity_reference"
		fields = ["name", "transaction_date", "expected_closing", "contact_person", "status", "customer_address"]
		if meta.has_field(ref):
			fields.append(ref)
		docs = frappe.get_all(
			"Opportunity",
			filters={"opportunity_from": "Customer", "party_name": ctx.customer, "docstatus": ["<", 2], **_visibility(ctx), **extra},
			fields=fields,
			order_by="transaction_date desc, creation desc",
			limit_page_length=limit,
		)
		titles = {} if light else _first_items("Opportunity Item", [d.name for d in docs])
		plants = {} if light else _plants([d.customer_address for d in docs], customer_name)
		for d in docs:
			step = chain.opp_step(d.name)
			status = "Open" if step == 1 else "Quotation" if step < 4 else "Converted"
			if step < 4 and d.status in ("Lost", "Closed"):
				status = d.status
			rows.append(
				{
					"name": d.name,
					"title": d.get(ref) or titles.get(d.name) or d.name,
					"owner": d.contact_person,
					"ownerName": contacts.get(d.contact_person, ""),
					"date": str(d.transaction_date or ""),
					"requiredBy": str(d.expected_closing or ""),
					"plant": plants.get(d.customer_address, ""),
					"opportunity": d.name,
					"step": step,
					"status": status,
				}
			)

	elif slug == "quotation":
		docs = frappe.get_all(
			"Quotation",
			filters={"quotation_to": "Customer", "party_name": ctx.customer, "docstatus": 1, **_visibility(ctx), **extra},
			fields=[
				"name", "transaction_date", "valid_till", "grand_total", "currency", "contact_person",
				"status", "opportunity", "shipping_address_name", "customer_address",
			],
			order_by="transaction_date desc, creation desc",
			limit_page_length=limit,
		)
		titles = {} if light else _first_items("Quotation Item", [d.name for d in docs])
		plants = {} if light else _plants([d.shipping_address_name or d.customer_address for d in docs], customer_name)
		for d in docs:
			step = chain.quote_step(d.name)
			status = "Open" if step == 2 else "PO submitted" if step == 3 else "Ordered"
			if step == 2 and (d.status in ("Expired", "Lost") or (d.valid_till and getdate(d.valid_till) < today)):
				status = "Lost" if d.status == "Lost" else "Expired"
			rows.append(
				{
					"name": d.name,
					"title": titles.get(d.name) or d.name,
					"owner": d.contact_person,
					"ownerName": contacts.get(d.contact_person, ""),
					"date": str(d.transaction_date or ""),
					"validTill": str(d.valid_till or ""),
					"amount": flt(d.grand_total),
					"currency": d.currency,
					"plant": plants.get(d.shipping_address_name or d.customer_address, ""),
					"opportunity": d.opportunity,
					"step": step,
					"status": status,
				}
			)

	elif slug == "po-submission":
		docs = frappe.get_all(
			"Customer PO Submission",
			filters={"customer": ctx.customer, **_visibility(ctx, "contact"), **extra},
			fields=[
				"name", "customer_po_no", "po_date", "quotation", "opportunity", "title", "grand_total",
				"currency", "contact", "status", "po_file", "remarks", "sales_order",
			],
			order_by="po_date desc, creation desc",
			limit_page_length=limit,
		)
		for d in docs:
			step = 3 if d.status != "Confirmed" else max(4, chain.quote_step(d.quotation))
			rows.append(
				{
					"name": d.name,
					"customerPo": d.customer_po_no,
					"title": d.title or d.quotation,
					"quotation": d.quotation,
					"opportunity": d.opportunity,
					"owner": d.contact,
					"uploadedBy": d.contact,
					"uploadedByName": contacts.get(d.contact, ""),
					"date": str(d.po_date or ""),
					"amount": flt(d.grand_total),
					"currency": d.currency,
					"file": d.po_file,
					"remarks": d.remarks or "",
					"plant": "",
					"step": step,
					"status": d.status,
				}
			)

	elif slug == "sales-order":
		docs = frappe.get_all(
			"Sales Order",
			filters={"customer": ctx.customer, "docstatus": 1, **_visibility(ctx), **extra},
			fields=[
				"name", "transaction_date", "delivery_date", "grand_total", "currency", "po_no",
				"contact_person", "shipping_address_name",
			],
			order_by="transaction_date desc, creation desc",
			limit_page_length=limit,
		)
		titles = {} if light else _first_items("Sales Order Item", [d.name for d in docs])
		plants = {} if light else _plants([d.shipping_address_name for d in docs], customer_name)
		for d in docs:
			step = chain.so_step(d.name)
			rows.append(
				{
					"name": d.name,
					"title": titles.get(d.name) or d.name,
					"owner": d.contact_person,
					"ownerName": contacts.get(d.contact_person, ""),
					"customerPo": d.po_no or "",
					"date": str(d.transaction_date or ""),
					"deliveryDate": str(d.delivery_date or ""),
					"amount": flt(d.grand_total),
					"currency": d.currency,
					"plant": plants.get(d.shipping_address_name, ""),
					"quotation": _first(chain.so_quotes.get(d.name)),
					"step": step,
					"status": "Processing" if step == 4 else "Ready for dispatch" if step == 5 else "Dispatched",
				}
			)

	elif slug == "sales-invoice":
		meta = frappe.get_meta("Sales Invoice")
		fields = ["name", "posting_date", "grand_total", "currency", "po_no", "contact_person", "docstatus", "shipping_address_name"]
		fields += [f for f in ("transporter_name", "lr_no", "custom_mode_of_shipment") if meta.has_field(f)]
		docs = frappe.get_all(
			"Sales Invoice",
			filters={"customer": ctx.customer, "docstatus": ["<", 2], "is_return": 0, **_visibility(ctx), **extra},
			fields=fields,
			order_by="posting_date desc, creation desc",
			limit_page_length=limit,
		)
		titles = {} if light else _first_items("Sales Invoice Item", [d.name for d in docs])
		plants = {} if light else _plants([d.shipping_address_name for d in docs], customer_name)
		for d in docs:
			carrier = (d.get("transporter_name") or d.get("custom_mode_of_shipment") or "").strip()
			awb = (d.get("lr_no") or "").strip()
			dispatched = d.docstatus == 1
			rows.append(
				{
					"name": d.name,
					"title": titles.get(d.name) or d.name,
					"owner": d.contact_person,
					"ownerName": contacts.get(d.contact_person, ""),
					"customerPo": d.po_no or "",
					"salesOrder": _first(chain.si_sos.get(d.name)) or "",
					"date": str(d.posting_date or ""),
					"amount": flt(d.grand_total),
					"currency": d.currency,
					"carrier": carrier,
					"awb": awb,
					"dispatch": " · ".join(filter(None, [carrier, awb])) or ("Awaiting AWB" if dispatched else "Awaiting pickup"),
					"plant": plants.get(d.shipping_address_name, ""),
					"step": 6 if dispatched else 5,
					"docstatus": "Submitted" if dispatched else "Draft",
					"status": "Dispatched" if dispatched else "Ready for dispatch",
				}
			)

	return rows


@frappe.whitelist()
def get_records(doctype: str):
	return get_rows(doctype, _ctx())


@frappe.whitelist()
def get_dashboard():
	ctx = _ctx()

	def count(slug, status):
		return sum(1 for r in get_rows(slug, ctx, light=True) if r["status"] == status)

	opps = get_rows("opportunity", ctx, light=True)
	queries = _issues(ctx)
	return {
		"counts": {
			"openOpportunities": sum(1 for r in opps if r["status"] == "Open"),
			"openQuotations": count("quotation", "Open"),
			"pendingPOs": count("po-submission", "Pending confirmation"),
			"processingOrders": count("sales-order", "Processing"),
			"readyForDispatch": count("sales-invoice", "Ready for dispatch"),
			"dispatched": count("sales-invoice", "Dispatched"),
			"openQueries": sum(1 for q in queries if QUERY_STATUS.get(q.status) != "Resolved"),
			"queriesAwaitingYou": sum(1 for q in queries if q.status == "Replied"),
			"unread": unread_count(),
		},
		"pipeline": [sum(1 for r in opps if r["step"] == n) for n in range(1, STEPS + 1)],
	}


# ---------------------------------------------------------------- one document


def _get_visible(slug, name, ctx):
	rows = get_rows(slug, ctx, name=name)
	if not rows:
		frappe.throw(_("Document not available"), frappe.PermissionError)
	return rows[0]


@frappe.whitelist()
def get_document(doctype: str, name: str):
	ctx = _ctx()
	row = _get_visible(doctype, name, ctx)
	erp_doctype = DOCTYPES[doctype]
	chain = frappe.local.customer_portal_chain[1]

	items, totals = [], None
	source = None
	if doctype == "po-submission":
		source = frappe.get_doc("Quotation", row["quotation"])
	else:
		source = frappe.get_doc(erp_doctype, name)

	for it in source.get("items") or []:
		items.append(
			{
				"idx": it.idx,
				"code": it.item_code or "",
				"description": it.item_name or strip_html_tags(it.description or ""),
				"uom": it.get("uom") or "",
				"qty": flt(it.qty),
				"rate": flt(it.get("rate")),
				"amount": flt(it.get("amount")),
			}
		)
	if source.doctype != "Opportunity":
		totals = {
			"net": flt(source.net_total),
			"taxes": flt(source.total_taxes_and_charges),
			"discount": flt(source.discount_amount),
			"grand": flt(source.grand_total),
			"currency": source.currency,
		}

	row.update(
		items=items,
		totals=totals,
		links=chain.links(erp_doctype, name),
		address=_one_line(source.get("shipping_address") or source.get("address_display")),
		terms=strip_html_tags(source.get("terms") or "") if source.doctype != "Opportunity" else "",
		hasPdf=doctype != "po-submission",
	)
	return row


@frappe.whitelist()
def download_pdf(doctype: str, name: str):
	ctx = _ctx()
	_get_visible(doctype, name, ctx)
	erp_doctype = DOCTYPES[doctype]
	if erp_doctype == "Customer PO Submission":
		frappe.throw(_("Open the uploaded PO file instead"))

	print_format = PRINT_FORMATS.get(erp_doctype)
	if not print_format or not frappe.db.exists("Print Format", {"name": print_format, "disabled": 0}):
		print_format = "Standard"

	frappe.flags.ignore_print_permissions = True
	try:
		pdf = frappe.get_print(erp_doctype, name, print_format, as_pdf=True)
	finally:
		frappe.flags.ignore_print_permissions = False

	frappe.local.response.filename = f"{name}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf" if cint(frappe.form_dict.get("inline")) else "download"


@frappe.whitelist()
def download_po_file(name: str):
	"""Stream the PO document uploaded on a PO submission."""
	ctx = _ctx()
	row = _get_visible("po-submission", name, ctx)
	file = frappe.get_doc("File", {"file_url": row["file"], "attached_to_doctype": "Customer PO Submission", "attached_to_name": name})
	frappe.local.response.filename = file.file_name
	frappe.local.response.filecontent = file.get_content()
	frappe.local.response.type = "download"


# ---------------------------------------------------------------- PO submission


@frappe.whitelist()
def submit_po(quotation: str, customer_po: str, po_date: str, file_url: str, remarks: str | None = None):
	ctx = _ctx(write=True)
	row = _get_visible("quotation", quotation, ctx)
	if row["status"] != "Open":
		frappe.throw(_("Quotation {0} is not open for a PO").format(quotation))
	if not (customer_po or "").strip():
		frappe.throw(_("Enter your PO number"))

	file_name = frappe.db.get_value(
		"File", {"file_url": file_url, "owner": frappe.session.user, "attached_to_name": ["is", "not set"]}, "name"
	)
	if not file_name:
		frappe.throw(_("Attach the PO document"))

	doc = frappe.get_doc(
		{
			"doctype": "Customer PO Submission",
			"customer": ctx.customer,
			"quotation": quotation,
			"title": row["title"],
			"customer_po_no": customer_po.strip(),
			"po_date": po_date or nowdate(),
			"po_file": file_url,
			"remarks": remarks,
			"contact": ctx.contact,
			"status": "Pending confirmation",
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.set_value(
		"File",
		file_name,
		{"attached_to_doctype": doc.doctype, "attached_to_name": doc.name, "attached_to_field": "po_file"},
	)

	quote_owner = frappe.db.get_value("Quotation", quotation, "owner")
	doc.add_comment("Info", _("PO submitted from the customer portal by {0}").format(frappe.session.user))
	if quote_owner and quote_owner != "Administrator":
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": quote_owner,
				"reference_type": doc.doctype,
				"reference_name": doc.name,
				"description": _("Customer PO {0} received against {1}. Please confirm it.").format(
					doc.customer_po_no, quotation
				),
			}
		).insert(ignore_permissions=True)
	return doc.name


# ---------------------------------------------------------------- queries (Issue)


def _issues(ctx, name=None):
	filters = {"customer": ctx.customer}
	if name:
		filters["name"] = name
	issues = frappe.get_all(
		"Issue",
		filters=filters,
		fields=[
			"name", "subject", "issue_type", "status", "opening_date", "contact", "raised_by", "modified",
			"custom_portal_reference_doctype", "custom_portal_reference_name",
		],
		order_by="modified desc",
		limit_page_length=ROW_LIMIT,
	)
	if not ctx.is_admin:
		issues = [i for i in issues if i.contact in ctx.contacts or i.raised_by == ctx.user]
	return issues


def _query_row(issue, contacts):
	related = None
	slug = SLUGS.get(issue.custom_portal_reference_doctype)
	if slug and issue.custom_portal_reference_name:
		related = {"doctype": slug, "name": issue.custom_portal_reference_name}
	return {
		"name": issue.name,
		"subject": issue.subject,
		"category": issue.issue_type or "Other",
		"related": related,
		"owner": issue.contact,
		"ownerName": contacts.get(issue.contact) or issue.raised_by,
		"date": str(issue.opening_date or ""),
		"updated": str(issue.modified),
		"status": QUERY_STATUS.get(issue.status, "Awaiting Refteck"),
	}


@frappe.whitelist()
def get_queries():
	ctx = _ctx()
	contacts = {c.name: c.label for c in _contact_names(ctx.customer)}
	return [_query_row(i, contacts) for i in _issues(ctx)]


def _get_issue(name, ctx):
	issues = _issues(ctx, name)
	if not issues:
		frappe.throw(_("Query not available"), frappe.PermissionError)
	return issues[0]


@frappe.whitelist()
def get_query(name: str):
	ctx = _ctx()
	issue = _get_issue(name, ctx)
	contacts = {c.name: c.label for c in _contact_names(ctx.customer)}
	row = _query_row(issue, contacts)
	comms = frappe.get_all(
		"Communication",
		filters={"reference_doctype": "Issue", "reference_name": name, "communication_type": "Communication"},
		fields=["sent_or_received", "sender", "sender_full_name", "content", "creation"],
		order_by="creation asc",
	)
	row["messages"] = [
		{
			"by": "refteck" if c.sent_or_received == "Sent" else (issue.contact or c.sender),
			"author": c.sender_full_name or c.sender if c.sent_or_received == "Sent" else None,
			"at": str(c.creation),
			"text": unescape(strip_html_tags((c.content or "").replace("<br>", "\n").replace("</p>", "\n"))).strip(),
		}
		for c in comms
	]
	return row


@frappe.whitelist()
def create_query(subject: str, category: str, text: str, related: str | None = None):
	ctx = _ctx(write=True)
	if not (subject or "").strip() or not (text or "").strip():
		frappe.throw(_("Subject and details are required"))

	ref_doctype = ref_name = None
	if related and "|" in related:
		slug, ref_name = related.split("|", 1)
		_get_visible(slug, ref_name, ctx)
		ref_doctype = DOCTYPES[slug]

	issue = frappe.get_doc(
		{
			"doctype": "Issue",
			"subject": subject.strip(),
			"issue_type": category if frappe.db.exists("Issue Type", category) else None,
			"description": escape_html(text.strip()).replace("\n", "<br>"),
			"customer": ctx.customer,
			"contact": ctx.contact,
			"raised_by": frappe.session.user,
			"via_customer_portal": 1,
			"custom_portal_reference_doctype": ref_doctype,
			"custom_portal_reference_name": ref_name,
		}
	)
	issue.insert(ignore_permissions=True)
	return issue.name


@frappe.whitelist()
def reply_query(name: str, text: str):
	ctx = _ctx(write=True)
	issue = _get_issue(name, ctx)
	if not (text or "").strip():
		frappe.throw(_("Write a reply"))
	comm = frappe.get_doc(
		{
			"doctype": "Communication",
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Received",
			"email_status": "Open",
			"subject": issue.subject,
			"sender": frappe.session.user,
			"content": escape_html(text.strip()).replace("\n", "<br>"),
			"status": "Linked",
			"reference_doctype": "Issue",
			"reference_name": name,
		}
	)
	comm.flags.ignore_permissions = True
	comm.flags.ignore_mandatory = True
	comm.insert()
	# Communication sets the Issue back to Open; make sure a resolved one reopens too
	frappe.db.set_value("Issue", name, "status", "Open")
	return True


@frappe.whitelist()
def set_query_resolved(name: str, resolved: int):
	ctx = _ctx(write=True)
	_get_issue(name, ctx)
	issue = frappe.get_doc("Issue", name)
	issue.status = "Resolved" if cint(resolved) else "Open"
	issue.save(ignore_permissions=True)
	return issue.status


# ---------------------------------------------------------------- notifications


ICONS = {
	"Quotation": "lucide-file-text",
	"Sales Order": "lucide-circle-check",
	"Sales Invoice": "lucide-truck",
	"Customer PO Submission": "lucide-upload",
	"Issue": "lucide-message-square",
	"Opportunity": "lucide-target",
}


def unread_count():
	ctx = get_portal_context()
	if ctx and ctx.staff:
		return 0
	return frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0, "type": "Alert"})


@frappe.whitelist()
def get_unread():
	_ctx()
	return unread_count()


@frappe.whitelist()
def get_notifications():
	if _ctx().staff:
		# Staff alerts are desk notifications; customers get theirs in their own login
		return []
	logs = frappe.get_all(
		"Notification Log",
		filters={"for_user": frappe.session.user, "type": "Alert"},
		fields=["name", "subject", "email_content", "document_type", "document_name", "read", "creation"],
		order_by="creation desc",
		limit_page_length=200,
	)
	out = []
	for n in logs:
		slug = SLUGS.get(n.document_type)
		to = (
			f"/queries/{n.document_name}"
			if n.document_type == "Issue"
			else f"/print/{slug}/{n.document_name}"
			if slug
			else "/"
		)
		out.append(
			{
				"id": n.name,
				"icon": ICONS.get(n.document_type, "lucide-bell"),
				"title": strip_html_tags(n.subject or ""),
				"body": strip_html_tags(n.email_content or ""),
				"at": str(n.creation),
				"read": bool(n.read),
				"to": to,
			}
		)
	return out


@frappe.whitelist()
def mark_notifications_read(names: list | str | None = None):
	_ctx()
	names = frappe.parse_json(names) if isinstance(names, str) else names
	filters = {"for_user": frappe.session.user, "read": 0}
	if names:
		filters["name"] = ["in", names]
	for name in frappe.get_all("Notification Log", filters=filters, pluck="name"):
		frappe.db.set_value("Notification Log", name, "read", 1, update_modified=False)
	return unread_count()

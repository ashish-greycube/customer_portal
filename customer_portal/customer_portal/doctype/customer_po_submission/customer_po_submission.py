# Copyright (c) 2026, Greycube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomerPOSubmission(Document):
	def validate(self):
		quotation = frappe.db.get_value(
			"Quotation",
			self.quotation,
			["party_name", "quotation_to", "opportunity", "currency", "grand_total", "docstatus"],
			as_dict=True,
		)
		if not quotation or quotation.docstatus != 1:
			frappe.throw(frappe._("Quotation {0} is not submitted").format(self.quotation))
		if quotation.quotation_to != "Customer" or quotation.party_name != self.customer:
			frappe.throw(frappe._("Quotation {0} does not belong to customer {1}").format(self.quotation, self.customer))
		self.opportunity = quotation.opportunity
		self.currency = quotation.currency
		self.grand_total = quotation.grand_total

// Copyright (c) 2026, Greycube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer PO Submission", {
	refresh(frm) {
		if (frm.doc.status === "Pending confirmation" && frm.doc.quotation && !frm.is_new()) {
			frm.add_custom_button(__("Make Sales Order"), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
					source_name: frm.doc.quotation,
				});
			});
		}
	},
});

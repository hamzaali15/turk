{% include "turk/public/js/utils.js" %}


frappe.ui.form.on("Opportunity", {
	party_name: function (frm) {
		var opportunityFrom = frm.doc.opportunity_from;
		var phoneField;
		if (opportunityFrom == "Customer") {
			phoneField = "cust_phone_number";
			frappe.db.get_value(opportunityFrom, frm.doc.party_name, "additional_contact_numbers", (r) => {
				frm.set_value("additional_contact_number", r["additional_contact_numbers"]);
			});
		}
		else if (opportunityFrom == "Lead") {
			phoneField = "mobile_no";
		}
		frappe.db.get_value(opportunityFrom, frm.doc.party_name, phoneField, (r) => {
			frm.set_value("cust_phone_number", r[phoneField]);
		});
	},
	tiles_qty: function (frm) { calculate_total(frm); },
	tiles_rate: function (frm) { calculate_total(frm); },
	fittings_qty: function (frm) { calculate_total(frm); },
	fittings_rate: function (frm) { calculate_total(frm); },
	laticrete_qty: function (frm) { calculate_total(frm); },
	laticrete_rate: function (frm) { calculate_total(frm); },
	ceramics_qty: function (frm) { calculate_total(frm); },
	ceramics_rate: function (frm) { calculate_total(frm); },
	accessories_qty: function (frm) { calculate_total(frm); },
	accessories_rate: function (frm) { calculate_total(frm); },
	kitchen_appliances_qty: function (frm) { calculate_total(frm); },
	kitchen_appliances_rate: function (frm) { calculate_total(frm); }
});

frappe.ui.form.on("Opportunity", "refresh", function (frm, cdt, cdn) {
	if (frm.doc.opportunity_from == "Customer") {
		frm.fields_dict.party_name.get_query = function (doc, cdt, cdn) {
			return { query: "erpnext.controllers.queries.customer_query" }
		}
		set_address_query(frm, frm.doc.party_name);
	}
	
});

frappe.ui.form.on("Opportunity", "validate", function (frm, cdt, cdn) {
	if (frm.doc.opportunity_from == "Customer") {
		frappe.db.get_value(frm.doc.opportunity_from, frm.doc.party_name, "additional_contact_numbers", (r) => {
			frm.set_value("additional_contact_number", r["additional_contact_numbers"]);
	});
	}		
});

frappe.ui.form.on("Followup Detail", "sms_message", function (frm, cdt, cdn) {
	var item = locals[cdt][cdn];
	var total_characters = item.sms_message.length;
	var total_msg = 1;
	if (total_characters > 160) {
		total_msg = cint(total_characters / 160);
		total_msg = (total_characters % 160 == 0 ? total_msg : total_msg + 1);
	}
	frappe.model.set_value(cdt, cdn, "total_characters", total_characters);
	frappe.model.set_value(cdt, cdn, "total_messages", item.sms_message ? total_msg : 0);
});

function calculate_total(frm) {
	frm.set_value("tiles_amount", (frm.doc.tiles_qty * frm.doc.tiles_rate));
	frm.set_value("fittings_amount", (frm.doc.fittings_qty * frm.doc.fittings_rate));
	frm.set_value("laticrete_amount", (frm.doc.laticrete_qty * frm.doc.laticrete_rate));
	frm.set_value("ceramics_amount", (frm.doc.ceramics_qty * frm.doc.ceramics_rate));
	frm.set_value("accessories_amount", (frm.doc.accessories_qty * frm.doc.accessories_rate));
	frm.set_value("kitchen_appliances_amount", (frm.doc.kitchen_appliances_qty * frm.doc.kitchen_appliances_rate));
	frm.set_value("total_potential", (frm.doc.tiles_amount + frm.doc.fittings_amount + frm.doc.laticrete_amount +
		frm.doc.ceramics_amount + frm.doc.accessories_amount + frm.doc.kitchen_appliances_amount));
}

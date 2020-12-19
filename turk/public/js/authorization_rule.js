frappe.ui.form.on("Authorization Rule", {
	refresh: function (frm) {
		frm.events.set_master_type_ts(frm);
	},
	set_master_type_ts: function (frm) {
		if (frm.doc.based_on == "Item Group wise Discount") {
			unhide_field("master_name");
			frm.set_value("customer_or_item", "Item Group");
		}
	},
	based_on: function (frm) {
		frm.events.set_master_type_ts(frm);
	}
});
cur_frm.fields_dict['master_name'].get_query = function (doc) {
	if (doc.based_on == "Item Group wise Discount") {
		return {
			doctype: "Item Group",
			filters: [
				["Item Group", "name", "!=", ""]
			]
		};
	}
};
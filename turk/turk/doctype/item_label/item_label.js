// Copyright (c) 2020, RC and contributors
// For license information, please see license.txt

{% include "turk/public/js/utils.js" %}

frappe.ui.form.on('Item Label', {

	refresh: function(frm) {

        frm.set_query("price_list","items", function() {
	        return {
                "filters": {"selling": 1   }
            }
        });
	}
});

frappe.ui.form.on('Item Label Reference', {
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.db.get_value('Item', row.item_code, ["item_name", "item_group"], (r) => {
			frappe.model.set_value(cdt, cdn, "item_name", r.item_name);
			frappe.model.set_value(cdt, cdn, "item_group", r.item_group);			
		});
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Item Price",
				filters: { "item_code": row.item_code, "price_list": row.price_list},
				fieldname: "price_list_rate"
			},
			freeze: true,
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "item_price", r.message.price_list_rate);
				}
			}
		});
	},
	price_list: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Item Price",
				filters: { "item_code": row.item_code, "price_list": row.price_list},
				fieldname: "price_list_rate"
			},
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "item_price", r.message.price_list_rate);
				}
			}
		});
	}
});

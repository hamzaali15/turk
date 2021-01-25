{% include "turk/public/js/utils.js" %}
{% include 'erpnext/selling/doctype/sales_order/sales_order.js' %}
frappe.provide('turk.selling');


frappe.ui.form.on("Sales Order", {
	onload: function (frm) {
		set_address_query(frm, frm.doc.customer);
	},
	//company: function (frm) {
	//	if (frm.doc.docstatus == 0) {
	//		var ret_obj = setseries(frm.doc.company);
	//		frm.set_value("naming_series", ret_obj.series);
	//	}
	//},
	delivery_date: function (frm) {
		if (frm.doc.docstatus == 0) {
			$.each(frm.doc.items || [], function (i, d) { d.delivery_date = frm.doc.delivery_date; })
		}
	},
	refresh: function (frm) {
		set_address_query(frm, frm.doc.customer);
		if (frm.doc.docstatus == 0 && frm.doc.company) {
			$.each(frm.doc.items || [], function (i, d) {
				set_total_qty(frm, d.doctype, d.name, d.item_code);
			})
		}
	}
});
frappe.ui.form.on("Sales Order", "onload", function (frm, cdt, cdn) {

	setup_warehouse_query('warehouse', frm);

	// $.each(frm.doc.items || [], function (i, d) {
	// 	if (d.needs_approval) {
	// 		$("div[data-fieldname=items]").find('div.grid-row[data-idx=' + d.idx + ']').css({ 'background-color': '#ffff99' });
	// 		$("div[data-fieldname=items]").find('div.grid-row[data-idx=' + d.idx + ']').find('.grid-static-col').css({ 'background-color': '#ffff99' });
	// 	}
	// 	else {
	// 		$("div[data-fieldname=items]").find('div.grid-row[data-idx=' + d.idx + ']').css({ 'background-color': '#ffffff' });
	// 		$("div[data-fieldname=items]").find('div.grid-row[data-idx=' + d.idx + ']').find('.grid-static-col').css({ 'background-color': '#ffffff' });
	// 	}
	// })
	if (frm.doc.docstatus == 0) {
		calculate_total_boxes(frm);
		// frappe.call({
		// 	method: "frappe.client.get",
		// 	args: {
		// 		doctype: "User",
		// 		filters: { "name": frappe.session.user },
		// 		fieldname: "user_costcenter"
		// 	},
		// 	callback: function (r) {
		// 		if (r.message.user_costcenter) {
		// 			frappe.model.set_value(cdt, cdn, 'cost_center', r.message.user_costcenter);
		// 		}
		// 	}
		// })

		$.each(frm.doc.items || [], function (i, d) {
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
			if (d.sqm == d.boxes && d.pieces == d.boxes && d.def_boxes != 1 && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }

		})
	}

	// for (let item of frm.doc.items) {
	// 	if (item.needs_approval === 1 && item.custom_approver_role && in_list(frappe.user_roles, item.custom_approver_role)) {
	// 		var item_childtable = $(`div[data-name='${item.name}']`);
	// 		$(item_childtable).css('background-color', 'yellow');
	// 	}
	///}
});

frappe.ui.form.on("Sales Order", "validate", function (frm, cdt, cdn) {
	if (frm.doc.delivery_date < frm.doc.transaction_date){
		frappe.throw(__("Expected Delivery Date should be after the transaction date"));
	}
	if (frm.doc.docstatus == 0) {
		calculate_total_boxes(frm);
		// frappe.call({
		// 	method: "frappe.client.get",
		// 	args: {
		// 		doctype: "Address",
		// 		filters: { "name": frm.doc.customer_address },
		// 		fieldname: "territory"
		// 	},
		// 	callback: function (r) {
		// 		if (r.message.territory) {
		// 			frappe.model.set_value(cdt, cdn, 'territory', r.message.territory);
		// 		}
		// 	}
		// })
		var ret_obj = setseries(frm.doc.company);
		frm.set_value("naming_series", ret_obj.series);
		frm.set_value("customer_name", frm.doc.customer_name.toUpperCase());
		if (frm.doc.title)
			frm.set_value("title", frm.doc.title.toUpperCase());

		$.each(frm.doc.taxes || [], function (i, d) {
			d.cost_center = frm.doc.cost_center;
		})
		$.each(frm.doc.items || [], function (i, d) {
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
			if (d.sqm == d.boxes && d.pieces == d.boxes && d.def_boxes != 1 && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
			// get_approval_limit(d);
			// d.warehouse = ret_obj.twarehouse;
			// d.cost_center = frm.doc.cost_center;
			// frm.doc.set_warehouse = ret_obj.twarehouse;
		})
		validateBoxes(frm);
	}
});

frappe.ui.form.on('Sales Order Item',
	{
		pieces: function (frm, cdt, cdn) {if (frm.doc.docstatus == 0){ CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn);} },
		sqm: function (frm, cdt, cdn) {if (frm.doc.docstatus == 0){ CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); }},
		boxes: function (frm, cdt, cdn) {if (frm.doc.docstatus == 0){ CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); }},
		qty: function (frm, cdt, cdn) { if (frm.doc.docstatus == 0){ CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); }},
		item_code: function(frm, cdt, cdn) {
			frappe.model.set_value(cdt, cdn, "qty", 1);
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
			frappe.model.set_value(cdt, cdn, "discount_percentage", 0);
			frappe.model.set_value(cdt, cdn, "discount_amount", 0);
			set_total_qty(frm, cdt, cdn);
		}
	})

function setseries() {
	var ret_obj = { twarehouse: "Delivery Depot - TT", series: "TT-SO-" };
	return ret_obj;
}

function get_approval_limit(crow) {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Authorization Rule",
			filters: { "master_name": crow.item_group },
			fields: ["value", "approving_role"]
		},
		callback: function (r) {
			for (var i = 0; i < r.message.length; i++) {
				if (r.message[i].value && r.message[i].approving_role.includes('Sales Manager')) {
					crow.sales_manager_limit = r.message[i].value.toFixed(0);
				}
				if (r.message[i].value && r.message[i].approving_role.includes('Director')) {
					crow.director_limit = r.message[i].value.toFixed(0);
				}
			}
		}
	})
}


turk.selling.SalesOrderController = erpnext.selling.SalesOrderController.extend({
	onload: function (doc, dt, dn) {
		this._super();
	},
	refresh: function (doc, dt, dn) {
		this._super(doc);
		var me = this;
		this.frm.remove_custom_button(__('Update Items'));
		me.make_sales_invoice = this.ts_make_sales_invoice
		me.make_material_request = this.ts_make_material_request;
		me.make_delivery_note_based_on_delivery_date = this.ts_make_delivery_note_based_on_delivery_date;
		if (frappe.user.has_role('Update Sales Order')) {
			if (this.frm.doc.docstatus === 1 && this.frm.doc.status !== 'Closed'
				&& flt(this.frm.doc.per_delivered, 6) < 100 && flt(this.frm.doc.per_billed, 6) < 100) {
				this.frm.add_custom_button(__('Update Items'), () => {
					frappe.model.open_mapped_doc({
						method: "turk.hook_events.sales_order.make_so_updation",
						frm: cur_frm
					})
				});
			}
		}
	},
	ts_make_sales_invoice() {
		this.check_allow_delivery(this.frm, "Sales Invoice");
	},
	ts_make_material_request() {
		this.check_allow_delivery(this.frm, "Material Request");
	},
	ts_make_delivery_note_based_on_delivery_date() {
		this.check_allow_delivery(this.frm, "Delivery Note");
	},
	check_allow_delivery(frm, to_create) {
		var me = this;
		frappe.call({
			method: "turk.hook_events.sales_order.check_to_allow_delivery",
			args: {
				so: frm.docname,
				to_create: to_create
			},
			callback: function (r) {
				if (r.message && r.message == true) {
					if (to_create == "Sales Invoice") {
						frappe.model.open_mapped_doc({
							method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
							frm: me.frm
						})
					}
					else if (to_create == "Material Request") {
						frappe.model.open_mapped_doc({
							method: "erpnext.selling.doctype.sales_order.sales_order.make_material_request",
							frm: me.frm
						})
					}
					else if (to_create == "Delivery Note") {
						me.create_new_delivery_delivery_note();
					}
				}
			}
		});
	},
	create_new_delivery_delivery_note: function () {
		var me = this;

		var delivery_dates = [];
		$.each(this.frm.doc.items || [], function (i, d) {
			if (!delivery_dates.includes(d.delivery_date)) {
				delivery_dates.push(d.delivery_date);
			}
		});

		var item_grid = this.frm.fields_dict["items"].grid;
		if (!item_grid.get_selected().length && delivery_dates.length > 1) {
			var dialog = new frappe.ui.Dialog({
				title: __("Select Items based on Delivery Date"),
				fields: [{ fieldtype: "HTML", fieldname: "dates_html" }]
			});

			var html = $(`
				<div style="border: 1px solid #d1d8dd">
					<div class="list-item list-item--head">
						<div class="list-item__content list-item__content--flex-2">
							${__('Delivery Date')}
						</div>
					</div>
					${delivery_dates.map(date => `
						<div class="list-item">
							<div class="list-item__content list-item__content--flex-2">
								<label>
								<input type="checkbox" data-date="${date}" checked="checked"/>
								${frappe.datetime.str_to_user(date)}
								</label>
							</div>
						</div>
					`).join("")}
				</div>
			`);

			var wrapper = dialog.fields_dict.dates_html.$wrapper;
			wrapper.html(html);

			dialog.set_primary_action(__("Select"), function () {
				var dates = wrapper.find('input[type=checkbox]:checked')
					.map((i, el) => $(el).attr('data-date')).toArray();
				if (!dates) return;

				$.each(dates, function (i, d) {
					$.each(item_grid.grid_rows || [], function (j, row) {
						if (row.doc.delivery_date == d) {
							row.doc.__checked = 1;
						}
					});
				})
				me.new_delivery_note();
				dialog.hide();
			});
			dialog.show();
		} else {
			this.new_delivery_note();
		}
	},
	new_delivery_note: function () {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
			frm: me.frm
		})
	}
});

$.extend(cur_frm.cscript, new turk.selling.SalesOrderController({ frm: cur_frm }));

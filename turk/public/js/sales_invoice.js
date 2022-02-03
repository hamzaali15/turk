{% include "turk/public/js/utils.js" %}
frappe.provide("turk");

frappe.ui.form.on("Sales Invoice", "onload", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		if (frm.doc.is_return == 1) { frm.set_df_property("update_stock", "read_only", 1); }
	//	frm.get_field("custom_delivery_warehouse").get_query = function (doc, cdt, cdn) {
	//		return {
	//			filters: { 'company': doc.company }
	//		}
	//	}
		$.each(frm.doc.items || [], function (i, d) {
			if (!frm.doc.cust_sales_order_owner) {
				get_sales_order_owner(d.sales_order);
			}
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
		})
		$.each(frm.doc.items || [], function (i, d) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Sales Order",
					filters: { "name": d.sales_order },
					fieldname: "cost_center"
				},
				callback: function (r) {
					d.cost_center = r.message.cost_center
					cur_frm.refresh_field("items");
				}
			})
		})
	}
	frappe.after_ajax(function () {
		setup_warehouse_query('warehouse', frm);
	});
});

frappe.ui.form.on("Sales Invoice", "validate", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		validateBoxes(frm);
		// update_item_qty_based_on_sales_order(frm);
		calculate_total_boxes(frm);
		if (frm.doc.calculate_so_discount_ == true) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Sales Order",
					filters: { 'name': frm.doc.cust_sales_order_number },
					fields: ['discount_amount', 'total', 'grand_total']
				},
				callback: function (r) {
					var discount_per = (r.message[0].discount_amount * 100) / r.message[0].total;
					frm.set_value("additional_discount_percentage", discount_per);
					frm.set_value("discount_amount", (frm.doc.total * discount_per) / 100);

				}
			})
		}
		var sales_order_no = "0";
		// var ret_obj = setseries(frm.doc.company); cur_frm.set_value("naming_series", ret_obj.series);
	//	if (!frm.doc.custom_delivery_warehouse) { frm.set_value("custom_delivery_warehouse", "Delivery Depot - TC"); }
		$.each(frm.doc.items || [], function (i, d) {
			if (d.item_group != 'Fixed Assets') {
				if (d.qty == 0 || d.rate == 0) {
					frappe.throw("0 Qty or Rate is not allowed. Please check item " + d.item_code);
					frappe.validated = false; return;
				}
				// if (frm.doc.update_stock) {
				// 	if (d.qty > d.actual_qty) {
				// 		frappe.throw("Stock Is not availabe in selected warehouse for item code " + d.item_code);
				// 		frappe.validated = false; return;
				// 	}
				// }
			}
			// if (typeof d.sales_order !== "undefined") { sales_order_no = d.sales_order; }
		//	if (frm.doc.direct_delivery_from_warehouse && frm.doc.custom_delivery_warehouse != "Delivery Depot - TC") { d.warehouse = frm.doc.custom_delivery_warehouse; }

		})

		$.each(frm.doc.items || [], function (i, d) {

			// if (!d.sales_order) { d.sales_order = sales_order_no; }
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Sales Order",
					filters: { "name": d.sales_order },
					fieldname: "cost_center"
				},
				callback: function (r) {
					d.cost_center = r.message.cost_center;
				}
			})
		})
		cur_frm.refresh_field("items");
		if (!frm.doc.ignore_advances_calculation) {
			if (!frm.doc.is_return) {
				return frm.call({
					method: "set_advances",
					doc: frm.doc,
					callback: function (r, rt) {
						refresh_field("advances");
					}
				})
			}
		}
	}
});

frappe.ui.form.on("Sales Invoice", "refresh", function (frm, cdt, cdn) {
	// Validate Items, Update Qty based on Sales Order
	// if (frm.doc.docstatus == 0) {
	// 	var item_childtable = frm.fields_dict["items"].$wrapper;
	// 	var grid_buttons = $(item_childtable).find(".grid-buttons");
	// 	if (!$(grid_buttons).find(".custom-update-item-qty").length) {
	// 		$(grid_buttons).append(`
	// 						<button type="reset" class="custom-update-item-qty btn btn-xs btn-default"
	// 								style="margin-left: 4px;">
	// 							Validate Items
	// 						</button>
	// 					`);
	// 	}
	// 	$(grid_buttons).find(".custom-update-item-qty").off().click(function () {
	// 		update_item_qty_based_on_sales_order(frm);
	// 	});
	// }
	// frappe.after_ajax(function () {
	// 	setup_warehouse_query('warehouse', frm);
	// });
	// Split Invoice between Warehouse
	if (frm.doc.docstatus == 0 && !frm.doc.__islocal) {
		var label = __("Split Invoice between Warehouses");
		frm.add_custom_button(label, () => split_invoice_between_warehouse(frm));
	}
});

frappe.ui.form.on('Sales Invoice', {
	// company: function (frm) {
	// 	var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
	// },
	// before_save: function (frm) {
	// 	if (frm.doc.docstatus == 0) {
	// 		update_item_qty_based_on_sales_order(frm);
	// 	}
	// },
	// custom_delivery_warehouse: function (frm) {
	// 	$.each(frm.doc.items || [], function (i, d) {
	// 		frappe.model.set_value(d.doctype, d.name, "warehouse", frm.doc.custom_delivery_warehouse);
	// 	})
	// },
 //	direct_delivery_from_warehouse: function (frm) {
// 		if (frm.doc.direct_delivery_from_warehouse) {
// 			frappe.call({
// 				method: "frappe.client.get",
// 				args: {
// 					doctype: "User",
// 					filters: { "name": frappe.session.user },
// 					fieldname: "user_warehouse"
// 				},
// 				callback: function (r) {
// 					if (r.message.user_warehouse) {
// 						frm.set_value("custom_delivery_warehouse", r.message.user_warehouse);
// 					}
// 				}
// 			})
// 		}
// 	}
 });

frappe.ui.form.on('Sales Invoice Item',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		items_add: function (frm, cdt, cdn) {
			// var sales_order_no = "";
			// $.each(frm.doc.items || [], function (i, d) {
			// 	// if (d.sales_order) { sales_order_no = d.sales_order; }
			// });

			// if (sales_order_no) {
			// 	var item = locals[cdt][cdn];
			// 	item.sales_order = sales_order_no;
			// }
		},
		item_code: function (frm, cdt, cdn) {
			frappe.model.set_value(cdt, cdn, "qty", 1);
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
		}
	})

turk.SalesInvoiceController = erpnext.selling.SellingController.extend({
	setup: function(doc) {
		this.setup_posting_date_time_check();
		this._super(doc);
	},

	company: function() {
		erpnext.accounts.dimensions.update_dimension(this.frm, this.frm.doctype);
		let me = this;
		if (this.frm.doc.company) {
			frappe.call({
				method:
					"erpnext.accounts.party.get_party_account",
				args: {
					party_type: 'Customer',
					party: this.frm.doc.customer,
					company: this.frm.doc.company
				},
				callback: (response) => {
					if (response) me.frm.set_value("debit_to", response.message);
				},
			});
		}
	},

	onload: function() {
		var me = this;
		this._super();

		this.frm.ignore_doctypes_on_cancel_all = ['POS Invoice', 'Timesheet', 'POS Invoice Merge Log', 'POS Closing Entry'];
		if(!this.frm.doc.__islocal && !this.frm.doc.customer && this.frm.doc.debit_to) {
			// show debit_to in print format
			this.frm.set_df_property("debit_to", "print_hide", 0);
		}

		erpnext.queries.setup_queries(this.frm, "Warehouse", function() {
			return erpnext.queries.warehouse(me.frm.doc);
		});

		if(this.frm.doc.__islocal && this.frm.doc.is_pos) {
			//Load pos profile data on the invoice if the default value of Is POS is 1

			me.frm.script_manager.trigger("is_pos");
			me.frm.refresh_fields();
		}
		erpnext.queries.setup_warehouse_query(this.frm);
		erpnext.accounts.dimensions.setup_dimension_filters(this.frm, this.frm.doctype);
	},

	refresh: function(doc, dt, dn) {
		const me = this;
		this._super();
		if(cur_frm.msgbox && cur_frm.msgbox.$wrapper.is(":visible")) {
			// hide new msgbox
			cur_frm.msgbox.hide();
		}

		this.frm.toggle_reqd("due_date", !this.frm.doc.is_return);

		if (this.frm.doc.is_return) {
			this.frm.return_print_format = "Sales Invoice Return";
		}

		this.show_general_ledger();

		if(doc.update_stock) this.show_stock_ledger();

		if (doc.docstatus == 1 && doc.outstanding_amount!=0
			&& !(cint(doc.is_return) && doc.return_against)) {
			cur_frm.add_custom_button(__('Payment'),
				this.make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}

		if(doc.docstatus==1 && !doc.is_return) {

			var is_delivered_by_supplier = false;

			is_delivered_by_supplier = cur_frm.doc.items.some(function(item){
				return item.is_delivered_by_supplier ? true : false;
			})

			if(doc.outstanding_amount >= 0 || Math.abs(flt(doc.outstanding_amount)) < flt(doc.grand_total)) {
				cur_frm.add_custom_button(__('Return / Credit Note'),
					this.make_sales_return, __('Create'));
				cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
			}

			if(cint(doc.update_stock)!=1) {
				// show Make Delivery Note button only if Sales Invoice is not created from Delivery Note
				var from_delivery_note = false;
				from_delivery_note = cur_frm.doc.items
					.some(function(item) {
						return item.delivery_note ? true : false;
					});

				if(!from_delivery_note && !is_delivered_by_supplier) {
					cur_frm.add_custom_button(__('Delivery'),
						cur_frm.cscript['Make Delivery Note'], __('Create'));
				}
			}

			if (doc.outstanding_amount>0) {
				cur_frm.add_custom_button(__('Payment Request'), function() {
					me.make_payment_request();
				}, __('Create'));

				cur_frm.add_custom_button(__('Invoice Discounting'), function() {
					cur_frm.events.create_invoice_discounting(cur_frm);
				}, __('Create'));

				if (doc.due_date < frappe.datetime.get_today()) {
					cur_frm.add_custom_button(__('Dunning'), function() {
						cur_frm.events.create_dunning(cur_frm);
					}, __('Create'));
				}
			}

			if (doc.docstatus === 1) {
				cur_frm.add_custom_button(__('Maintenance Schedule'), function () {
					cur_frm.cscript.make_maintenance_schedule();
				}, __('Create'));
			}

			if(!doc.auto_repeat) {
				cur_frm.add_custom_button(__('Subscription'), function() {
					erpnext.utils.make_subscription(doc.doctype, doc.name)
				}, __('Create'))
			}
		}

		// Show buttons only when pos view is active
		if (cint(doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !doc.is_return) {
			this.frm.cscript.sales_order_btn();
			this.frm.cscript.purchase_invoice_btn();
			this.frm.cscript.delivery_note_btn();
			this.frm.cscript.quotation_btn();
		}

		this.set_default_print_format();
		if (doc.docstatus == 1 && !doc.inter_company_invoice_reference) {
			let internal = me.frm.doc.is_internal_customer;
			if (internal) {
				let button_label = (me.frm.doc.company === me.frm.doc.represents_company) ? "Internal Purchase Invoice" :
					"Inter Company Purchase Invoice";

				me.frm.add_custom_button(button_label, function() {
					me.make_inter_company_invoice();
				}, __('Create'));
			}
		}
	},

	make_maintenance_schedule: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_maintenance_schedule",
			frm: cur_frm
		})
	},

	on_submit: function(doc, dt, dn) {
		var me = this;

		if (frappe.get_route()[0] != 'Form') {
			return
		}

		$.each(doc["items"], function(i, row) {
			if(row.delivery_note) frappe.model.clear_doc("Delivery Note", row.delivery_note)
		})
	},

	set_default_print_format: function() {
		// set default print format to POS type or Credit Note
		if(cur_frm.doc.is_pos) {
			if(cur_frm.pos_print_format) {
				cur_frm.meta._default_print_format = cur_frm.meta.default_print_format;
				cur_frm.meta.default_print_format = cur_frm.pos_print_format;
			}
		} else if(cur_frm.doc.is_return && !cur_frm.meta.default_print_format) {
			if(cur_frm.return_print_format) {
				cur_frm.meta._default_print_format = cur_frm.meta.default_print_format;
				cur_frm.meta.default_print_format = cur_frm.return_print_format;
			}
		} else {
			if(cur_frm.meta._default_print_format) {
				cur_frm.meta.default_print_format = cur_frm.meta._default_print_format;
				cur_frm.meta._default_print_format = null;
			} else if(in_list([cur_frm.pos_print_format, cur_frm.return_print_format], cur_frm.meta.default_print_format)) {
				cur_frm.meta.default_print_format = null;
				cur_frm.meta._default_print_format = null;
			}
		}
	},

	sales_order_btn: function() {
		var me = this;
		this.$sales_order_btn = this.frm.add_custom_button(__('Sales Order'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
					source_doctype: "Sales Order",
					target: me.frm,
					setters: {
						customer: me.frm.doc.customer || undefined,
					},
					get_query_filters: {
						docstatus: 1,
						status: ["not in", ["Closed", "On Hold"]],
						per_billed: ["<", 99.99],
						company: me.frm.doc.company
					}
				})
			}, __("Get Items From"));
	},
	purchase_invoice_btn: function() {
		var me = this;
		this.$purchase_invoice_btn = this.frm.add_custom_button(__('Purchase Invoice'),
			function() {
				erpnext.utils.map_current_doc({
					method: "turk.utils.ts_make_sales_invoice",
					source_doctype: "Purchase Invoice",
					target: me.frm,
					date_field: "posting_date",
					setters: {
						company: me.frm.doc.company,
						shipment_no: me.frm.doc.shipment_no
					},
					get_query_filters: {
						docstatus: 1,
						company: me.frm.doc.company
					}
				})
			}, __("Get Items From"));
		},

	quotation_btn: function() {
		var me = this;
		this.$quotation_btn = this.frm.add_custom_button(__('Quotation'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.selling.doctype.quotation.quotation.make_sales_invoice",
					source_doctype: "Quotation",
					target: me.frm,
					setters: [{
						fieldtype: 'Link',
						label: __('Customer'),
						options: 'Customer',
						fieldname: 'party_name',
						default: me.frm.doc.customer,
					}],
					get_query_filters: {
						docstatus: 1,
						status: ["!=", "Lost"],
						company: me.frm.doc.company
					}
				})
			}, __("Get Items From"));
	},

	delivery_note_btn: function() {
		var me = this;
		this.$delivery_note_btn = this.frm.add_custom_button(__('Delivery Note'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
					source_doctype: "Delivery Note",
					target: me.frm,
					date_field: "posting_date",
					setters: {
						customer: me.frm.doc.customer || undefined
					},
					get_query: function() {
						var filters = {
							docstatus: 1,
							company: me.frm.doc.company,
							is_return: 0
						};
						if(me.frm.doc.customer) filters["customer"] = me.frm.doc.customer;
						return {
							query: "erpnext.controllers.queries.get_delivery_notes_to_be_billed",
							filters: filters
						};
					}
				});
			}, __("Get Items From"));
	},

	tc_name: function() {
		this.get_terms();
	},
	customer: function() {
		if (this.frm.doc.is_pos){
			var pos_profile = this.frm.doc.pos_profile;
		}
		var me = this;
		if(this.frm.updating_party_details) return;
		erpnext.utils.get_party_details(this.frm,
			"erpnext.accounts.party.get_party_details", {
				posting_date: this.frm.doc.posting_date,
				party: this.frm.doc.customer,
				party_type: "Customer",
				account: this.frm.doc.debit_to,
				price_list: this.frm.doc.selling_price_list,
				pos_profile: pos_profile
			}, function() {
				me.apply_pricing_rule();
			});

		if(this.frm.doc.customer) {
			frappe.call({
				"method": "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_loyalty_programs",
				"args": {
					"customer": this.frm.doc.customer
				},
				callback: function(r) {
					if(r.message && r.message.length > 1) {
						select_loyalty_program(me.frm, r.message);
					}
				}
			});
		}
	},

	make_inter_company_invoice: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_inter_company_purchase_invoice",
			frm: me.frm
		});
	},

	debit_to: function() {
		var me = this;
		if(this.frm.doc.debit_to) {
			me.frm.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Account",
					fieldname: "account_currency",
					filters: { name: me.frm.doc.debit_to },
				},
				callback: function(r, rt) {
					if(r.message) {
						me.frm.set_value("party_account_currency", r.message.account_currency);
						me.set_dynamic_labels();
					}
				}
			});
		}
	},

	allocated_amount: function() {
		this.calculate_total_advance();
		this.frm.refresh_fields();
	},

	write_off_outstanding_amount_automatically() {
		if (cint(this.frm.doc.write_off_outstanding_amount_automatically)) {
			frappe.model.round_floats_in(this.frm.doc, ["grand_total", "paid_amount"]);
			// this will make outstanding amount 0
			this.frm.set_value("write_off_amount",
				flt(this.frm.doc.grand_total - this.frm.doc.paid_amount - this.frm.doc.total_advance, precision("write_off_amount"))
			);
		}

		this.calculate_outstanding_amount(false);
		this.frm.refresh_fields();
	},

	write_off_amount: function() {
		this.set_in_company_currency(this.frm.doc, ["write_off_amount"]);
		this.write_off_outstanding_amount_automatically();
	},

	items_add: function(doc, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		this.frm.script_manager.copy_from_first_row("items", row, ["income_account", "discount_account", "cost_center"]);
	},

	set_dynamic_labels: function() {
		this._super();
		this.frm.events.hide_fields(this.frm)
	},

	items_on_form_rendered: function() {
		erpnext.setup_serial_or_batch_no();
	},

	packed_items_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_or_batch_no();
	},

	make_sales_return: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
			frm: cur_frm
		})
	},

	asset: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if(row.asset) {
			frappe.call({
				method: erpnext.assets.doctype.asset.depreciation.get_disposal_account_and_cost_center,
				args: {
					"company": frm.doc.company
				},
				callback: function(r, rt) {
					frappe.model.set_value(cdt, cdn, "income_account", r.message[0]);
					frappe.model.set_value(cdt, cdn, "cost_center", r.message[1]);
				}
			})
		}
	},

	is_pos: function(frm){
		this.set_pos_data();
	},

	pos_profile: function() {
		this.frm.doc.taxes = []
		this.set_pos_data();
	},

	set_pos_data: function() {
		if(this.frm.doc.is_pos) {
			this.frm.set_value("allocate_advances_automatically", 0);
			if(!this.frm.doc.company) {
				this.frm.set_value("is_pos", 0);
				frappe.msgprint(__("Please specify Company to proceed"));
			} else {
				var me = this;
				return this.frm.call({
					doc: me.frm.doc,
					method: "set_missing_values",
					callback: function(r) {
						if(!r.exc) {
							if(r.message && r.message.print_format) {
								me.frm.pos_print_format = r.message.print_format;
							}
							me.frm.trigger("update_stock");
							if(me.frm.doc.taxes_and_charges) {
								me.frm.script_manager.trigger("taxes_and_charges");
							}

							frappe.model.set_default_values(me.frm.doc);
							me.set_dynamic_labels();
							me.calculate_taxes_and_totals();
						}
					}
				});
			}
		}
		else this.frm.trigger("refresh");
	},

	amount: function(){
		this.write_off_outstanding_amount_automatically()
	},

	change_amount: function(){
		if(this.frm.doc.paid_amount > this.frm.doc.grand_total){
			this.calculate_write_off_amount();
		}else {
			this.frm.set_value("change_amount", 0.0);
			this.frm.set_value("base_change_amount", 0.0);
		}

		this.frm.refresh_fields();
	},

	loyalty_amount: function(){
		this.calculate_outstanding_amount();
		this.frm.refresh_field("outstanding_amount");
		this.frm.refresh_field("paid_amount");
		this.frm.refresh_field("base_paid_amount");
	},

	currency() {
		var me = this;
		this._super();
		if (this.frm.doc.timesheets) {
			this.frm.doc.timesheets.forEach((d) => {
				let row = frappe.get_doc(d.doctype, d.name)
				set_timesheet_detail_rate(row.doctype, row.name, me.frm.doc.currency, row.timesheet_detail)
			});
			this.frm.trigger("calculate_timesheet_totals");
		}
	}
});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new turk.SalesInvoiceController({frm: cur_frm}));

// function setseries(company) {
// 	var ret_obj = { twarehouse: "", series: "" };
// 	switch (company) {
// 		case "Turk Tiles": ret_obj.series = "TT-SI-"; break;
// //		case "T.S ENTERPRISES": ret_obj.series = "TE-SI-"; break;
// //		case "KALE FAISALABAD": ret_obj.series = "KF-SI-"; break;
// //		case "TILE BAZAR": ret_obj.series = "TB-SI-"; break;
// 	}
// 	if (cur_frm.doc.is_return) { ret_obj.series = ret_obj.series + "RT-" }
// 	return ret_obj;
// }

function search_in_roles(roles_array, role_string) {
	for (i = 0; i < roles_array.length; ++i) {
		if (roles_array[i].includes(role_string)) {
			return true;
		}
	}
	return false;
}

function get_sales_order_owner(sales_order) {
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Sales Order",
			filters: { "name": sales_order },
			fieldname: "owner"
		},
		callback: function (r) {
			// cur_frm.set_value("cust_sales_order_owner",r.message.owner);
			cur_frm.set_value("sales_order_owner", r.message.owner);
		}
	})
}

// function update_item_qty_based_on_sales_order(frm) {
// 	var items = [];
// 	$.each(frm.doc.items || [], function (i, d) {
// 		items.push({
// 			name: d.name,
// 			idx: d.idx,
// 			item_code: d.item_code,
// 			sales_order: d.sales_order,
// 			so_detail: d.so_detail,
// 			parent: frm.doc.name,
// 			qty: d.qty
// 		});
// 	});

// 	if (items.length) {
// 		frappe.call({
// 			method: "turk.utils.update_item_qty_based_on_sales_order",
// 			args: {
// 				"items": items
// 			},
// 			freeze: true,
// 			callback: function (r) {
// 				if (!r.exc) {
// 					$.each(r.message || {}, function (cdn, row) {
// 						$.each(row || {}, function (fieldname, value) {
// 							frappe.model.set_value("Sales Invoice Item", cdn, fieldname, value);
// 						});
// 					});
// 					frm.refresh_field("items");
// 				}
// 			}
// 		});
// 	}
// }

handlePrintButtonClickEvent(cur_frm);

function handlePrintButtonClickEvent(cur_frm) {
	var btn = document.getElementsByClassName('btn-print-print');
	if (btn) {
		for (var i = 0; i < btn.length; i++) {
			if (btn[i].textContent.trim() == "Print") {
				btn[i].addEventListener("click", function () {
					increase_print_count(cur_frm);
				});
				break;
			}
		}
	}
}

function increase_print_count(frm) {
	frappe.db.get_value(frm.doc.doctype, frm.doc.name, "print_count", (r) => {
		frappe.db.set_value(frm.doc.doctype, frm.doc.name, "print_count", Number(r.print_count) + 1);
	});
}

// cur_frm.cscript.onload = function (frm) {
// 	setup_warehouse_query('warehouse', frm);
// }

function split_invoice_between_warehouse(frm) {
	if(frm.is_dirty()) {
		frappe.throw(__("You have unsaved changes. Please save or reload the document first."))
	} else {
	frappe.confirm(__("Are you sure you want to split this Sales Invoice between Warehouses?"),
		() => frappe.call({
			method: "turk.hook_events.sales_invoice.split_invoice_between_warehouse",
			args: {
				"source_name": frm.doc.name
			},
			freeze: true,
			callback: function (r) {
				if (!r.exc) {
					frm.reload_doc();
				}
			}
		}),
		() => window.close()
	);
	}
}
frappe.provide("turk");


frappe.ui.form.on(cur_frm.doctype, {
	setup: function (frm) {
		// set conditional display for rate column in taxes
		$(frm.wrapper).on('grid-row-render', function (e, grid_row) {
			if (in_list(['Sales Taxes and Charges', 'Purchase Taxes and Charges'], grid_row.doc.doctype)) {
				erpnext.taxes.set_conditional_mandatory_rate_or_amount(grid_row);
			}
		});
	},

	onload: function (frm) {
		if (frm.get_field("taxes") && frm.doc.docstatus == 0) {
			frm.set_query("account_head", "taxes", function (doc) {
				if (frm.cscript.tax_table == "Sales Taxes and Charges") {
					var account_type = ["Tax", "Chargeable", "Expense Account"];
				} else {
					var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
				}

				return {
					query: "erpnext.controllers.queries.tax_account_query",
					filters: {
						"account_type": account_type,
						"company": doc.company
					}
				}
			});

			frm.set_query("cost_center", "taxes", function (doc) {
				return {
					filters: {
						'company': doc.company,
						"is_group": 0
					}
				};
			});
		}
	},

	refresh: function (frm) {
		if (frm.doc.docstatus == 0 && in_list(["Sales Order Updation", "Quotation", "Sales Order", "Sales Invoice", "Delivery Note", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Stock Entry", "Stock Reconciliation", "Material Request", "Item Label"], frm.doctype)) {
			var item_childtable = frm.fields_dict["items"].$wrapper;
			var grid_buttons = $(item_childtable).find(".grid-buttons");
			if (!$(grid_buttons).find(".custom-add-multiple-rows").length) {
				$(grid_buttons).append(`
					<button type="reset" class="custom-add-multiple-rows btn btn-xs btn-default"
							style="margin-left: 4px;">
						Add Items
					</button>
				`);
			}
			$(grid_buttons).find(".custom-add-multiple-rows").off().click(function () {
				frm.events.custom_add_multiple_items(frm);
			});
		}
	},

	custom_add_multiple_items: function (frm) {
		// frappe.custom_mutli_add_dialog(this.frm).show();
		let multi_item_dialog = frappe.custom_mutli_add_dialog(frm);
		multi_item_dialog.show();
		multi_item_dialog.$wrapper.find('.modal-dialog').css("width", "960px");
	},

	validate: function (frm) {
		// neither is absolutely mandatory
		if (frm.get_docfield("taxes")) {
			frm.get_docfield("taxes", "rate").reqd = 0;
			frm.get_docfield("taxes", "tax_amount").reqd = 0;
		}
	},

	taxes_on_form_rendered: function (frm) {
		erpnext.taxes.set_conditional_mandatory_rate_or_amount(frm.open_grid_row());
	}
});

frappe.provide("frappe");

frappe.custom_mutli_add_dialog = function (frm) {
	var dialog;

	const custom_warehouse_template1 = `
	<div style="display:block; max-height:320px; overflow-y:auto;">
	<table class="table table-bordered table-hover table-condensed custom-item-selection-tool">
		<thead>
			<tr>
				<th style="width: 90px" rowspan="2">Item Name</th>
				<th style="width: 360px" rowspan="2">Details</th>
				<th style="width: 80px" >Avail. Qty</th>
				<th style="width: 180px" colspan="3">Present Qty</th>
				<th style="width: 180px" colspan="3">Reserved Qty</th>

			</tr>
			<tr>
				<th>SQM</th>
				<th>SQM</th>
				<th>Boxes</th>
				<th>Pieces</th>
				<th>SQM</th>
				<th>Boxes</th>
				<th>Pieces</th>
			</tr>
		</thead>
		<tbody>
	`;

	const custom_warehouse_template2 = `</tbody></table></div>`;

	const custom_warehousewise_template1 = `
		<table class="table table-bordered table-hover table-condensed custom-warehouse-detail-tool">
			<thead>
				<tr>
					<th style="width: 280px" rowspan="2">Warehouse Name</th>
					<th style="width: 90px" >Avail. Qty</th>
					<th style="width: 210px" colspan="3">Present Qty</th>
					<th style="width: 210px" colspan="3">Reserved Qty</th>
				</tr>
				<tr>
					<th>SQM</th>
					<th>SQM</th>
					<th>Boxes</th>
					<th>Pieces</th>
					<th>SQM</th>
					<th>Boxes</th>
					<th>Pieces</th>
				</tr>
			</thead>
			<tbody>
		`;

	let fields = [
		{
			"label": __("Items Beginning with"),
			"fieldname": "item_search",
			"fieldtype": "Data"
		},
		{
			"label": __("Search"),
			"fieldname": "item_search_button",
			"fieldtype": "Button"
		},
		{
			"fieldname": "section_break",
			"fieldtype": "Section Break"
		},
		{
			"label": __("Item Name"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"onchange": function () {
				renderWarehousewiseItemDetails(frm);
			},
			"reqd": 1,
			"read_only": 1
		},
		{
			"fieldname": "column_break",
			"fieldtype": "Column Break"
		},
		{
			"label": __("Quantity (SQM)"),
			"fieldname": "quantity",
			"fieldtype": "Float",
			"reqd": 1
		},
		{
			"fieldname": "section_break",
			"fieldtype": "Section Break"
		},
		{
			"label": __("Item Detials"),
			"fieldname": "item_html",
			"fieldtype": "HTML"
		}
	];
	dialog = new frappe.ui.Dialog({
		title: __("Select Mutliple Items"),
		fields: fields,
		primary_action: function (values) {
			custom_add_item(frm, values.item_code, values.quantity);
			dialog.fields_dict.item_search_button.input.click();
		},
		primary_action_label: __("Add"),
		width: 800
	});

	dialog.fields_dict.item_search_button.input.onclick = function (frm) {
		get_item_details(true);
	}

	frappe.ui.keys.on("ctrl+f", function () {
		dialog.fields_dict.item_search_button.input.click();
	});

	function get_item_details(via_search) {
		// backend call to find the item details
		let txt = dialog.get_field("item_search").get_value();
		let item_code = '';
		if (!via_search) {
			item_code = dialog.get_field("item_code").get_value();
		}
		if (txt && txt != frappe.custom_item_details_string) {
			frappe.call({
				method: "turk.utils.get_item_details",
				args: {
					args: {
						txt: txt,
						item_code: item_code,
						customer: frm.doc.customer,
						update_stock: frm.doc.update_stock,
						company: frm.doc.company,
						order_type: frm.doc.order_type,
						transaction_date: frm.doc.transaction_date,
						doctype: frm.doc.doctype,
						name: frm.doc.name
					}
				},
				callback: function (r) {
					frappe.custom_item_details = r.message;
					frappe.custom_item_details_string = txt;
					createItemDetailTemplate(frm);
				}
			});
		} else if (true) {
			createItemDetailTemplate(frm);
		}
	}

	function createItemDetailTemplate(frm) {
		let customItemDetailsTemplate = '';
		let item_details = frappe.custom_item_details;
		if (item_details) {
			// create the sorted dict
			let sortedItems = Object.keys(item_details).map(function (key) {
				let data = item_details[key]['item_stock_totals'];
				return [key, data['actual_qty'] - data['reserved_qty']];
			});
			sortedItems.sort(function (first, second) {
				return second[1] - first[1];
			});

			customItemDetailsTemplate += custom_warehouse_template1;
			for (let item of sortedItems) {
				item = item[0];
				let actual_qty_sqm = item_details[item]["item_stock_totals"]["actual_qty"];
				let actual_qty_box = actual_qty_sqm / item_details[item]["uom_box"];
				actual_qty_box = Math.floor(actual_qty_box + .0001);
				let actual_qty_pieces = Math.round(actual_qty_sqm / (item_details[item]["uom_box"] / item_details[item]["uom_pieces"])) % item_details[item]["uom_pieces"];
				let reserved_qty_sqm = item_details[item]["item_stock_totals"]["reserved_qty"];
				let reserved_qty_box = reserved_qty_sqm / item_details[item]["uom_box"];
				reserved_qty_box = Math.floor(reserved_qty_box + .0001);
				let reserved_qty_pieces = Math.round(reserved_qty_sqm / (item_details[item]["uom_box"] / item_details[item]["uom_pieces"])) % item_details[item]["uom_pieces"];
				customItemDetailsTemplate += `
					<tr data-item=${item} class="custom-item-row">
						<td>${item}</td>
						<td>${item_details[item]["item_details"]}</td>
						<td><b>${flt(actual_qty_sqm - reserved_qty_sqm, 3)}</b></td>
						<td>${flt(actual_qty_sqm, 3)}</td>
						<td>${flt(actual_qty_box, 3) || 0}</td>
						<td>${flt(actual_qty_pieces, 3) || 0}</td>
						<td>${flt(reserved_qty_sqm, 3)}</td>
						<td>${flt(reserved_qty_box, 3) || 0}</td>
						<td>${flt(reserved_qty_pieces, 3) || 0}</td>
					</tr>`;
			}

			customItemDetailsTemplate += custom_warehouse_template2;
		} else {
			customItemDetailsTemplate += `<div>No Item stock details found.</div>`;
		}
		render_html_template(frm, customItemDetailsTemplate);
	}

	function renderWarehousewiseItemDetails(frm) {
		let customWarehouseDetailsTemplate = '';
		// let item_details = frappe.custom_item_details;
		let item_code = dialog.get_field("item_code").get_value();
		let warehouse_dict = frappe.custom_item_details[item_code]["warehouse_details"]
		if (Object.keys(warehouse_dict).length) {
			customWarehouseDetailsTemplate += custom_warehousewise_template1;
			for (let warehouse in warehouse_dict) {
				let actual_qty_sqm = warehouse_dict[warehouse]["actual_qty"];
				let reserved_qty_sqm = warehouse_dict[warehouse]["reserved_qty"];

				if (actual_qty_sqm != 0 || reserved_qty_sqm != 0) {
					let actual_qty_box = actual_qty_sqm / warehouse_dict[warehouse]["uom_box"];
					actual_qty_box = Math.floor(actual_qty_box + .0001);
					let actual_qty_pieces = Math.round(actual_qty_sqm / (warehouse_dict[warehouse]["uom_box"] / warehouse_dict[warehouse]["uom_pieces"])) % warehouse_dict[warehouse]["uom_pieces"];
					let reserved_qty_box = reserved_qty_sqm / warehouse_dict[warehouse]["uom_box"];
					reserved_qty_box = Math.floor(reserved_qty_box + .0001);
					let reserved_qty_pieces = Math.round(reserved_qty_sqm / (warehouse_dict[warehouse]["uom_box"] / warehouse_dict[warehouse]["uom_pieces"])) % warehouse_dict[warehouse]["uom_pieces"];
					customWarehouseDetailsTemplate += `
					<tr data-item=${warehouse} class="custom-item-row">
						<td>${warehouse}</td>
						<td><b>${flt(actual_qty_sqm - reserved_qty_sqm, 3)}</b></td>
						<td>${flt(actual_qty_sqm, 3)}</td>
						<td>${flt(actual_qty_box, 3) || 0}</td>
						<td>${flt(actual_qty_pieces, 3) || 0}</td>
						<td>${flt(reserved_qty_sqm, 3)}</td>
						<td>${flt(reserved_qty_box, 3) || 0}</td>
						<td>${flt(reserved_qty_pieces, 3) || 0}</td>

					</tr>
					`;
				}
			}
			customWarehouseDetailsTemplate += custom_warehouse_template2;
		} else {
			customWarehouseDetailsTemplate += `<div>No Warehouse details found.</div>`
		}
		render_html_template(frm, customWarehouseDetailsTemplate, true);
	}

	function render_html_template(frm, htmlTemplate, warehouseWiseDetails = false) {
		var item_html_df = dialog.get_field("item_html");
		$(item_html_df.wrapper).empty();
		var warehouse_table = $(frappe.render_template(htmlTemplate));
		warehouse_table.appendTo(item_html_df.wrapper);

		if (!warehouseWiseDetails) {
			$(".custom-item-row").click(function () {
				let old_item_code = dialog.get_value("item_code");
				let old_quantity = dialog.get_value("quantity");
				let new_quantity = 1;
				let itme_clicked = $(this).attr("data-item");
				dialog.set_value("item_code", itme_clicked);
				if (old_item_code === itme_clicked) {
					new_quantity = old_quantity + 1;
				}
				dialog.set_value("quantity", new_quantity);
			})
		}
	}

	function custom_add_item(frm, item_code, item_qty) {
		// add row or update qty
		var added = false;

		// find row with item if exists
		$.each(frm.doc.items || [], (i, d) => {
			if (d["item_code"] === item_code) {
				frappe.model.set_value(d.doctype, d.name, 'qty', d.qty + item_qty);
				frappe.show_alert({ message: __("Added Item  {0} {1}", [item_code, item_qty]), indicator: 'green' });
				added = true;
				return false;
			}
		});

		if (!added) {
			var childDoctype = frm.doctype == "Sales Order Updation" ? "SO Updation Item" : frm.doctype + " Item";
			var item_row = frappe.model.add_child(frm.doc, childDoctype, "items");
			item_row.item_code = item_code;
			item_row.qty = item_qty;
			if (frappe.custom_item_details[item_code]) {
				item_row.def_boxes = frappe.custom_item_details[item_code]["uom_box"];
				item_row.def_pieces = frappe.custom_item_details[item_code]["uom_pieces"];
			}

			frm.refresh_field("items");

			frappe.run_serially([
				() => frappe.model.set_value(item_row.doctype, item_row.name, "item_code", item_row.item_code),
				() => frm.script_manager.trigger("item_code", item_row.doctype, item_row.name),
				() => frappe.model.set_value(item_row.doctype, item_row.name, 'qty', item_qty),
				() => frm.script_manager.trigger("qty", item_row.doctype, item_row.name),
				() => frappe.timeout(0.1),
				() => {
					frm.refresh_field("items");
					frappe.show_alert({ message: __("Added Item - {0} with quantity - {1}", [item_code, item_qty]), indicator: 'green' });
				}
			]);
		}
	}
	return dialog;
}

function CalculateSQM(crow, field, cdt, cdn) {
	if (typeof crow.def_boxes != 'undefined' && crow.def_boxes && crow.def_boxes > 0) {
		var total_piece = 0.0;
		switch (field) {
			case "pieces": total_piece = Math.round(crow.pieces + (crow.boxes * crow.def_pieces)); break;
			case "boxes": total_piece = Math.round(crow.boxes * crow.def_pieces); break;
			case "sqm": total_piece = Math.round(crow.sqm / (crow.def_boxes / crow.def_pieces)); break;
			case "qty": total_piece = Math.round(crow.qty / (crow.def_boxes / crow.def_pieces));
		}
		var new_sqm = parseFloat((total_piece * (crow.def_boxes / crow.def_pieces)).toFixed(4));
		if (new_sqm > 0) {
			crow.boxes = Math.floor((new_sqm / crow.def_boxes).toFixed(4));
		} else { crow.boxes = Math.ceil((new_sqm / crow.def_boxes).toFixed(4)); }

		crow.pieces = (total_piece % crow.def_pieces);
		frappe.model.set_value(cdt, cdn, 'qty', new_sqm);
		crow.sqm = new_sqm;
		cur_frm.refresh_field("items");
	}
	else {
		var new_sqm = 0;
		switch (field) {
			case "pieces": new_sqm = crow.pieces; break;
			case "boxes": new_sqm = crow.boxes; break;
			case "sqm": new_sqm = crow.sqm; break;
			case "qty": new_sqm = crow.qty; break;
		}
		crow.sqm = new_sqm;
		crow.boxes = new_sqm;
		crow.pieces = new_sqm;
		crow.qty = new_sqm;
		cur_frm.refresh_field("items");
	}
	var dt = ["Sales Order Updation", "Stock Reconciliation"];
	if (!dt.includes(cur_frm.doctype)) {
		calculate_total_boxes(cur_frm);
	}
}
function calculate_total_boxes(frm) {
	var totalqty = 0, totalbox = 0, totalpieces = 0, loosetotal = 0;
	$.each(frm.doc.items || [], function (i, d) {
		totalqty += d.qty;
		totalbox += d.boxes;
		totalpieces += d.pieces;
		loosetotal += (d.boxes * d.def_pieces) + d.pieces;
	});
	frm.set_value("cust_total_qty", totalqty);
	frm.set_value("cust_total_box", totalbox);
	frm.set_value("cust_total_pieces", totalpieces);
	frm.set_value("custom_loose_total", loosetotal);
}


function setup_warehouse_query(warehouse, frm) {
	frm.set_query(warehouse, 'items', function (doc, cdt, cdn) {
		var row = locals[cdt][cdn];
		var filters = erpnext.queries.warehouse(frm.doc);
		if (row.item_code) {
			$.extend(filters, { "query": "turk.utils.warehouse_query" });
			filters["filters"].push(["Bin", "item_code", "=", row.item_code]);
		}
		return filters
	});
}

var set_total_qty = function (frm, cdt, cdn) {
	var row = locals[cdt][cdn];
	if (row.item_code && frm.doc.company) {
		frappe.call({
			method: "turk.utils.get_total_item_qty",
			args: {
				"company": frm.doc.company,
				"item_code": row.item_code
			},
			callback: function (r) {
				var total_qty = r.message > 0 ? Number(r.message).toFixed(4) : '0';
				frappe.model.set_value(cdt, cdn, 'total_qty', total_qty);
			}
		});
	}
}


function set_address_query(frm, customer) {
	if (frappe.meta.has_field(frm.doctype, "shipping_address_name")) {
		frm.fields_dict.shipping_address_name.get_query = function (doc, cdt, cdn) {
			return {
				query: "turk.utils.address_query",
				filters: {
					address_title: customer
				}
			}
		}
	}
	if (frappe.meta.has_field(frm.doctype, "customer_address")) {
		frm.fields_dict.customer_address.get_query = function (doc, cdt, cdn) {
			return {
				query: "turk.utils.address_query",
				filters: {
					address_title: customer
				}
			}
		}
	}
}

function validateBoxes(frm) {
	var qtyFieldName = frm.doc.doctype == "Purchase Receipt" ? "received_qty" : "qty";
	$.each(frm.doc.items || [], function (i, d) {
		CalculateSQM(d, qtyFieldName, d.doctype, d.name);
	})
}
frappe.ui.form.on("Customer", "onload", function (frm, cdt, cdn) {
	var is_salesman = search_in_roles(frappe.user_roles, "Salesman TC");
	if (frm.doc.__islocal != 1 && is_salesman) {
		frm.set_df_property("customer_name", "read_only", 1);
		frm.set_df_property("customer_group", "read_only", 1);
		frm.set_df_property("cust_phone_number", "read_only", 1);
	}
});

frappe.ui.form.on("Customer", "validate", function (frm, cdt, cdn) {
	frm.set_value("customer_name", frm.doc.customer_name.toUpperCase());
	validate_number(frm);
});

frappe.ui.form.on("Customer", {
	cust_phone_number: function (frm) { validate_number(frm); },
	cnic: function (frm) { validate_cnic(frm); }
});

function search_in_roles(roles_array, role_string) {
	for (var i = 0; i < roles_array.length; ++i) {
		if (roles_array[i].includes(role_string)) {
			return true;
		}
	}
	return false;
}

function validate_number(frm) {
	var manager_accounts = search_in_roles(frappe.user_roles, "Manager Accounts TC")
	if (frm.doc.cust_phone_number && !manager_accounts) {
		var reg = /[^0-9]/g;
		frm.set_value("cust_phone_number", frm.doc.cust_phone_number.replace(reg, ''));
		if (!(frm.doc.cust_phone_number.length == 11 || reg.test(frm.doc.cust_phone_number))) {
			frappe.throw("Phone Number should be 11 digit and Numbers only. ");
			frappe.validated = false; return;
		}
	}
}

function validate_cnic(frm) {
	if (frm.doc.cnic) {
		var reg = /[^0-9]/g;
		frm.set_value("cnic", frm.doc.cnic.replace(reg, ''));
		if (!(frm.doc.cnic.length == 13 || reg.test(frm.doc.cnic))) {
			frappe.throw("CNIC number should be 13 digit and Numbers only without '-'. ");
			frappe.validated = false; return;
		}
	}
}
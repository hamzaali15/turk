import frappe
from frappe import _


def validate_user_warehouse(se, method):
	if not se.bypass_transit_warehouse :
		user_warehouse = frappe.db.get_value("User", {"name": frappe.session.user}, "user_warehouse")
		strTransit = "Transit"
		if user_warehouse :
			for d in se.get("items"):
				if d.t_warehouse:
					if ( strTransit in d.t_warehouse ):
						if not (user_warehouse in d.s_warehouse or user_warehouse.replace("Normal","Breakage") in d.s_warehouse or user_warehouse.replace("Depot","Breakage") in d.s_warehouse ):
							frappe.throw(_("you are note allowed to tranfer stock from warehouse {0} .").format(d.s_warehouse))

				if d.s_warehouse:
					if ( strTransit in d.s_warehouse):
							if not (user_warehouse in d.t_warehouse or user_warehouse.replace("Normal","Breakage") in d.t_warehouse or user_warehouse.replace("Depot","Breakage") in d.t_warehouse ):
								frappe.throw(_("you cannot Receive stock from warehouse {0} .").format(d.t_warehouse))
		else :
			frappe.throw(_("your user has not allocated any warehouse ."))
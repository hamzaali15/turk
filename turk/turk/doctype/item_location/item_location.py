# -*- coding: utf-8 -*-
# Copyright (c) 2020, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ItemLocation(Document):
	def on_submit(self):
		for d in self.get("items"):							
			old_item_location = frappe.db.get_value("Item", {"name": d.item_code},"bin_location")
			# update Item Location if it's available and 			
			if(old_item_location != d.bin_location):
				frappe.db.set_value("Item", d.item_code, "bin_location", d.bin_location)
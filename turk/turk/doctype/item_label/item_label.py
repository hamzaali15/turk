# -*- coding: utf-8 -*-
# Copyright (c) 2020, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ItemLabel(Document):

	def on_submit(self):
		for d in self.get("items"):
			# Check for Price list if it dosent exsist. create  a new one. # Get Item Price name
			item_price_name = frappe.db.get_value("Item Price", {"item_code": d.item_code,"price_list": d.price_list},"name")
			if not item_price_name:
				self.make_item_price(d.item_code,d.price_list,d.item_price)
			else :
				old_item_price = frappe.db.get_value("Item Price", {"name": item_price_name},"price_list_rate")
				# update Item Price if it's available and
				if(old_item_price != d.item_price):
					frappe.db.set_value("Item Price", item_price_name, "price_list_rate", d.item_price)

	def make_item_price(self,item, price_list_name, item_price):
		frappe.get_doc({
			"doctype": "Item Price",
			"price_list": price_list_name,
			"item_code": item,
			"price_list_rate": item_price
		}).insert(ignore_permissions=True)

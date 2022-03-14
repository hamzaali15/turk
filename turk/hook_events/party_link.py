# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.party import get_party_account


def create_invoice_adj_jv(self,cdt):
	if self.doctype == 'Sales Invoice' and self.is_pos == 0 and self.no_double_ledger==0:
		doc = frappe.get_doc(self,cdt)
		customer_list = frappe.get_list('Party Link', filters= {'primary_role':'Supplier','secondary_party':self.customer}, fields = "*" )
		customer_dp = None
		supplier_dp = None
		primary_role_dp = None

		if customer_list:
			for msg in customer_list:
				customer_dp = msg.secondary_party
				supplier_dp = msg.primary_party
				primary_role_dp = msg.primary_role

			customer_account_type = get_party_account('Customer', customer_dp, doc.company)
			supplier_account_type = get_party_account('Supplier', supplier_dp, doc.company)

			jv = frappe.new_doc('Journal Entry')
			jv.voucher_type = 'Journal Entry'
			jv.naming_series = 'JV-'
			jv.posting_date = doc.posting_date
			jv.company = doc.company
			jv.remark = 'Adjustment for Sales Invoice# {0}'.format(doc.name)

		#Entry for Customer
			jv.append('accounts', {
				'account': customer_account_type,
				'party_type': 'Customer',
				'party': customer_dp,
				'reference_type': 'Sales Invoice',
				'reference_name': doc.name,
				'credit_in_account_currency': doc.total
			})
		#Entry for Supplier    
			jv.append('accounts', {
				'account': supplier_account_type,
				'party_type': 'Supplier',
				'party': supplier_dp,
				'debit_in_account_currency': doc.total,
				'is_advance': 'Yes'
			})

			jv.save()
			jv.submit()

def cancel_adjusted_jv(self,cdt):
	doc = frappe.get_doc(self,cdt)
	if self.doctype == 'Sales Invoice' and self.is_pos == 0 and self.no_double_ledger==0:
		doc = frappe.get_doc(self,cdt)
		customer_list = frappe.get_list('Party Link', filters= {'primary_role':'Supplier','secondary_party':self.customer}, fields = "*" )
		if customer_list:
			jv_list = frappe.get_list('Journal Entry', filters= [['remark','like','%{0}%'.format(doc.name)],['docstatus','=','1']], fields = "*" )
			jv_name = None
			if(jv_list!=None):
				for msg in jv_list:
					jv_name = msg.name
				if jv_name!=None:
					jv_doc = frappe.get_doc('Journal Entry', jv_name)
					jv_doc.cancel()
					frappe.msgprint("Journal Entry " + jv_name + " cancelled")

def prevent_linked_jv_cancellation(self,cdt):
	pass
	# for f in self.accounts:
	# 	if f.reference_type!= None:
	# 		frappe.throw("Journal Entry linked with {0} {1}".format(f.reference_type, f.reference_name))
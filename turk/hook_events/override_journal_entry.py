import frappe
from frappe.utils import flt, cint
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry

class OverrideJournalEntry(JournalEntry):
	def validate_invoices(self):
		pass 
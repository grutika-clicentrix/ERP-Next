import frappe
from custom_ui.custom_ui.ai_chat.handler import chat

@frappe.whitelist()
def get_current_month_cost():
    return 0.0

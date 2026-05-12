import frappe
from frappe import _

def debug_assets():
    company = "Wood Craft Furniture Pvt. Ltd."
    comp_curr = frappe.get_value("Company", company, "default_currency")
    print(f"Company: {company}, Currency: {comp_curr}")
    
    accounts = [
        "Plants and Machineries - WCFPL",
        "Buildings - WCFPL",
        "Office Equipments - WCFPL",
        "Accumulated Depreciation - WCFPL",
        "Depreciation - WCFPL"
    ]
    
    for acc in accounts:
        curr = frappe.get_value("Account", acc, "account_currency")
        print(f"Account: {acc}, Currency: {curr}")
        if not curr or curr == "":
            print(f"Updating {acc} to {comp_curr}")
            frappe.db.set_value("Account", acc, "account_currency", comp_curr)
    
    frappe.db.commit()

if __name__ == "__main__":
    debug_assets()

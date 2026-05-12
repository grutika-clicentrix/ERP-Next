import frappe
from frappe.utils import fmt_money

def audit_transactions():
    company = "Wood Craft Furniture Pvt. Ltd."
    abbr = "WCFPL"
    
    print("--- 📊 DATA AUDIT REPORT ---")
    
    doctypes = [
        "Customer", "Supplier", "Item", 
        "Sales Invoice", "Purchase Invoice", 
        "Stock Entry", "Payment Entry", "Journal Entry",
        "Asset"
    ]
    
    for dt in doctypes:
        count = frappe.db.count(dt)
        print(f"{dt:20}: {count}")
    
    # Financials (using sum of GL Entry)
    bank_account = f"WCFPL Current Account - HDFC - {abbr}"
    balance = frappe.db.sql(f"select sum(debit) - sum(credit) from `tabGL Entry` where account='{bank_account}' and is_cancelled=0")[0][0] or 0
    print(f"\n{'Bank Balance':20}: {fmt_money(balance, currency='INR')}")
    
    # Sales Total
    sales_total = frappe.db.sql(f"select sum(grand_total) from `tabSales Invoice` where docstatus=1 and company='{company}'")[0][0] or 0
    print(f"{'Total Sales':20}: {fmt_money(sales_total, currency='INR')}")
    
    # Purchase Total
    purchase_total = frappe.db.sql(f"select sum(grand_total) from `tabPurchase Invoice` where docstatus=1 and company='{company}'")[0][0] or 0
    print(f"{'Total Purchases':20}: {fmt_money(purchase_total, currency='INR')}")

if __name__ == "__main__":
    audit_transactions()

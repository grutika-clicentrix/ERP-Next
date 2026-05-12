import frappe
from frappe.utils import add_days, add_months, getdate, nowdate, flt
import random

def setup_transactions():
    company = "Wood Craft Furniture Pvt. Ltd."
    abbr = "WCFPL"
    bank_account = f"WCFPL Current Account - HDFC - {abbr}"
    warehouse_stores = f"Stores - {abbr}"
    warehouse_fg = f"Finished Goods - {abbr}"
    
    frappe.db.set_value("Stock Settings", None, "allow_negative_stock", 1)
    frappe.db.sql("update tabCustomer set payment_terms = ''")
    frappe.db.sql("update tabSupplier set payment_terms = ''")
    frappe.db.commit()

    start_date = getdate("2025-04-01")
    end_date = getdate("2026-03-31")
    
    customers = frappe.get_all("Customer", fields=["name"])
    suppliers = frappe.get_all("Supplier", fields=["name"])
    items_fg = frappe.get_all("Item", filters={"item_group": "Finished Goods"}, fields=["name", "stock_uom"])
    items_rm = frappe.get_all("Item", filters={"item_group": ["in", ["Raw Material", "Consumable"]]}, fields=["name", "stock_uom"])
    
    sales_tax_template = frappe.get_value("Sales Taxes and Charges Template", {"company": company})
    purchase_tax_template = frappe.get_value("Purchase Taxes and Charges Template", {"company": company})

    print(f"Starting transaction generation from {start_date} to {end_date}...")

    current_date = start_date
    while current_date <= end_date:
        print(f"Processing Month: {current_date.strftime('%B %Y')}")
        
        # --- PURCHASES ---
        for i in range(random.randint(30, 40)):
            txn_date = add_days(current_date, random.randint(0, 27)).strftime("%Y-%m-%d")
            sup = random.choice(suppliers)
            item = random.choice(items_rm)
            qty = random.randint(100, 500)
            rate = frappe.get_value("Item Price", {"item_code": item["name"], "price_list": "Standard Buying"}, "price_list_rate") or random.randint(10, 500)
            
            se = frappe.get_doc({
                "doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": company, "posting_date": txn_date,
                "items": [{"item_code": item["name"], "qty": qty, "t_warehouse": warehouse_stores, "basic_rate": rate, "uom": item["stock_uom"], "conversion_factor": 1}]
            })
            se.set_missing_values()
            se.insert().submit()
            
            pi = frappe.get_doc({
                "doctype": "Purchase Invoice", "company": company, "posting_date": txn_date, "supplier": sup["name"],
                "update_stock": 0, "items": [{"item_code": item["name"], "qty": qty, "rate": rate, "uom": item["stock_uom"], "conversion_factor": 1}],
                "taxes_and_charges": purchase_tax_template, "due_date": add_days(txn_date, 30), "bill_date": txn_date,
                "currency": "INR", "conversion_rate": 1.0, "price_list_currency": "INR", "plc_conversion_rate": 1.0
            })
            pi.set_missing_values()
            pi.calculate_taxes_and_totals()
            pi.flags.ignore_validate = True
            pi.insert().submit()
            pi.reload()
            
            if random.random() < 0.7:
                amt = pi.outstanding_amount
                pe = frappe.get_doc({
                    "doctype": "Payment Entry", "payment_type": "Pay", "company": company, "posting_date": txn_date,
                    "party_type": "Supplier", "party": sup["name"], "paid_from": bank_account, "paid_to": pi.credit_to,
                    "paid_amount": amt, "received_amount": amt,
                    "reference_no": f"PAY-{pi.name}", "reference_date": txn_date,
                    "references": [{"reference_doctype": "Purchase Invoice", "reference_name": pi.name, "allocated_amount": amt}]
                })
                pe.set_missing_values()
                pe.insert().submit()

        # --- MANUFACTURING ---
        for i in range(random.randint(15, 25)):
            txn_date = add_days(current_date, random.randint(0, 27)).strftime("%Y-%m-%d")
            fg_item = random.choice(items_fg)
            qty = random.randint(5, 15)
            se = frappe.get_doc({
                "doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": company, "posting_date": txn_date,
                "items": [{"item_code": fg_item["name"], "qty": qty, "t_warehouse": warehouse_fg, "basic_rate": random.randint(5000, 15000), "uom": fg_item["stock_uom"], "conversion_factor": 1}]
            })
            se.set_missing_values()
            se.insert().submit()

        # --- SALES ---
        for i in range(random.randint(80, 100)):
            txn_date = add_days(current_date, random.randint(0, 27)).strftime("%Y-%m-%d")
            cust = random.choice(customers)
            item = random.choice(items_fg)
            qty = random.randint(1, 3)
            rate = frappe.get_value("Item Price", {"item_code": item["name"], "price_list": "Standard Selling"}, "price_list_rate") or random.randint(10000, 40000)
            
            se = frappe.get_doc({
                "doctype": "Stock Entry", "stock_entry_type": "Material Issue", "company": company, "posting_date": txn_date,
                "items": [{"item_code": item["name"], "qty": qty, "s_warehouse": warehouse_fg, "uom": item["stock_uom"], "conversion_factor": 1}]
            })
            se.set_missing_values()
            se.insert().submit()
            
            si = frappe.get_doc({
                "doctype": "Sales Invoice", "company": company, "posting_date": txn_date, "customer": cust["name"],
                "update_stock": 0, "items": [{"item_code": item["name"], "qty": qty, "rate": rate, "uom": item["stock_uom"], "conversion_factor": 1}],
                "taxes_and_charges": sales_tax_template, "due_date": add_days(txn_date, 30),
                "currency": "INR", "conversion_rate": 1.0, "price_list_currency": "INR", "plc_conversion_rate": 1.0
            })
            si.set_missing_values()
            si.calculate_taxes_and_totals()
            si.flags.ignore_validate = True
            si.insert().submit()
            si.reload()
            
            if random.random() < 0.7:
                amt = si.outstanding_amount
                pe = frappe.get_doc({
                    "doctype": "Payment Entry", "payment_type": "Receive", "company": company, "posting_date": txn_date,
                    "party_type": "Customer", "party": cust["name"], "paid_to": bank_account, "paid_from": si.debit_to,
                    "paid_amount": amt, "received_amount": amt,
                    "reference_no": f"REC-{si.name}", "reference_date": txn_date,
                    "references": [{"reference_doctype": "Sales Invoice", "reference_name": si.name, "allocated_amount": amt}]
                })
                pe.set_missing_values()
                pe.insert().submit()

        frappe.db.commit()
        current_date = add_months(current_date, 1)

    print("\n🎉 Transaction Generation Complete")

if __name__ == "__main__":
    setup_transactions()

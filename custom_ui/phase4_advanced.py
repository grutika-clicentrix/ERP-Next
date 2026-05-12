import frappe
from frappe.utils import add_days, getdate, flt
import random

def run_phase4():
    company = "Wood Craft Furniture Pvt. Ltd."
    abbr = "WCFPL"
    bank_account = f"WCFPL Current Account - HDFC - {abbr}"
    
    # 1. Map Sales Persons to Territories
    person_map = {
        "Delhi NCR Executive": "Delhi NCR",
        "Rajasthan Executive": "Rajasthan",
        "UP & Uttarakhand Executive": "Uttar Pradesh",
        "Karnataka Executive": "Karnataka",
        "Tamil Nadu Executive": "Tamil Nadu",
        "Gujarat Executive": "Gujarat",
        "Goa & MP Executive": "Goa",
        "West Bengal Executive": "West Bengal",
        "Odisha Executive": "Odisha",
        "Mumbai Executive": "Mumbai Metropolitan",
        "Pune & Nash Executive": "Pune Region"
    }

    # 2. Update Sales Invoices with Sales Persons
    print("Attributing Sales Team to Invoices...")
    sales_invoices = frappe.get_all("Sales Invoice", filters={"docstatus": 1, "company": company}, fields=["name", "customer"])
    for si_name in [si["name"] for si in sales_invoices]:
        cust_territory = frappe.db.get_value("Customer", frappe.db.get_value("Sales Invoice", si_name, "customer"), "territory")
        sales_person = "Sales Team"
        for p, t in person_map.items():
            if t in str(cust_territory):
                sales_person = p
                break
        
        if not frappe.db.exists("Sales Team", {"parent": si_name}):
            frappe.db.sql(f"""insert into `tabSales Team` (name, parent, parenttype, parentfield, sales_person, allocated_percentage) 
                          values ('{frappe.generate_hash(length=10)}', '{si_name}', 'Sales Invoice', 'sales_team', '{sales_person}', 100)""")
    frappe.db.commit()

    # 3. Generate Returns
    print("Generating Returns...")
    to_return_si = random.sample(sales_invoices, min(20, len(sales_invoices)))
    for si_item in to_return_si:
        si = frappe.get_doc("Sales Invoice", si_item["name"])
        try:
            sn = frappe.get_doc({
                "doctype": "Sales Invoice", "is_return": 1, "return_against": si.name, "company": company,
                "customer": si.customer, "posting_date": add_days(si.posting_date, random.randint(2, 10)),
                "items": [{"item_code": item.item_code, "qty": -1, "rate": item.rate, "uom": item.uom, "conversion_factor": 1, "income_account": item.income_account} for item in si.items[:1]]
            })
            sn.flags.ignore_validate = True
            sn.insert().submit()
        except: pass

    # 4. Depreciation
    print("Processing Asset Depreciation...")
    assets = frappe.get_all("Asset", filters={"docstatus": 1, "company": company})
    for asset_item in assets:
        asset = frappe.get_doc("Asset", asset_item["name"])
        try:
            frappe.get_doc({
                "doctype": "Journal Entry", "company": company, "posting_date": "2026-03-31",
                "voucher_type": "Depreciation Entry",
                "accounts": [
                    {"account": f"Depreciation - {abbr}", "debit_in_account_currency": flt(asset.gross_purchase_amount * 0.1)},
                    {"account": f"Accumulated Depreciation - {abbr}", "credit_in_account_currency": flt(asset.gross_purchase_amount * 0.1)}
                ],
                "user_remark": f"Annual Depreciation for {asset.name}"
            }).insert().submit()
        except Exception as e:
            print(f"Depreciation failed for {asset.name}: {e}")

    # 5. Bad Debts
    print("Simulating Bad Debts...")
    bad_si = random.sample(sales_invoices, min(5, len(sales_invoices)))
    for si_item in bad_si:
        si = frappe.get_doc("Sales Invoice", si_item["name"])
        si.reload()
        if si.outstanding_amount > 0:
            try:
                frappe.get_doc({
                    "doctype": "Journal Entry", "company": company, "posting_date": "2026-03-31",
                    "accounts": [
                        {"account": f"Bad Debts Written Off - {abbr}", "debit_in_account_currency": si.outstanding_amount},
                        {"account": si.debit_to, "party_type": "Customer", "party": si.customer, "credit_in_account_currency": si.outstanding_amount}
                    ],
                    "user_remark": f"Write off for {si.name}"
                }).insert().submit()
            except: pass

    # 6. GST Settlement
    print("GST Settlement...")
    for m in range(4, 13):
        date = f"2025-{m:02d}-20"
        try:
            frappe.get_doc({
                "doctype": "Journal Entry", "company": company, "posting_date": date,
                "accounts": [
                    {"account": f"GST Payable - {abbr}", "debit_in_account_currency": 50000},
                    {"account": bank_account, "credit_in_account_currency": 50000}
                ],
                "user_remark": f"GST Payment for Month {m}"
            }).insert().submit()
        except: pass

    frappe.db.commit()
    print("\n🎉 Phase 4 Advanced Scenarios Complete")

if __name__ == "__main__":
    run_phase4()

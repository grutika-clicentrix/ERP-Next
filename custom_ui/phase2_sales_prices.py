import frappe
from frappe import _

def setup_phase2():
    company_doc = frappe.get_doc("Company", "Wood Craft Furniture Pvt. Ltd.")
    company = company_doc.name
    abbr = company_doc.abbr
    comp_curr = company_doc.default_currency

    # 0. Fiscal Years
    fys = [
        ("2022-2023", "2022-04-01", "2023-03-31"),
        ("2023-2024", "2023-04-01", "2024-03-31"),
        ("2024-2025", "2024-04-01", "2025-03-31"),
        ("2025-2026", "2025-04-01", "2026-03-31"),
    ]
    for fy_name, start, end in fys:
        if not frappe.db.exists("Fiscal Year", fy_name):
            frappe.get_doc({"doctype": "Fiscal Year", "year": fy_name, "year_start_date": start, "year_end_date": end}).insert()

    # 1. Sales Team
    sales_tree = [
        ("Sales Director", None, 1, 0), ("North Zone Manager", "Sales Director", 1, 1),
        ("South & West Zone Manager", "Sales Director", 1, 1), ("East & Central Zone Manager", "Sales Director", 1, 1),
        ("Delhi NCR Executive", "North Zone Manager", 0, 2), ("Rajasthan Executive", "North Zone Manager", 0, 2),
        ("UP & Uttarakhand Executive", "North Zone Manager", 0, 2), ("Karnataka Executive", "South & West Zone Manager", 0, 2),
        ("Tamil Nadu Executive", "South & West Zone Manager", 0, 2), ("Gujarat Executive", "South & West Zone Manager", 0, 2),
        ("Goa & MP Executive", "South & West Zone Manager", 0, 2), ("West Bengal Executive", "East & Central Zone Manager", 0, 2),
        ("Odisha Executive", "East & Central Zone Manager", 0, 2), ("Mumbai Executive", "South & West Zone Manager", 0, 2),
        ("Pune & Nash Executive", "South & West Zone Manager", 0, 2),
    ]
    for sp_name, parent, is_group, comm in sales_tree:
        if not frappe.db.exists("Sales Person", sp_name):
            frappe.get_doc({"doctype": "Sales Person", "sales_person_name": sp_name, "parent_sales_person": parent or "Sales Team", "is_group": is_group, "commission_rate": comm, "enabled": 1}).insert()

    # 2. Assign Sales Persons
    exec_territory_map = {
        "Delhi NCR": "Delhi NCR Executive", "Rajasthan": "Rajasthan Executive", "Punjab & Haryana": "UP & Uttarakhand Executive",
        "Uttar Pradesh": "UP & Uttarakhand Executive", "Himachal & Uttarakhand": "UP & Uttarakhand Executive", "Tamil Nadu": "Tamil Nadu Executive",
        "Karnataka": "Karnataka Executive", "Telangana & Andhra Pradesh": "Karnataka Executive", "Kerala": "Tamil Nadu Executive",
        "West Bengal": "West Bengal Executive", "Odisha": "Odisha Executive", "Bihar & Jharkhand": "West Bengal Executive",
        "North East India": "Odisha Executive", "Gujarat": "Gujarat Executive", "Goa": "Goa & MP Executive", "Madhya Pradesh": "Goa & MP Executive",
        "Chhattisgarh": "Goa & MP Executive", "Mumbai Metropolitan": "Mumbai Executive", "Pune Region": "Pune & Nash Executive",
        "Nashik & Aurangabad": "Pune & Nash Executive", "Rest of Maharashtra": "Pune & Nash Executive", "Middle East": "Delhi NCR Executive",
        "Southeast Asia": "West Bengal Executive", "Europe": "Delhi NCR Executive", "Americas": "Delhi NCR Executive",
    }
    for c in frappe.get_all("Customer", fields=["name", "territory"]):
        sp = exec_territory_map.get(c.territory or "")
        if sp:
            cust_doc = frappe.get_doc("Customer", c.name)
            if not cust_doc.sales_team:
                cust_doc.append("sales_team", {"sales_person": sp, "allocated_percentage": 100})
                cust_doc.save()

    # 3. Item Prices
    item_prices = [
        ("WOODEN-CHAIR", 12000, 6500), ("DINING-TABLE", 65000, 32000), ("Office Table", 18000, 9000), ("Study Table", 14000, 7000),
        ("Coffee Table", 9000, 4500), ("Queen Size Bed", 55000, 27000), ("King Size Bed", 72000, 35000), ("Wardrobe 2-Door", 38000, 18500),
        ("Wardrobe 3-Door", 48000, 23500), ("Nightstand", 8500, 4200), ("Bookshelf Large", 22000, 11000), ("Bookshelf Small", 12000, 6000),
        ("Sofa 3-Seater", 38000, 19000), ("Sofa Single", 18000, 9000), ("TV Unit", 16000, 8000), ("Kitchen Cabinet Upper", 14000, 7000),
        ("Kitchen Cabinet Lower", 16000, 8000), ("Shoe Rack", 6000, 3000), ("Office Chair Executive", 22000, 11000), ("Office Chair Basic", 9500, 4750),
        ("Dining Chair Set of 4", 24000, 12000), ("Wall Shelf", 3500, 1750), ("Dressing Table", 19000, 9500),
    ]
    for item_code, sell_price, buy_price in item_prices:
        if not frappe.db.exists("Item", item_code): continue
        if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": "Standard Selling"}):
            frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": "Standard Selling", "price_list_rate": sell_price, "currency": comp_curr}).insert()
        if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": "Standard Buying"}):
            frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": "Standard Buying", "price_list_rate": buy_price, "currency": comp_curr}).insert()

    # 4. Fixed Assets - Step 1: Category
    if not frappe.db.exists("Location", "Factory - Pune"):
        frappe.get_doc({"doctype": "Location", "location_name": "Factory - Pune"}).insert()

    dep_method = "Straight Line"
    asset_categories = [
        {"name": "Plant and Machinery", "acc": f"Plants and Machineries - {abbr}", "total": 10},
        {"name": "Buildings", "acc": f"Buildings - {abbr}", "total": 20},
        {"name": "Office Equipment", "acc": f"Office Equipments - {abbr}", "total": 5},
    ]
    for cat in asset_categories:
        if not frappe.db.exists("Asset Category", cat["name"]):
            doc = frappe.get_doc({
                "doctype": "Asset Category", "asset_category_name": cat["name"], "depreciation_method": dep_method,
                "total_number_of_depreciations": cat["total"], "frequency_of_depreciation": 12,
                "accounts": [{"company_name": company, "fixed_asset_account": cat["acc"], "accumulated_depreciation_account": f"Accumulated Depreciation - {abbr}", "depreciation_expense_account": f"Depreciation - {abbr}"}]
            })
            doc.flags.ignore_validate = True
            doc.insert()

    # Fixed Assets - Step 2: Items
    asset_items = [
        {"code": "CNC Router Machine", "cat": "Plant and Machinery"},
        {"code": "Factory Building", "cat": "Buildings"},
        {"code": "Delivery Vehicle", "cat": "Office Equipment"}
    ]
    for ai in asset_items:
        if not frappe.db.exists("Item", ai["code"]):
            frappe.get_doc({
                "doctype": "Item", "item_code": ai["code"], "item_name": ai["code"], "item_group": "All Item Groups", "is_fixed_asset": 1, "is_stock_item": 0, "asset_category": ai["cat"]
            }).insert()

    # Fixed Assets - Step 3: Assets
    assets = [
        {"name": "CNC Router Machine Asset", "item": "CNC Router Machine", "cat": "Plant and Machinery", "date": "2024-04-01", "amt": 1800000, "total_dep": 10},
        {"name": "Factory Building Asset", "item": "Factory Building", "cat": "Buildings", "date": "2022-04-01", "amt": 4500000, "total_dep": 20},
        {"name": "Delivery Vehicle Asset", "item": "Delivery Vehicle", "cat": "Office Equipment", "date": "2023-10-01", "amt": 850000, "total_dep": 5},
    ]
    for a in assets:
        if frappe.db.exists("Asset Category", a["cat"]) and not frappe.db.exists("Asset", a["name"]):
            doc = frappe.get_doc({
                "doctype": "Asset", "asset_name": a["name"], "item_code": a["item"], "asset_category": a["cat"], "company": company, "purchase_date": a["date"], "gross_purchase_amount": a["amt"],
                "calculate_depreciation": 1, "available_for_use_date": a["date"], "location": "Factory - Pune", "cost_center": f"Main - {abbr}",
                "finance_books": [{
                    "depreciation_method": dep_method,
                    "total_number_of_depreciations": a["total_dep"],
                    "frequency_of_depreciation": 12,
                    "depreciation_start_date": a["date"]
                }]
            })
            doc.flags.ignore_validate = True
            doc.insert().submit()

    # 5. Opening Bank & Stock
    bank_account = f"WCFPL Current Account - HDFC - {abbr}"
    if not frappe.db.exists("Journal Entry", {"cheque_no": "OPENING-BANK-001"}):
        frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Opening Entry", "posting_date": "2025-04-01", "company": company, "cheque_no": "OPENING-BANK-001", "cheque_date": "2025-04-01", "accounts": [{"account": bank_account, "debit_in_account_currency": 5000000, "cost_center": f"Main - {abbr}"}, {"account": f"Opening Balance Equity - {abbr}", "credit_in_account_currency": 5000000, "cost_center": f"Main - {abbr}"}]}).insert().submit()

    if not frappe.db.exists("Stock Entry", {"remarks": "OPENING-STOCK-001"}):
        se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": company, "posting_date": "2025-04-01", "remarks": "OPENING-STOCK-001", "to_warehouse": f"Stores - {abbr}", "items": []})
        for item_code, qty, rate in [("Wood Plank", 500, 800), ("SCREW", 10000, 5), ("POLISH", 200, 450), ("Fabric", 100, 650), ("Foam", 80, 1200), ("Glue", 150, 280), ("Metal Handle", 300, 180)]:
            if frappe.db.exists("Item", item_code): se.append("items", {"item_code": item_code, "qty": qty, "basic_rate": rate, "t_warehouse": f"Stores - {abbr}"})
        se.insert().submit()

    frappe.db.commit()
    print("\n🎉 Phase 2 Complete")

if __name__ == "__main__":
    setup_phase2()

import frappe

def audit():
    print("=== EXISTING MASTER DATA AUDIT ===")
    
    print("\n--- Companies ---")
    for c in frappe.get_all("Company", fields=["name", "abbr", "default_currency", "country"]):
        print(f"  {c.name} | {c.abbr} | {c.default_currency}")

    print("\n--- Fiscal Years ---")
    for f in frappe.get_all("Fiscal Year", fields=["name", "year_start_date", "year_end_date"]):
        print(f"  {f.name}: {f.year_start_date} to {f.year_end_date}")

    print("\n--- Customer Groups ---")
    for g in frappe.get_all("Customer Group", fields=["name"]):
        print(f"  {g.name}")

    print("\n--- Supplier Groups ---")
    for g in frappe.get_all("Supplier Group", fields=["name"]):
        print(f"  {g.name}")

    print("\n--- Item Groups ---")
    for g in frappe.get_all("Item Group", fields=["name"]):
        print(f"  {g.name}")

    print("\n--- Finished Goods Items ---")
    for i in frappe.get_all("Item", filters={"item_group": "Finished Goods"}, fields=["name", "item_group"]):
        print(f"  {i.name}")

    print("\n--- Raw Material Items ---")
    for i in frappe.get_all("Item", filters={"item_group": ["in", ["Raw Material","Consumable"]]}, fields=["name","item_group"]):
        print(f"  {i.name} ({i.item_group})")

    print("\n--- Accounts (Key Ones) ---")
    for a in frappe.get_all("Account", filters={"company": "Wood Craft Furniture Pvt. Ltd."}, fields=["name","account_type","root_type"], limit=30):
        print(f"  {a.name} | {a.root_type} | {a.account_type}")

    print("\n--- Existing Sales Tax Templates ---")
    for t in frappe.get_all("Sales Taxes and Charges Template", fields=["name"]):
        print(f"  {t.name}")

    print("\n--- Existing Purchase Tax Templates ---")
    for t in frappe.get_all("Purchase Taxes and Charges Template", fields=["name"]):
        print(f"  {t.name}")

    print("\n--- Warehouses ---")
    for w in frappe.get_all("Warehouse", filters={"company": "Wood Craft Furniture Pvt. Ltd."}, fields=["name"]):
        print(f"  {w.name}")

    print("\n--- Existing Price Lists ---")
    for p in frappe.get_all("Price List", fields=["name", "currency"]):
        print(f"  {p.name}")

    print("\n--- Existing Territories ---")
    for t in frappe.get_all("Territory", fields=["name"]):
        print(f"  {t.name}")

    print("\n--- Existing Customers (count) ---")
    print(f"  Total: {frappe.db.count('Customer')}")
    
    print("\n--- Existing Suppliers (count) ---")
    print(f"  Total: {frappe.db.count('Supplier')}")
    
    print("\n--- Existing BOMs ---")
    for b in frappe.get_all("BOM", filters={"is_active": 1}, fields=["name","item"]):
        print(f"  {b.name} -> {b.item}")

    print("\n--- Payment Terms ---")
    for p in frappe.get_all("Payment Terms Template", fields=["name"]):
        print(f"  {p.name}")

    print("\n--- Modes of Payment ---")
    for m in frappe.get_all("Mode of Payment", fields=["name"]):
        print(f"  {m.name}")

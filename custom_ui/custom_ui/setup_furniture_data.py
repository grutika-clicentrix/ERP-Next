
import frappe
from frappe import _
import random
from datetime import datetime, timedelta

def run():
    company = "Clicentrix"
    abbr = "Cx"
    
    # 1. Create Item Groups
    item_groups = ["Raw Material", "Finished Good", "Sub Assembly"]
    for group in item_groups:
        if not frappe.db.exists("Item Group", group):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": group,
                "parent_item_group": "All Item Groups",
                "is_group": 0
            }).insert()
            print(f"Created Item Group: {group}")

    # 2. Create Warehouses
    warehouses = [
        {"warehouse_name": "Finished Goods", "parent_warehouse": f"All Warehouses - {abbr}"},
        {"warehouse_name": "Raw Materials", "parent_warehouse": f"All Warehouses - {abbr}"}
    ]
    for wh in warehouses:
        wh_name = f"{wh['warehouse_name']} - {abbr}"
        if not frappe.db.exists("Warehouse", wh_name):
            frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": wh["warehouse_name"],
                "parent_warehouse": wh["parent_warehouse"],
                "company": company
            }).insert()
            print(f"Created Warehouse: {wh_name}")

    # 3. Create Items
    items = [
        {"item_code": "WOOD-001", "item_name": "Teak Wood", "item_group": "Raw Material", "is_stock_item": 1, "stock_uom": "Nos"},
        {"item_code": "SCREW-001", "item_name": "Wood Screws", "item_group": "Raw Material", "is_stock_item": 1, "stock_uom": "Nos"},
        {"item_code": "GLUE-001", "item_name": "Wood Glue", "item_group": "Raw Material", "is_stock_item": 1, "stock_uom": "Kg"},
        {"item_code": "CHAIR-001", "item_name": "Wooden Office Chair", "item_group": "Finished Good", "is_stock_item": 1, "stock_uom": "Nos", "standard_rate": 150.0},
        {"item_code": "TABLE-001", "item_name": "Dining Table", "item_group": "Finished Good", "is_stock_item": 1, "stock_uom": "Nos", "standard_rate": 500.0}
    ]
    for item in items:
        if not frappe.db.exists("Item", item["item_code"]):
            doc = frappe.get_doc({
                "doctype": "Item",
                **item
            })
            doc.insert()
            print(f"Created Item: {item['item_code']}")
        else:
            frappe.db.set_value("Item", item["item_code"], "stock_uom", item["stock_uom"])

    # 4. Create Workstations
    workstations = ["Cutting Station", "Assembly Station", "Finishing Station"]
    for ws in workstations:
        if not frappe.db.exists("Workstation", ws):
            frappe.get_doc({
                "doctype": "Workstation",
                "workstation_name": ws,
                "hour_rate": 20.0
            }).insert()
            print(f"Created Workstation: {ws}")

    if not frappe.db.exists("UOM", "Kg"):
        frappe.get_doc({"doctype": "UOM", "uom_name": "Kg", "must_be_whole_number": 0}).insert()
    else:
        frappe.db.set_value("UOM", "Kg", "must_be_whole_number", 0)

    # 5. Create BOM for Wooden Office Chair
    bom_name = "BOM-CHAIR-001-001"
    if not frappe.db.exists("BOM", bom_name):
        bom = frappe.get_doc({
            "doctype": "BOM",
            "item": "CHAIR-001",
            "quantity": 1,
            "company": company,
            "is_active": 1,
            "is_default": 1,
            "items": [
                {"item_code": "WOOD-001", "qty": 4, "uom": "Nos"},
                {"item_code": "SCREW-001", "qty": 10, "uom": "Nos"},
                {"item_code": "GLUE-001", "qty": 0.5, "uom": "Kg"}
            ]
        })
        bom.insert()
        bom.submit()
        print(f"Created and Submitted BOM: {bom_name}")

    # 6. Create Suppliers and Customers
    suppliers = ["Timber Mart", "Hardware Hub"]
    for sup in suppliers:
        if not frappe.db.exists("Supplier", sup):
            frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": sup,
                "supplier_group": "Local"
            }).insert()
            print(f"Created Supplier: {sup}")

    # 7. Invoices
    if not frappe.db.exists("Purchase Invoice", {"supplier": "Timber Mart", "company": company}):
        pi = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": "Timber Mart",
            "company": company,
            "posting_date": frappe.utils.today(),
            "items": [
                {"item_code": "WOOD-001", "qty": 100, "rate": 10, "expense_account": f"Cost of Goods Sold - {abbr}"}
            ]
        })
        pi.insert()
        pi.submit()
        print("Created and Submitted Purchase Invoice for Timber Mart")

    # 8. Bulk & Realistic Data
    realistic_customers = ["Ashley Furniture Industries", "IKEA India", "Godrej Interio", "Nilkamal Ltd", "Pepperfry", "Urban Ladder", "Hometown Furnishings", "Durian Furniture"]
    for cust_name in realistic_customers:
        if not frappe.db.exists("Customer", cust_name):
            frappe.get_doc({
                "doctype": "Customer",
                "customer_name": cust_name,
                "customer_group": "Commercial",
                "territory": "All Territories"
            }).insert()
            print(f"Created Realistic Customer: {cust_name}")

    print("Generating bulk sales orders...")
    fg_items = frappe.get_all("Item", filters={"item_group": "Finished Good"}, limit=5)
    for cust_name in realistic_customers:
        if not frappe.db.exists("Sales Order", {"customer": cust_name, "company": company}):
            item = random.choice(fg_items)
            so = frappe.get_doc({
                "doctype": "Sales Order",
                "customer": cust_name,
                "company": company,
                "transaction_date": frappe.utils.today(),
                "delivery_date": frappe.utils.add_days(frappe.utils.today(), 7),
                "items": [
                    {
                        "item_code": item.name,
                        "qty": random.randint(5, 20),
                        "rate": 250,
                        "warehouse": f"Finished Goods - {abbr}"
                    }
                ]
            })
            so.insert()
            so.submit()
            print(f"Created and Submitted Sales Order for {cust_name}")

    frappe.db.commit()

if __name__ == "__main__":
    run()

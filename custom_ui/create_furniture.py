import frappe
from frappe import _

def create_furniture_data():
    # 1. Ensure UOMs exist
    required_uoms = ["Nos", "Unit", "Litre", "Metre"]
    for uom in required_uoms:
        if not frappe.db.exists("UOM", uom):
            frappe.get_doc({
                "doctype": "UOM",
                "uom_name": uom,
                "must_be_whole_number": 0 if uom in ["Litre", "Metre"] else 1
            }).insert()

    # 2. Ensure Item Groups exist
    groups = ["Finished Goods", "Raw Material", "Consumable"]
    for g in groups:
        if not frappe.db.exists("Item Group", g):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": g,
                "parent_item_group": "All Item Groups",
                "is_group": 0
            }).insert()
    
    # 3. Ensure basic Raw Materials exist
    raw_materials = {
        "Wood Plank": "Raw Material",
        "SCREW": "Raw Material",
        "POLISH": "Raw Material",
        "Glue": "Consumable",
        "Fabric": "Raw Material",
        "Foam": "Raw Material",
        "Metal Handle": "Raw Material",
        "Varnish": "Consumable"
    }
    
    uom_map = {
        "POLISH": "Litre",
        "Glue": "Nos",
        "SCREW": "Nos",
        "Metal Handle": "Nos",
        "Wood Plank": "Nos",
        "Varnish": "Litre",
        "Fabric": "Metre",
        "Foam": "Nos"
    }
    
    for rm_name, rm_group in raw_materials.items():
        if not frappe.db.exists("Item", rm_name):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": rm_name,
                "item_name": rm_name,
                "item_group": rm_group,
                "is_stock_item": 1,
                "stock_uom": uom_map.get(rm_name, "Nos")
            }).insert()

    # 4. Define Finished Goods
    finished_goods = {
        "Study Table": [("Wood Plank", 5), ("SCREW", 20), ("POLISH", 1), ("Glue", 1)],
        "Coffee Table": [("Wood Plank", 3), ("SCREW", 12), ("POLISH", 1), ("Glue", 1)],
        "Bookshelf Large": [("Wood Plank", 10), ("SCREW", 40), ("POLISH", 2), ("Glue", 2)],
        "Bookshelf Small": [("Wood Plank", 4), ("SCREW", 16), ("POLISH", 1), ("Glue", 1)],
        "Wardrobe 2-Door": [("Wood Plank", 15), ("SCREW", 60), ("POLISH", 3), ("Metal Handle", 2)],
        "Wardrobe 3-Door": [("Wood Plank", 22), ("SCREW", 80), ("POLISH", 4), ("Metal Handle", 3)],
        "Queen Size Bed": [("Wood Plank", 20), ("SCREW", 50), ("POLISH", 3), ("Glue", 2)],
        "King Size Bed": [("Wood Plank", 25), ("SCREW", 60), ("POLISH", 4), ("Glue", 3)],
        "Nightstand": [("Wood Plank", 3), ("SCREW", 10), ("POLISH", 1), ("Metal Handle", 1)],
        "Sofa 3-Seater": [("Wood Plank", 8), ("Fabric", 10), ("Foam", 5), ("SCREW", 20)],
        "Sofa Single": [("Wood Plank", 4), ("Fabric", 4), ("Foam", 2), ("SCREW", 10)],
        "TV Unit": [("Wood Plank", 8), ("SCREW", 30), ("POLISH", 2), ("Metal Handle", 2)],
        "Kitchen Cabinet Upper": [("Wood Plank", 6), ("SCREW", 24), ("POLISH", 1), ("Metal Handle", 2)],
        "Kitchen Cabinet Lower": [("Wood Plank", 8), ("SCREW", 24), ("POLISH", 1), ("Metal Handle", 2)],
        "Shoe Rack": [("Wood Plank", 5), ("SCREW", 20), ("POLISH", 1)],
        "Office Chair Executive": [("Wood Plank", 2), ("Fabric", 3), ("Foam", 2), ("SCREW", 15)],
        "Office Chair Basic": [("Wood Plank", 1), ("Fabric", 2), ("Foam", 1), ("SCREW", 10)],
        "Dining Chair Set of 4": [("Wood Plank", 8), ("SCREW", 32), ("POLISH", 2)],
        "Wall Shelf": [("Wood Plank", 2), ("SCREW", 4), ("POLISH", 1)],
        "Dressing Table": [("Wood Plank", 10), ("SCREW", 30), ("POLISH", 2), ("Metal Handle", 3)]
    }

    company = frappe.db.get_value("Company", {"company_name": "Wood Craft Furniture Pvt. Ltd."}, "name") or frappe.get_all("Company", limit=1)[0].name

    for fg_name, components in finished_goods.items():
        if not frappe.db.exists("Item", fg_name):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": fg_name,
                "item_name": fg_name,
                "item_group": "Finished Goods",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            }).insert()

        if not frappe.db.exists("BOM", {"item": fg_name}):
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": fg_name,
                "quantity": 1,
                "company": company,
                "is_active": 1,
                "is_default": 1,
                "items": []
            })
            for comp_name, qty in components:
                bom.append("items", {
                    "item_code": comp_name,
                    "qty": qty,
                    "uom": frappe.db.get_value("Item", comp_name, "stock_uom") or "Nos"
                })
            bom.insert()
            bom.submit()
            print(f"Created {fg_name}")

if __name__ == "__main__":
    create_furniture_data()
    frappe.db.commit()

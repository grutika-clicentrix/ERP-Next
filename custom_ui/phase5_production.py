import frappe
from frappe.utils import add_days, getdate, nowdate
import random

def run_phase5():
    company = "Wood Craft Furniture Pvt. Ltd."
    abbr = "WCFPL"
    warehouse_stores = f"Stores - {abbr}"
    warehouse_fg = f"Finished Goods - {abbr}"
    warehouse_wip = f"Work In Progress - {abbr}"
    
    boms = frappe.get_all("BOM", filters={"docstatus": 1, "is_active": 1}, fields=["name", "item", "uom"])
    
    print(f"Generating Production Data for {len(boms)} items...")
    
    for i in range(20):
        bom_item = random.choice(boms)
        txn_date = add_days("2026-03-01", random.randint(0, 25))
        qty = random.randint(5, 15)
        
        try:
            wo = frappe.get_doc({
                "doctype": "Work Order", "company": company, "bom_no": bom_item["name"], "production_item": bom_item["item"],
                "qty": qty, "planned_start_date": txn_date, "fg_warehouse": warehouse_fg, "wip_warehouse": warehouse_wip,
                "skip_transfer": 0
            })
            wo.insert().submit()
            
            se_transfer = frappe.get_doc({
                "doctype": "Stock Entry", "stock_entry_type": "Material Transfer for Manufacture", "work_order": wo.name,
                "company": company, "posting_date": txn_date, "from_warehouse": warehouse_stores, "to_warehouse": warehouse_wip
            })
            se_transfer.set_missing_values()
            se_transfer.items = []
            for item in wo.required_items:
                se_transfer.append("items", {
                    "item_code": item.item_code, "qty": item.required_qty, "s_warehouse": warehouse_stores, "t_warehouse": warehouse_wip,
                    "uom": item.stock_uom, "conversion_factor": 1
                })
            se_transfer.insert().submit()
            
            se_finish = frappe.get_doc({
                "doctype": "Stock Entry", "stock_entry_type": "Manufacture", "work_order": wo.name,
                "company": company, "posting_date": add_days(txn_date, 2), "from_warehouse": warehouse_wip, "to_warehouse": warehouse_fg,
                "fg_completed_qty": qty, "from_bom": 1, "bom_no": bom_item["name"]
            })
            se_finish.flags.ignore_mandatory = True # Force
            se_finish.items = []
            se_finish.append("items", {
                "item_code": bom_item["item"], "qty": qty, "t_warehouse": warehouse_fg, "is_finished_item": 1,
                "uom": bom_item["uom"], "conversion_factor": 1
            })
            for item in wo.required_items:
                se_finish.append("items", {
                    "item_code": item.item_code, "qty": item.required_qty, "s_warehouse": warehouse_wip,
                    "uom": item.stock_uom, "conversion_factor": 1
                })
            se_finish.insert().submit()
            
            wo.db_set("status", "Completed")
            
        except Exception as e:
            print(f"Failed to process WO for {bom_item['item']}: {e}")

    frappe.db.commit()
    print("\n🎉 Phase 5 Production Data Complete")

if __name__ == "__main__":
    run_phase5()

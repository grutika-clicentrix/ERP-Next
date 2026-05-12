import frappe
import random

def create_generic_vendors():
    # Ensure a basic Supplier Group exists
    if not frappe.db.exists("Supplier Group", "General"):
        frappe.get_doc({
            "doctype": "Supplier Group",
            "supplier_group_name": "General"
        }).insert()
    
    prefixes = ["Global", "Universal", "Apex", "Premier", "Elite", "Standard", "Choice", "Prime", "Direct", "Reliable"]
    types = ["Solutions", "Supplies", "Trading", "Industries", "Ventures", "Partners", "Systems", "Resources", "Logistics", "Enterprises"]
    suffixes = ["Inc.", "Corp.", "Ltd.", "Group", "LLC"]

    created_count = 0
    for i in range(1, 41):
        # Generate a generic name
        name = f"{random.choice(prefixes)} {random.choice(types)} {i:02d}"
        
        if not frappe.db.exists("Supplier", name):
            vendor = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": name,
                "supplier_group": "General",
                "supplier_type": "Company"
            })
            vendor.insert()
            created_count += 1
            print(f"Created Vendor: {name}")

    frappe.db.commit()
    print(f"\nSuccessfully created {created_count} vendors.")

if __name__ == "__main__":
    create_generic_vendors()

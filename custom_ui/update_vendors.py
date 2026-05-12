import frappe
import random

def update_generic_vendors_with_data():
    suppliers = frappe.get_all("Supplier", filters={"supplier_group": "General"}, fields=["name", "supplier_name"])
    
    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Pune"]
    
    for i, s in enumerate(suppliers, 1):
        # 1. Update Tax ID on Supplier
        tax_id = f"TAX{random.randint(100000, 999999)}{i:02d}"
        frappe.db.set_value("Supplier", s.name, "tax_id", tax_id)
        
        # 2. Add Address
        address_name = f"{s.name}-Address"
        if not frappe.db.exists("Address", address_name):
            addr = frappe.get_doc({
                "doctype": "Address",
                "address_title": s.name,
                "address_type": "Billing",
                "address_line1": f"Street {random.randint(1, 100)}, Industrial Area Phase {random.randint(1, 5)}",
                "city": random.choice(cities),
                "country": "India",
                "links": [
                    {
                        "link_doctype": "Supplier",
                        "link_name": s.name
                    }
                ]
            })
            addr.insert()
        
        # 3. Add Contact
        contact_name = f"{s.name}-Contact"
        if not frappe.db.exists("Contact", {"email_id": f"contact{i:02d}@example.com"}):
            contact = frappe.get_doc({
                "doctype": "Contact",
                "first_name": f"Manager {i:02d}",
                "email_id": f"contact{i:02d}@{s.name.replace(' ', '').lower()}.com",
                "status": "Passive",
                "links": [
                    {
                        "link_doctype": "Supplier",
                        "link_name": s.name
                    }
                ]
            })
            contact.insert()
            
        print(f"Updated {s.name} with Address, Contact, and Tax ID.")

    frappe.db.commit()
    print("\nSuccessfully updated all vendors with generic data.")

if __name__ == "__main__":
    update_generic_vendors_with_data()

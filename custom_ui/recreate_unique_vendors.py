import frappe
import random

def recreate_unique_vendors():
    # 1. Identify and Delete old vendors (the ones with numbers in them from the previous run)
    old_vendors = frappe.get_all("Supplier", filters={"supplier_group": "General"})
    for v in old_vendors:
        # Delete linked Address and Contact first to avoid orphan data
        links = frappe.get_all("Dynamic Link", filters={"link_doctype": "Supplier", "link_name": v.name}, fields=["parent", "parenttype"])
        for link in links:
            try:
                frappe.delete_doc(link.parenttype, link.parent)
            except:
                pass
        try:
            frappe.delete_doc("Supplier", v.name)
        except:
            pass
    
    # 2. Define unique combinations
    prefixes = ["Global", "Apex", "Premier", "Elite", "Standard", "Choice", "Prime", "Direct", "Reliable", "Zenith", 
                "Alpha", "Omega", "Stellar", "Infinity", "Vision", "Smart", "Core", "Pure", "Bright", "Fast"]
    types = ["Solutions", "Supplies", "Trading", "Industries", "Ventures", "Partners", "Systems", "Resources", "Logistics", "Enterprises", 
             "Corp", "Group", "Ltd", "Holdings", "Labs", "Works", "Mills", "Fabricators", "Dynamics", "Synergy"]
    
    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Pune", "Surat", "Jaipur"]
    
    unique_names = set()
    while len(unique_names) < 40:
        name = f"{random.choice(prefixes)} {random.choice(types)}"
        unique_names.add(name)
    
    # 3. Create new vendors with full data
    created_count = 0
    for i, name in enumerate(list(unique_names), 1):
        if not frappe.db.exists("Supplier", name):
            # Create Supplier
            vendor = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": name,
                "supplier_group": "General",
                "supplier_type": "Company",
                "tax_id": f"TAX{random.randint(100000, 999999)}{random.randint(10, 99)}"
            })
            vendor.insert()
            
            # Create Address
            addr = frappe.get_doc({
                "doctype": "Address",
                "address_title": name,
                "address_type": "Billing",
                "address_line1": f"Plot No {random.randint(100, 999)}, Sector {random.randint(1, 20)}",
                "city": random.choice(cities),
                "country": "India",
                "links": [{"link_doctype": "Supplier", "link_name": name}]
            })
            addr.insert()
            
            # Create Contact
            contact = frappe.get_doc({
                "doctype": "Contact",
                "first_name": f"{random.choice(prefixes)} Manager",
                "email_id": f"office@{name.replace(' ', '').lower()}.net",
                "links": [{"link_doctype": "Supplier", "link_name": name}]
            })
            contact.insert()
            
            created_count += 1
            print(f"Created Unique Vendor: {name}")

    frappe.db.commit()
    print(f"\nSuccessfully created {created_count} truly unique vendors with full data.")

if __name__ == "__main__":
    recreate_unique_vendors()

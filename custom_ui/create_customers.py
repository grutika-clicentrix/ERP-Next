import frappe
import random

def create_meaningful_customers():
    # 1. Ensure Customer Groups exist
    groups = ["Retail", "Corporate"]
    for g in groups:
        if not frappe.db.exists("Customer Group", g):
            frappe.get_doc({
                "doctype": "Customer Group",
                "customer_group_name": g,
                "parent_item_group": "All Customer Groups"
            }).insert()
    
    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Pune", "Gurugram", "Noida"]
    
    # 2. Generate 30 Retailers
    ret_prefixes = ["Urban", "Rustic", "Vintage", "Modern", "Elegant", "Royal", "Classic", "Cozy", "Chic", "Grand", "Aesthetic", "Heritage"]
    ret_nouns = ["Furniture", "Decor", "Interiors", "Gallery", "Studio", "Boutique", "Hub", "Oasis", "Haven", "Collection", "Showroom", "Atelier"]
    ret_suffixes = ["Mart", "World", "Zone", "Place", "Spot", "Corner", "Plaza", "Center", "House", "Loft", "Land", "Square"]
    
    unique_retailers = set()
    while len(unique_retailers) < 30:
        name = f"{random.choice(ret_prefixes)} {random.choice(ret_nouns)} {random.choice(ret_suffixes)}"
        unique_retailers.add(name)
    
    # 3. Generate 70 B2B Corporates
    corp_prefixes = ["BlueChip", "Horizon", "Summit", "Nexus", "Infinity", "Global", "Alliance", "Integrity", "Vision", "Precision", "Synergy", "Stellar"]
    corp_nouns = ["Offices", "Co-working", "Realty", "Hotels", "Estates", "Construction", "Architects", "TechPark", "Tower", "Plaza", "Resorts", "Developments"]
    corp_suffixes = ["Group", "Systems", "Solutions", "Services", "Partners", "Corp", "Ltd", "Holdings", "Associates", "International", "Infrastructure", "Consultancy"]
    
    unique_corporates = set()
    while len(unique_corporates) < 70:
        name = f"{random.choice(corp_prefixes)} {random.choice(corp_nouns)} {random.choice(corp_suffixes)}"
        unique_corporates.add(name)
    
    def create_customer_with_data(name, group):
        if not frappe.db.exists("Customer", name):
            # Create Customer
            cust = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": name,
                "customer_group": group,
                "customer_type": "Company" if group == "Corporate" else "Individual",
                "territory": "All Territories"
            })
            cust.insert()
            
            # Create Address
            addr = frappe.get_doc({
                "doctype": "Address",
                "address_title": name,
                "address_type": "Shipping",
                "address_line1": f"Suite {random.randint(101, 999)}, {random.choice(['Furniture Block', 'Design District', 'Business Hub', 'Tech Square'])}",
                "city": random.choice(cities),
                "country": "India",
                "links": [{"link_doctype": "Customer", "link_name": name}]
            })
            addr.insert()
            
            # Create Contact
            contact = frappe.get_doc({
                "doctype": "Contact",
                "first_name": "Procurement" if group == "Corporate" else "Owner",
                "last_name": "Department" if group == "Corporate" else "Desk",
                "email_id": f"hello@{name.replace(' ', '').lower()}.com",
                "links": [{"link_doctype": "Customer", "link_name": name}]
            })
            contact.insert()
            return True
        return False

    count = 0
    for r in unique_retailers:
        if create_customer_with_data(r, "Retail"):
            count += 1
            if count % 10 == 0: print(f"Created {count} customers...")

    for c in unique_corporates:
        if create_customer_with_data(c, "Corporate"):
            count += 1
            if count % 10 == 0: print(f"Created {count} customers...")

    frappe.db.commit()
    print(f"\nSuccessfully created {count} meaningful customers with full data.")

if __name__ == "__main__":
    create_meaningful_customers()

import frappe
from frappe.utils import add_days, add_months, getdate, flt
import random

def run_phase6_simulated():
    company = "Wood Craft Furniture Pvt. Ltd."
    abbr = "WCFPL"
    
    print(f"🚀 Starting Phase 6 Simulation for {company}...")

    # 1. Departments & Designations
    print("Setting up HR Masters (Departments & Designations)...")
    departments = ["Sales", "Production", "HR", "Accounts", "Management", "Logistics", "IT Support"]
    for d_name in departments:
        if not frappe.db.exists("Department", {"department_name": d_name, "company": company}):
            try:
                frappe.get_doc({
                    "doctype": "Department", 
                    "department_name": d_name, 
                    "company": company,
                    "parent_department": "All Departments"
                }).insert(ignore_if_duplicate=True)
            except: pass
            
    designations = ["General Manager", "Sales Manager", "Production Manager", "Accountant", 
                    "Sales Executive", "Factory Worker", "HR Manager", "Logistics Coordinator", "IT Specialist"]
    for d_name in designations:
        if not frappe.db.exists("Designation", d_name):
            try:
                frappe.get_doc({"doctype": "Designation", "designation_name": d_name}).insert(ignore_if_duplicate=True)
            except: pass

    # 2. Create 20 Employees
    print("Creating 20 Employees directly...")
    emp_names = [
        "Aarav Sharma", "Aditi Verma", "Arjun Kapoor", "Ananya Singh", "Ishaan Malhotra", 
        "Kavya Reddy", "Mohan Das", "Nisha Goel", "Rahul Khanna", "Sanya Iyer",
        "Vikram Sethi", "Zoya Khan", "Rohan Joshi", "Priya Mehra", "Amit Bajaj", 
        "Sneha Patil", "Karan Grover", "Meera Nair", "Siddharth Ray", "Tanvi Bose"
    ]
    
    employees = []
    for i, full_name in enumerate(emp_names):
        emp_id = f"EMP-{100+i+1}"
        # Check if exists by employee_number or first_name + last_name
        name_parts = full_name.split()
        f_name = name_parts[0]
        l_name = name_parts[1] if len(name_parts) > 1 else ""
        
        emp_name_in_db = frappe.db.exists("Employee", {"first_name": f_name, "last_name": l_name, "company": company})
        if not emp_name_in_db:
            try:
                emp = frappe.get_doc({
                    "doctype": "Employee", 
                    "employee_number": emp_id, 
                    "first_name": f_name, 
                    "last_name": l_name,
                    "company": company,
                    "gender": random.choice(["Male", "Female"]), 
                    "date_of_birth": "1990-01-01",
                    "date_of_joining": "2024-01-01",
                    "department": frappe.db.get_value("Department", {"department_name": random.choice(departments), "company": company}),
                    "designation": random.choice(designations),
                    "status": "Active"
                })
                emp.insert()
                employees.append(emp.name)
            except Exception as e:
                print(f"  Warning: Could not create employee {full_name}: {e}")
        else:
            employees.append(emp_name_in_db)

    # 3. Ensure Accounting Masters are Ready
    print("Verifying Accounting Masters for Payroll & TDS...")
    salary_expense_acc = f"Salary & Wages - {abbr}"
    salary_payable_acc = f"Salary Payable - {abbr}"
    bank_acc = f"WCFPL Current Account - HDFC - {abbr}"
    tds_payable_acc = f"TDS Payable - {abbr}"
    pt_payable_acc = f"Professional Tax - {abbr}"
    
    # Create PT account if missing
    if not frappe.db.exists("Account", pt_payable_acc):
        try:
            frappe.get_doc({
                "doctype": "Account",
                "account_name": "Professional Tax",
                "parent_account": f"2120 - Duties and Taxes - {abbr}",
                "company": company,
                "root_type": "Liability",
                "is_group": 0
            }).insert()
        except: pass

    # 4. Generate 12 months of Payroll Journal Entries
    print(f"Simulating 12 months of Payroll via Journal Entries for {salary_expense_acc}...")
    # Fiscal Year: April 2024 to March 2025
    for m in range(0, 12):
        # Month End Date
        month_start = getdate(add_months("2024-04-01", m))
        posting_date = getdate(add_days(add_months(month_start, 1), -1))
        
        remark = f"Payroll Accrual for {posting_date.strftime('%B %Y')}"
        print(f"  Processing month {m+1}/12: {posting_date.strftime('%B %Y')}...")
        
        if not frappe.db.exists("Journal Entry", {"remark": remark, "company": company}):
            try:
                # Average salary 45k per emp * 20 = 900,000
                base_salary = 900000 + random.randint(-50000, 50000)
                pt_amount = 200 * 20 # Standard PT in many regions
                net_salary = base_salary - pt_amount
                
                print(f"    Creating Accrual JV for {base_salary}...")
                jv = frappe.get_doc({
                    "doctype": "Journal Entry",
                    "voucher_type": "Journal Entry",
                    "company": company,
                    "posting_date": posting_date,
                    "remark": remark,
                    "accounts": [
                        {
                            "account": salary_expense_acc,
                            "debit_in_account_currency": base_salary,
                            "user_remark": "Monthly Gross Salaries"
                        },
                        {
                            "account": salary_payable_acc,
                            "credit_in_account_currency": net_salary,
                            "user_remark": "Net Salaries Payable"
                        },
                        {
                            "account": pt_payable_acc,
                            "credit_in_account_currency": pt_amount,
                            "user_remark": "PT Deduction"
                        }
                    ]
                })
                jv.insert()
                jv.submit()
                
                # Bank Payment (usually 1st to 7th of next month)
                payment_date = add_days(posting_date, 5)
                print(f"    Creating Payment JV for {net_salary} on {payment_date}...")
                pay_jv = frappe.get_doc({
                    "doctype": "Journal Entry",
                    "voucher_type": "Bank Entry",
                    "company": company,
                    "posting_date": payment_date,
                    "cheque_no": f"SAL-{posting_date.strftime('%m%Y')}",
                    "cheque_date": payment_date,
                    "remark": f"Salary Disbursement for {posting_date.strftime('%B %Y')}",
                    "accounts": [
                        {
                            "account": salary_payable_acc,
                            "debit_in_account_currency": net_salary,
                        },
                        {
                            "account": bank_acc,
                            "credit_in_account_currency": net_salary,
                        }
                    ]
                })
                pay_jv.insert()
                pay_jv.submit()
                print(f"  ✅ Processed {posting_date.strftime('%B %Y')}")
            except Exception as e:
                print(f"  ❌ Error in month {m}: {e}")
                frappe.log_error(f"Payroll Simulation Error Month {m}", frappe.get_traceback())
        else:
            print(f"  ⏭️ Month {posting_date.strftime('%B %Y')} already exists.")

    # 5. TDS (Tax Deducted at Source) Configuration
    print("Setting up TDS (Section 194C)...")
    tds_cat_name = "Section 194C - Contractor - WCFPL"
    if not frappe.db.exists("Tax Withholding Category", tds_cat_name):
        try:
            twc = frappe.get_doc({
                "doctype": "Tax Withholding Category",
                "name": tds_cat_name,
                "category_name": "Section 194C",
                "rates": [{
                    "company": company,
                    "tax_withholding_rate": 2.0,
                    "from_date": "2024-04-01",
                    "to_date": "2025-03-31"
                }],
                "accounts": [{
                    "company": company,
                    "account": tds_payable_acc
                }]
            })
            twc.insert()
        except Exception as e:
            print(f"  Warning: TDS Category creation failed: {e}")

    # Assign TDS to top suppliers (especially 'Local Services' or 'Local Contract Labour')
    suppliers_to_tds = frappe.get_all("Supplier", filters={"supplier_group": ["in", ["Local Services", "Local Contract Labour"]]}, limit=5)
    if not suppliers_to_tds:
        suppliers_to_tds = frappe.get_all("Supplier", limit=5)
        
    for s in suppliers_to_tds:
        frappe.db.set_value("Supplier", s.name, "tax_withholding_category", tds_cat_name)
    print(f"  ✅ Assigned TDS Category to {len(suppliers_to_tds)} suppliers.")

    # 6. Generate Purchase Invoices with TDS
    print("Generating Purchase Invoices with TDS deductions...")
    for i, s in enumerate(suppliers_to_tds):
        inv_date = add_days("2025-01-15", i * 3)
        if not frappe.db.exists("Purchase Invoice", {"supplier": s.name, "posting_date": inv_date}):
            try:
                amount = 75000 + random.randint(0, 50000)
                tds_val = flt(amount * 0.02)
                
                pi = frappe.get_doc({
                    "doctype": "Purchase Invoice",
                    "company": company,
                    "supplier": s.name,
                    "posting_date": inv_date,
                    "items": [{
                        "item_code": "Service Item" if frappe.db.exists("Item", "Service Item") else frappe.get_all("Item", limit=1)[0].name,
                        "qty": 1,
                        "rate": amount,
                        "expense_account": f"Factory Overheads - {abbr}"
                    }],
                    "taxes": [{
                        "charge_type": "Actual",
                        "account_head": tds_payable_acc,
                        "description": "TDS @ 2%",
                        "tax_amount": tds_val,
                        "add_deduct_tax": "Deduct"
                    }]
                })
                pi.insert()
                pi.submit()
                print(f"  ✅ PI {pi.name} created for {s.name} (TDS: {tds_val})")
            except Exception as e:
                print(f"  ❌ PI Error: {e}")

    # 7. TDS Settlement
    print("Processing TDS Settlement Payment...")
    # Calculate total TDS balance (Absolute value because it might be debit or credit depending on setup)
    total_tds = frappe.db.get_value("GL Entry", {"account": tds_payable_acc, "company": company, "is_cancelled": 0}, "sum(credit-debit)")
    
    # We want to settle whatever the balance is. If it's negative (Debit), we credit it. If positive (Credit), we debit it.
    if total_tds and total_tds != 0:
        try:
            total_tds_abs = abs(total_tds)
            settle_jv = frappe.get_doc({
                "doctype": "Journal Entry",
                "voucher_type": "Bank Entry",
                "company": company,
                "posting_date": "2025-04-07",
                "cheque_no": "TDS-SETTLE-001",
                "cheque_date": "2025-04-07",
                "remark": "Consolidated TDS Settlement to Government",
                "accounts": [
                    {
                        "account": tds_payable_acc, 
                        "debit_in_account_currency": total_tds_abs if total_tds > 0 else 0,
                        "credit_in_account_currency": total_tds_abs if total_tds < 0 else 0
                    },
                    {
                        "account": bank_acc, 
                        "credit_in_account_currency": total_tds_abs if total_tds > 0 else 0,
                        "debit_in_account_currency": total_tds_abs if total_tds < 0 else 0
                    }
                ]
            })
            settle_jv.insert()
            settle_jv.submit()
            print(f"  ✅ TDS Settlement of {total_tds} completed.")
        except Exception as e:
            print(f"  ❌ Settlement Error: {e}")

    frappe.db.commit()
    print("\n🎉 Phase 6 Simulation Complete: Workforce & Financials recorded.")

if __name__ == "__main__":
    run_phase6_simulated()

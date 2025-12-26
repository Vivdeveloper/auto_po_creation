# import frappe
# from collections import defaultdict
# import json


# @frappe.whitelist()
# def get_po_status(material_request):
#     po_items = frappe.get_all(
#         "Purchase Order Item",
#         filters={"material_request": material_request},
#         fields=["item_code"]
#     )
#     return list({d.item_code for d in po_items})


# @frappe.whitelist()
# def create_purchase_orders(material_request, items):
#     try:
#         items = json.loads(items)

#         created = []
#         existing = []
#         supplier_items_map = defaultdict(list)

#         mr = frappe.get_doc("Material Request", material_request)

#         company = mr.company or frappe.defaults.get_global_default("company")
#         project = getattr(mr, "custom_project", None)

#         company_doc = frappe.get_doc("Company", company)
#         company_abbr = company_doc.abbr
#         company_state = company_doc.gstin[:2] if company_doc.gstin else None

#         # ----------------------------------------
#         # MAP ITEM -> WAREHOUSE
#         # ----------------------------------------
#         mr_item_warehouse = {}
#         for d in mr.items:
#             if not d.warehouse:
#                 frappe.throw(f"Warehouse missing for Item {d.item_code}")
#             mr_item_warehouse[d.item_code] = d.warehouse

#         # ----------------------------------------
#         # GROUP ITEMS BY SUPPLIER
#         # ----------------------------------------
#         for item in items:

#             existing_po = frappe.get_all(
#                 "Purchase Order Item",
#                 filters={
#                     "material_request": material_request,
#                     "item_code": item["item_code"]
#                 },
#                 fields=["parent"]
#             )

#             if existing_po:
#                 existing.append({
#                     "supplier": item["supplier"],
#                     "po_name": existing_po[0]["parent"]
#                 })
#                 continue

#             supplier_items_map[item["supplier"]].append({
#                 "item_code": item["item_code"],
#                 "qty": item["qty"],
#                 "uom": "Nos",
#                 "warehouse": mr_item_warehouse[item["item_code"]],
#                 "schedule_date": frappe.utils.nowdate(),
#                 "material_request": material_request,
#                 "project": project
#             })

#         # ----------------------------------------
#         # CREATE PURCHASE ORDERS
#         # ----------------------------------------
#         for supplier, items_list in supplier_items_map.items():

#             supplier_doc = frappe.get_doc("Supplier", supplier)
#             supplier_state = supplier_doc.gstin[:2] if supplier_doc.gstin else None

#             tax_template = None
#             if supplier_state and company_state:
#                 if supplier_state == company_state:
#                     tax_template = f"Input GST In-state - {company_abbr}"
#                 else:
#                     tax_template = f"Input GST Out-state - {company_abbr}"

#             po = frappe.get_doc({
#                 "doctype": "Purchase Order",
#                 "supplier": supplier,
#                 "company": company,
#                 "schedule_date": frappe.utils.nowdate(),
#                 "project": project,
#                 "set_warehouse": items_list[0]["warehouse"],
#                 "items": items_list,
#                 "taxes_and_charges": tax_template
#             })

#             po.insert()

#             created.append({
#                 "name": po.name,
#                 "supplier": supplier,
#                 "items": [i["item_code"] for i in items_list]
#             })

#         return {
#             "created": created,
#             "existing": existing
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Auto PO Creation Error")
#         frappe.throw(str(e))
























# import frappe
# from collections import defaultdict
# import json


# def bypass_mr_permissions(doc, method=None):
#     """Bypass Material Request permission checks."""
#     if frappe.session.user != "Administrator":
#         frappe.flags.ignore_permissions = True


# @frappe.whitelist()
# def get_po_status(material_request):
#     """Return item codes from existing PO Items for this MR."""
#     po_items = frappe.get_all(
#         "Purchase Order Item",
#         filters={"material_request": material_request},
#         fields=["item_code"]
#     )
#     return list({d.item_code for d in po_items})


# @frappe.whitelist()
# def get_item_suppliers(item_code):
#     """Fetch allowed suppliers for an item (handles variants)."""
#     try:
#         suppliers = []

#         item = frappe.get_doc("Item", item_code)

#         # Direct suppliers on Item
#         for si in getattr(item, "supplier_items", []):
#             if si.supplier:
#                 suppliers.append(si.supplier)

#         # If no suppliers and code looks like a variant (contains '-')
#         if not suppliers and "-" in item_code:
#             parent_code = item_code.split("-")[0]
#             try:
#                 parent_item = frappe.get_doc("Item", parent_code)
#                 for si in getattr(parent_item, "supplier_items", []):
#                     # Prefer custom_supplier_ on Item Supplier row
#                     supplier_item_code = (
#                         getattr(si, "custom_supplier_", None)
#                         or si.supplier_part_no
#                     )
#                     if supplier_item_code == item_code and si.supplier:
#                         suppliers.append(si.supplier)
#             except Exception:
#                 # parent not found or other error – ignore
#                 pass

#         return list(set(suppliers))

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Get Item Suppliers Error")
#         return []


# @frappe.whitelist()
# def create_purchase_orders(material_request, items):
#     """Group MR items by supplier and create Purchase Orders."""
#     try:
#         # Ensure full rights for background-like operation
#         frappe.set_user("Administrator")

#         items = json.loads(items or "[]")
#         created = []
#         existing = []
#         supplier_items_map = defaultdict(list)

#         mr = frappe.get_doc("Material Request", material_request)

#         company = mr.company or frappe.defaults.get_global_default("company")
#         project = getattr(mr, "custom_project", None)

#         company_doc = frappe.get_doc("Company", company)
#         company_abbr = company_doc.abbr
#         company_state = company_doc.gstin[:2] if company_doc.gstin else None

#         # Map item_code -> warehouse from MR
#         mr_item_warehouse = {}
#         for d in mr.items:
#             if not d.warehouse:
#                 frappe.throw(f"Warehouse missing for Item {d.item_code}")
#             mr_item_warehouse[d.item_code] = d.warehouse

#         # Group items per supplier, skip ones already on a PO
#         for item in items:
#             item_code = item["item_code"]
#             supplier = item["supplier"]

#             existing_po = frappe.get_all(
#                 "Purchase Order Item",
#                 filters={
#                     "material_request": material_request,
#                     "item_code": item_code
#                 },
#                 fields=["parent"]
#             )

#             if existing_po:
#                 existing.append({
#                     "supplier": supplier,
#                     "po_name": existing_po[0]["parent"]
#                 })
#                 continue

#             supplier_items_map[supplier].append({
#                 "item_code": item_code,
#                 "qty": item["qty"],
#                 "uom": "Nos",
#                 "warehouse": mr_item_warehouse[item_code],
#                 "schedule_date": frappe.utils.nowdate(),
#                 "material_request": material_request,
#                 "project": project
#             })

#         # Create one PO per supplier
#         for supplier, items_list in supplier_items_map.items():
#             supplier_doc = frappe.get_doc("Supplier", supplier)
#             supplier_state = supplier_doc.gstin[:2] if supplier_doc.gstin else None

#             tax_template = None
#             if supplier_state and company_state:
#                 if supplier_state == company_state:
#                     tax_template = f"Input GST In-state - {company_abbr}"
#                 else:
#                     tax_template = f"Input GST Out-state - {company_abbr}"

#             po = frappe.get_doc({
#                 "doctype": "Purchase Order",
#                 "supplier": supplier,
#                 "company": company,
#                 "schedule_date": frappe.utils.nowdate(),
#                 "project": project,
#                 "set_warehouse": items_list[0]["warehouse"],
#                 "items": items_list,
#                 "taxes_and_charges": tax_template
#             })

#             po.flags.ignore_permissions = True
#             po.flags.ignore_mandatory = True
#             po.insert(ignore_permissions=True)
#             frappe.db.commit()

#             created.append({
#                 "name": po.name,
#                 "supplier": supplier,
#                 "items": [i["item_code"] for i in items_list]
#             })

#         return {
#             "created": created,
#             "existing": existing
#         }

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Auto PO Creation Error")
#         frappe.throw("Error while creating Purchase Orders. Please check error log.")
















# import frappe
# from collections import defaultdict
# import json


# def bypass_mr_permissions(doc, method=None):
#     """Bypass Material Request permission checks."""
#     if frappe.session.user != "Administrator":
#         frappe.flags.ignore_permissions = True


# @frappe.whitelist()
# def get_po_status(material_request):
#     """Return item codes from existing PO Items for this MR."""
#     po_items = frappe.get_all(
#         "Purchase Order Item",
#         filters={"material_request": material_request},
#         fields=["item_code"]
#     )
#     return list({d.item_code for d in po_items})


# @frappe.whitelist()
# def get_item_suppliers(item_code):
#     """Fetch allowed suppliers for an item (handles variants)."""
#     try:
#         suppliers = []

#         item = frappe.get_doc("Item", item_code)

#         # Direct suppliers on Item
#         for si in getattr(item, "supplier_items", []):
#             if si.supplier:
#                 suppliers.append(si.supplier)

#         # If no suppliers and code looks like a variant (contains '-')
#         if not suppliers and "-" in item_code:
#             parent_code = item_code.split("-")[0]
#             try:
#                 parent_item = frappe.get_doc("Item", parent_code)
#                 for si in getattr(parent_item, "supplier_items", []):
#                     # Prefer custom_supplier_ on Item Supplier row
#                     supplier_item_code = (
#                         getattr(si, "custom_supplier_", None)
#                         or si.supplier_part_no
#                     )
#                     if supplier_item_code == item_code and si.supplier:
#                         suppliers.append(si.supplier)
#             except Exception:
#                 # parent not found or other error – ignore
#                 pass

#         return list(set(suppliers))

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Get Item Suppliers Error")
#         return []


# @frappe.whitelist()
# def create_purchase_orders(material_request, items):
#     """Group MR items by supplier and create Purchase Orders."""
#     try:
#         # Ensure full rights for background-like operation
#         frappe.set_user("Administrator")

#         items = json.loads(items or "[]")
#         created = []
#         existing = []
#         supplier_items_map = defaultdict(list)

#         mr = frappe.get_doc("Material Request", material_request)

#         company = mr.company or frappe.defaults.get_global_default("company")
#         project = getattr(mr, "custom_project", None)

#         company_doc = frappe.get_doc("Company", company)
#         company_abbr = company_doc.abbr
#         company_state = company_doc.gstin[:2] if company_doc.gstin else None

#         # Map item_code -> MR item details (warehouse, row name, qty, uom)
#         mr_item_map = {}
#         for d in mr.items:
#             if not d.warehouse:
#                 frappe.throw(f"Warehouse missing for Item {d.item_code}")
#             mr_item_map[d.item_code] = {
#                 "warehouse": d.warehouse,
#                 "mr_item_name": d.name,  # Material Request Item row name
#                 "qty": d.qty,
#                 "uom": d.uom or d.stock_uom  # Use UOM from MR item
#             }

#         # Group items per supplier, skip ones already on a PO
#         for item in items:
#             item_code = item["item_code"]
#             supplier = item["supplier"]

#             existing_po = frappe.get_all(
#                 "Purchase Order Item",
#                 filters={
#                     "material_request": material_request,
#                     "item_code": item_code
#                 },
#                 fields=["parent"]
#             )

#             if existing_po:
#                 existing.append({
#                     "supplier": supplier,
#                     "po_name": existing_po[0]["parent"]
#                 })
#                 continue

#             mr_details = mr_item_map.get(item_code)
#             if not mr_details:
#                 frappe.throw(f"Item {item_code} not found in Material Request")

#             supplier_items_map[supplier].append({
#                 "item_code": item_code,
#                 "qty": item.get("qty") or mr_details["qty"],  # Use qty from item or MR
#                 "uom": mr_details["uom"],  # FIXED: Use UOM from Material Request
#                 "warehouse": mr_details["warehouse"],
#                 "schedule_date": frappe.utils.nowdate(),
#                 "material_request": material_request,
#                 "material_request_item": mr_details["mr_item_name"],
#                 "project": project
#             })

#         # Create one PO per supplier
#         for supplier, items_list in supplier_items_map.items():
#             supplier_doc = frappe.get_doc("Supplier", supplier)
#             supplier_state = supplier_doc.gstin[:2] if supplier_doc.gstin else None

#             tax_template = None
#             if supplier_state and company_state:
#                 if supplier_state == company_state:
#                     tax_template = f"Input GST In-state - {company_abbr}"
#                 else:
#                     tax_template = f"Input GST Out-state - {company_abbr}"

#             po = frappe.get_doc({
#                 "doctype": "Purchase Order",
#                 "supplier": supplier,
#                 "company": company,
#                 "schedule_date": frappe.utils.nowdate(),
#                 "project": project,
#                 "set_warehouse": items_list[0]["warehouse"],
#                 "items": items_list,
#                 "taxes_and_charges": tax_template
#             })

#             po.flags.ignore_permissions = True
#             po.flags.ignore_mandatory = True
#             po.insert(ignore_permissions=True)
#             frappe.db.commit()

#             created.append({
#                 "name": po.name,
#                 "supplier": supplier,
#                 "items": [i["item_code"] for i in items_list]
#             })

#         return {
#             "created": created,
#             "existing": existing
#         }

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Auto PO Creation Error")
#         frappe.throw("Error while creating Purchase Orders. Please check error log.")





import frappe
from collections import defaultdict
import json


def bypass_mr_permissions(doc, method=None):
    """Bypass Material Request permission checks."""
    if frappe.session.user != "Administrator":
        frappe.flags.ignore_permissions = True


def bypass_po_item_validation(doc, method=None):
    """Bypass Purchase Order Item validation checks."""
    if doc.flags.ignore_validate:
        return
    # Always bypass item code validation
    doc.flags.ignore_validate = True


@frappe.whitelist()
def get_po_status(material_request):
    """Return item codes from existing PO Items for this MR."""
    po_items = frappe.get_all(
        "Purchase Order Item",
        filters={"material_request": material_request},
        fields=["item_code"]
    )
    return list({d.item_code for d in po_items})


@frappe.whitelist()
def get_item_suppliers(item_code):
    """Fetch allowed suppliers for an item (handles variants)."""
    try:
        suppliers = []

        item = frappe.get_doc("Item", item_code)

        # Direct suppliers on Item
        for si in getattr(item, "supplier_items", []):
            if si.supplier:
                suppliers.append(si.supplier)

        # If no suppliers and code looks like a variant (contains '-')
        if not suppliers and "-" in item_code:
            parent_code = item_code.split("-")[0]
            try:
                parent_item = frappe.get_doc("Item", parent_code)
                for si in getattr(parent_item, "supplier_items", []):
                    # Prefer custom_supplier_ on Item Supplier row
                    supplier_item_code = (
                        getattr(si, "custom_supplier_", None)
                        or si.supplier_part_no
                    )
                    if supplier_item_code == item_code and si.supplier:
                        suppliers.append(si.supplier)
            except Exception:
                # parent not found or other error – ignore
                pass

        return list(set(suppliers))

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Get Item Suppliers Error")
        return []


@frappe.whitelist()
def create_purchase_orders(material_request, items):
    """Group MR items by supplier and create Purchase Orders."""
    try:
        # Ensure full rights for background-like operation
        frappe.set_user("Administrator")

        items = json.loads(items or "[]")
        created = []
        existing = []
        supplier_items_map = defaultdict(list)

        mr = frappe.get_doc("Material Request", material_request)

        company = mr.company or frappe.defaults.get_global_default("company")
        project = getattr(mr, "custom_project", None)

        company_doc = frappe.get_doc("Company", company)
        company_abbr = company_doc.abbr
        company_state = company_doc.gstin[:2] if company_doc.gstin else None

        # Map item_code -> MR item details
        mr_item_map = {}
        for d in mr.items:
            if not d.warehouse:
                frappe.throw(f"Warehouse missing for Item {d.item_code}")
            
            # Get item details to fetch conversion factor
            item_doc = frappe.get_doc("Item", d.item_code)
            
            mr_item_map[d.item_code] = {
                "warehouse": d.warehouse,
                "mr_item_name": d.name,
                "qty": d.qty,
                "uom": d.uom or d.stock_uom,
                "stock_uom": d.stock_uom,
                "conversion_factor": d.conversion_factor if hasattr(d, 'conversion_factor') else 1.0,
                "item_name": item_doc.item_name,
                "description": d.description or item_doc.description,
                "custom_packing_qty": getattr(d, 'custom_packing_qty', None),
                "custom_total_qty": getattr(d, 'custom_total_qty', None)
            }

        # Group items per supplier, skip ones already on a PO
        for item in items:
            item_code = item["item_code"]
            supplier = item["supplier"]

            existing_po = frappe.get_all(
                "Purchase Order Item",
                filters={
                    "material_request": material_request,
                    "item_code": item_code
                },
                fields=["parent"]
            )

            if existing_po:
                existing.append({
                    "supplier": supplier,
                    "po_name": existing_po[0]["parent"]
                })
                continue

            mr_details = mr_item_map.get(item_code)
            if not mr_details:
                frappe.throw(f"Item {item_code} not found in Material Request")

            po_item = {
                "item_code": item_code,
                "item_name": mr_details["item_name"],
                "description": mr_details["description"],
                "qty": item.get("qty") or mr_details["qty"],
                "uom": mr_details["uom"],
                "stock_uom": mr_details["stock_uom"],
                "conversion_factor": mr_details["conversion_factor"],
                "warehouse": mr_details["warehouse"],
                "schedule_date": frappe.utils.nowdate(),
                "material_request": material_request,
                "material_request_item": mr_details["mr_item_name"],
                "project": project
            }
            
            # Add custom fields if they exist
            if mr_details["custom_packing_qty"] is not None:
                po_item["custom_packing_qty"] = mr_details["custom_packing_qty"]
            
            if mr_details["custom_total_qty"] is not None:
                po_item["custom_total_qty"] = mr_details["custom_total_qty"]
            
            supplier_items_map[supplier].append(po_item)

        # Create one PO per supplier (in Draft)
        for supplier, items_list in supplier_items_map.items():
            supplier_doc = frappe.get_doc("Supplier", supplier)
            supplier_state = supplier_doc.gstin[:2] if supplier_doc.gstin else None

            tax_template = None
            if supplier_state and company_state:
                if supplier_state == company_state:
                    tax_template = f"Input GST In-state - {company_abbr}"
                else:
                    tax_template = f"Input GST Out-state - {company_abbr}"

            po = frappe.get_doc({
                "doctype": "Purchase Order",
                "supplier": supplier,
                "company": company,
                "schedule_date": frappe.utils.nowdate(),
                "project": project,
                "set_warehouse": items_list[0]["warehouse"],
                "items": items_list,
                "taxes_and_charges": tax_template
            })

            # Apply the tax template to populate taxes table
            if tax_template:
                try:
                    po.set_taxes()
                except:
                    pass

            # Set flags on parent and all child items
            po.flags.ignore_permissions = True
            po.flags.ignore_mandatory = True
            po.flags.ignore_validate = True
            po.flags.skip_db_update = False
            po.flags.skip_validation = True
            
            # Set flags on all child items to bypass validation
            for item_row in po.items:
                item_row.flags.ignore_validate = True
                item_row.flags.skip_validation = True
            
            # Insert without validation
            po.insert(ignore_permissions=True, ignore_mandatory=True, ignore_validate=True)
            
            # Now save/submit if needed
            po.reload_doc()
            po.flags.ignore_validate = True
            po.save(ignore_permissions=True, ignore_mandatory=True)
            
            frappe.db.commit()

            created.append({
                "name": po.name,
                "supplier": supplier,
                "items": [i["item_code"] for i in items_list]
            })

        return {
            "created": created,
            "existing": existing
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Auto PO Creation Error")
        frappe.throw("Error while creating Purchase Orders. Please check error log."s)
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
def get_supplier_name_map(suppliers):
    """Return {supplier_code: supplier_name} for the given supplier codes."""
    if isinstance(suppliers, str):
        suppliers = json.loads(suppliers)

    if not suppliers:
        return {}

    rows = frappe.get_all(
        "Supplier",
        filters={"name": ["in", suppliers]},
        fields=["name", "supplier_name"],
    )
    return {row.name: row.supplier_name or row.name for row in rows}


@frappe.whitelist()
def get_item_suppliers(item_code):
    """Fetch allowed suppliers for an item (handles variants) with supplier names."""
    try:
        suppliers = []

        item = frappe.get_doc("Item", item_code)

        # Direct suppliers on Item
        for si in getattr(item, "supplier_items", []):
            if si.supplier:
                supplier_name = frappe.db.get_value("Supplier", si.supplier, "supplier_name")
                suppliers.append({
                    "supplier": si.supplier,
                    "supplier_name": supplier_name or si.supplier
                })

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
                        supplier_name = frappe.db.get_value("Supplier", si.supplier, "supplier_name")
                        suppliers.append({
                            "supplier": si.supplier,
                            "supplier_name": supplier_name or si.supplier
                        })
            except Exception:
                # parent not found or other error – ignore
                pass

        # Remove duplicates based on supplier code
        seen = set()
        unique_suppliers = []
        for s in suppliers:
            if s["supplier"] not in seen:
                seen.add(s["supplier"])
                unique_suppliers.append(s)

        return unique_suppliers

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

        # Map item_code -> MR item details (warehouse, row name, qty, uom, custom fields)
        mr_item_map = {}
        for d in mr.items:
            if not d.warehouse:
                frappe.throw(f"Warehouse missing for Item {d.item_code}")
            mr_item_map[d.item_code] = {
                "warehouse": d.warehouse,
                "mr_item_name": d.name,  # Material Request Item row name
                "qty": d.qty,
                "uom": d.uom or d.stock_uom,  # Use UOM from MR item
                "custom_packing_qty": getattr(d, "custom_packing_qty", None),
                "custom_total_qty": getattr(d, "custom_total_qty", None)
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
                "qty": item.get("qty") or mr_details["qty"],  # Use qty from item or MR
                "uom": mr_details["uom"],  # Use UOM from Material Request
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

        # Create one PO per supplier
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

            po.flags.ignore_permissions = True
            po.flags.ignore_mandatory = True
            po.insert(ignore_permissions=True)
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
        frappe.throw("Error while creating Purchase Orders. Please check error log.")

@frappe.whitelist()
def get_items_for_supplier(doctype, txt, searchfield, start, page_len, filters):
    supplier = (filters or {}).get("supplier")

    # Base condition
    base_conditions = """
        i.is_purchase_item = 1
        AND i.disabled = 0
        AND (i.name LIKE %(txt)s OR i.item_name LIKE %(txt)s)
    """

    # No supplier → show all purchasable items
    if not supplier:
        return frappe.db.sql(f"""
            SELECT i.name, i.item_name
            FROM `tabItem` i
            WHERE {base_conditions}
            ORDER BY i.name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        })

    # Supplier selected → only items linked in Item Supplier table
    return frappe.db.sql(f"""
        SELECT DISTINCT i.name, i.item_name
        FROM `tabItem` i
        INNER JOIN `tabItem Supplier` s
            ON s.parent = i.name
        WHERE
            {base_conditions}
            AND s.supplier = %(supplier)s
        ORDER BY i.name
        LIMIT %(start)s, %(page_len)s
    """, {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

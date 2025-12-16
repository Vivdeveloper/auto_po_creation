# import frappe
# from frappe.utils import nowdate


# @frappe.whitelist()
# def auto_create_po_from_mr(material_request):
#     mr = frappe.get_doc("Material Request", material_request)

#     if not mr.items:
#         frappe.throw("Material Request has no items.")

#     created_pos = []
#     supplier_map = {}

#     existing_items = frappe.get_all(
#         "Purchase Order Item",
#         filters={"material_request": mr.name},
#         pluck="item_code"
#     )
#     items_with_po = set(existing_items)

#     po_schedule_date = mr.schedule_date or mr.transaction_date or nowdate()

#     for row in mr.items:
#         if row.item_code in items_with_po:
#             continue

#         supplier = frappe.db.get_value(
#             "Item Default",
#             {
#                 "parent": row.item_code,
#                 "company": mr.company
#             },
#             "default_supplier"
#         )

#         if not supplier:
#             frappe.throw(
#                 f"No Default Supplier found for Item <b>{row.item_code}</b> "
#                 f"for company <b>{mr.company}</b>.<br><br>"
#                 "Please set it in:<br>"
#                 "<b>Item → Accounting → Item Defaults</b>"
#             )

#         supplier_map.setdefault(supplier, []).append({
#             "item_code": row.item_code,
#             "item_name": row.item_name,
#             "qty": row.qty,
#             "uom": row.uom,
#             "schedule_date": po_schedule_date,
#             "material_request": mr.name,
#             "material_request_item": row.name
#         })

#     if not supplier_map:
#         frappe.msgprint("All items already have Purchase Orders.")
#         return []

#     for supplier, items in supplier_map.items():
#         po = frappe.get_doc({
#             "doctype": "Purchase Order",
#             "supplier": supplier,
#             "company": mr.company,
#             "transaction_date": nowdate(),
#             "schedule_date": po_schedule_date,
#             "items": items
#         })

#         po.insert(ignore_permissions=True)
#         po.submit()
#         created_pos.append(po.name)

#     frappe.msgprint(
#         "<b>Purchase Orders Created:</b><br>" + "<br>".join(created_pos)
#     )

#     return created_pos





















# import frappe
# from frappe.utils import nowdate


# @frappe.whitelist()
# def auto_create_po_from_mr(material_request):
#     # --------------------------------------------------
#     # Fetch Material Request
#     # --------------------------------------------------
#     mr = frappe.get_doc("Material Request", material_request)

#     if not mr.items:
#         frappe.throw("Material Request has no items.")

#     created_pos = []
#     supplier_map = {}

#     # --------------------------------------------------
#     # Items already ordered for this MR
#     # --------------------------------------------------
#     items_with_po = set(
#         frappe.get_all(
#             "Purchase Order Item",
#             filters={"material_request": mr.name},
#             pluck="item_code"
#         )
#     )

#     # --------------------------------------------------
#     # Schedule date (ERPNext v15 safe)
#     # --------------------------------------------------
#     po_schedule_date = mr.schedule_date or mr.transaction_date or nowdate()

#     # --------------------------------------------------
#     # Process MR Items
#     # --------------------------------------------------
#     for row in mr.items:
#         if row.item_code in items_with_po:
#             continue

#         # ---------------------------
#         # Default Supplier (company-wise)
#         # ---------------------------
#         supplier = frappe.db.get_value(
#             "Item Default",
#             {
#                 "parent": row.item_code,
#                 "company": mr.company
#             },
#             "default_supplier"
#         )

#         if not supplier:
#             frappe.throw(
#                 f"No Default Supplier found for Item <b>{row.item_code}</b> "
#                 f"for company <b>{mr.company}</b>.<br><br>"
#                 "Please set it in:<br>"
#                 "<b>Item → Accounting → Item Defaults</b>"
#             )

#         # ---------------------------
#         # Warehouse (MANDATORY)
#         # ---------------------------
#         warehouse = (
#             row.warehouse or
#             frappe.db.get_value(
#                 "Item Default",
#                 {
#                     "parent": row.item_code,
#                     "company": mr.company
#                 },
#                 "default_warehouse"
#             )
#         )

#         if not warehouse:
#             frappe.throw(
#                 f"No Warehouse found for Item <b>{row.item_code}</b>.<br><br>"
#                 "Please set:<br>"
#                 "<b>Material Request Item → Warehouse</b> OR<br>"
#                 "<b>Item → Accounting → Default Warehouse</b>"
#             )

#         supplier_map.setdefault(supplier, []).append({
#             "item_code": row.item_code,
#             "item_name": row.item_name,
#             "qty": row.qty,
#             "uom": row.uom,
#             "warehouse": warehouse,
#             "schedule_date": po_schedule_date,
#             "material_request": mr.name,
#             "material_request_item": row.name
#         })

#     if not supplier_map:
#         frappe.msgprint("All items already have Purchase Orders.")
#         return []

#     # --------------------------------------------------
#     # Create Purchase Orders (supplier-wise)
#     # --------------------------------------------------
#     for supplier, items in supplier_map.items():
#         po = frappe.get_doc({
#             "doctype": "Purchase Order",
#             "supplier": supplier,
#             "company": mr.company,
#             "transaction_date": nowdate(),
#             "schedule_date": po_schedule_date,
#             "items": items
#         })

#         po.insert(ignore_permissions=True)
#         po.submit()

#         created_pos.append(po.name)

#     frappe.msgprint(
#         "<b>Purchase Orders Created Successfully:</b><br>" +
#         "<br>".join(created_pos)
#     )

#     return created_pos



























import frappe
from collections import defaultdict
import json


@frappe.whitelist()
def get_po_status(material_request):
    """
    Returns item_codes for which PO already exists
    """
    po_items = frappe.get_all(
        "Purchase Order Item",
        filters={"material_request": material_request},
        fields=["item_code"]
    )
    return list({d.item_code for d in po_items})


@frappe.whitelist()
def create_purchase_orders(material_request, items):
    try:
        items = json.loads(items)

        created = []
        existing = []
        supplier_items_map = defaultdict(list)

        mr = frappe.get_doc("Material Request", material_request)

        company = mr.company or frappe.defaults.get_global_default("company")
        project = getattr(mr, "custom_project", None)

        company_doc = frappe.get_doc("Company", company)
        company_abbr = company_doc.abbr
        company_state = company_doc.gstin[:2] if company_doc.gstin else None

        # --------------------------------------------------
        # MAP ITEM -> WAREHOUSE FROM MATERIAL REQUEST
        # --------------------------------------------------
        mr_item_warehouse = {}
        for d in mr.items:
            if not d.warehouse:
                frappe.throw(
                    f"Warehouse is missing for Item {d.item_code} in Material Request"
                )
            mr_item_warehouse[d.item_code] = d.warehouse

        # --------------------------------------------------
        # GROUP ITEMS BY SUPPLIER
        # --------------------------------------------------
        for item in items:
            if not item.get("supplier"):
                continue

            existing_po = frappe.get_all(
                "Purchase Order Item",
                filters={
                    "material_request": material_request,
                    "item_code": item["item_code"]
                },
                fields=["parent"]
            )

            if existing_po:
                existing.append({
                    "supplier": item["supplier"],
                    "po_name": existing_po[0]["parent"]
                })
                continue

            warehouse = mr_item_warehouse.get(item["item_code"])

            supplier_items_map[item["supplier"]].append({
                "item_code": item["item_code"],
                "qty": item["qty"],
                "uom": "Nos",
                "warehouse": warehouse,              # ✅ ITEM WAREHOUSE
                "schedule_date": frappe.utils.nowdate(),
                "material_request": material_request,
                "project": project
            })

        # --------------------------------------------------
        # CREATE PURCHASE ORDERS
        # --------------------------------------------------
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

                # ✅ CRITICAL FIX (HEADER WAREHOUSE)
                "set_warehouse": items_list[0]["warehouse"],

                "items": items_list,
                "taxes_and_charges": tax_template
            })

            po.insert()
            created.append({
                "name": po.name,
                "supplier": supplier
            })

        return {
            "created": created,
            "existing": existing
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Auto PO Creation Error")
        frappe.throw(str(e))

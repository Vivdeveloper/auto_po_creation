// frappe.ui.form.on("Material Request", {
//     refresh(frm) {
//         if (frm.doc.docstatus === 1) {
//             frm.add_custom_button(
//                 "Auto Create PO",
//                 function () {
//                     frappe.call({
//                         method: "auto_po_creation.api.auto_create_po_from_mr",
//                         args: {
//                             material_request: frm.doc.name
//                         },
//                         freeze: true,
//                         freeze_message: "Creating Purchase Orders...",
//                         callback: function (r) {
//                             if (r.message) {
//                                 frappe.msgprint({
//                                     title: "Success",
//                                     indicator: "green",
//                                     message:
//                                         "<b>Purchase Orders Created:</b><br>" +
//                                         r.message.join("<br>")
//                                 });
//                             }
//                         }
//                     });
//                 },
//                 "Create"
//             );
//         }
//     }
// });



















// frappe.ui.form.on("Material Request", {
//     refresh(frm) {
//         if (frm.doc.docstatus === 1) {
//             frm.add_custom_button(
//                 "Auto Create PO",
//                 function () {
//                     frappe.call({
//                         method: "auto_po_creation.api.auto_create_po_from_mr",
//                         args: {
//                             material_request: frm.doc.name
//                         },
//                         freeze: true,
//                         freeze_message: "Creating Purchase Orders...",
//                         callback: function (r) {
//                             if (r.message) {
//                                 frappe.msgprint({
//                                     title: "Success",
//                                     indicator: "green",
//                                     message:
//                                         "<b>Purchase Orders Created:</b><br>" +
//                                         r.message.join("<br>")
//                                 });
//                             }
//                         }
//                     });
//                 },
//                 "Create"
//             );
//         }
//     }
// });


























frappe.ui.form.on('Material Request', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Auto Create PO'), function() {

                frappe.call({
                    method: 'auto_po_creation.api.get_po_status',
                    args: {
                        material_request: frm.doc.name
                    },
                    callback: function(response) {
                        if (!response.message) return;

                        let items_with_po = response.message;

                        let fields = [
                            {
                                fieldname: 'filter_unordered',
                                fieldtype: 'Check',
                                label: 'Show Only Items Without PO'
                            },
                            {
                                fieldname: 'items_table',
                                fieldtype: 'Table',
                                label: 'Select Suppliers',
                                fields: [
                                    { fieldname: 'item_code', fieldtype: 'Data', label: 'Item Code', read_only: 1, in_list_view: 1 },
                                    { fieldname: 'item_name', fieldtype: 'Data', label: 'Item Name', read_only: 1, in_list_view: 1 },
                                    { fieldname: 'qty', fieldtype: 'Float', label: 'Qty', read_only: 1, in_list_view: 1 },
                                    { fieldname: 'supplier', fieldtype: 'Link', label: 'Supplier', options: 'Supplier', in_list_view: 1 },
                                    { fieldname: 'po_created', fieldtype: 'Check', label: 'PO Created', read_only: 1, in_list_view: 1 }
                                ]
                            }
                        ];

                        let dialog = new frappe.ui.Dialog({
                            title: __('Select Supplier for Each Item'),
                            size: 'extra-large',
                            fields: fields,
                            primary_action_label: __('Create PO'),
                            primary_action: function() {

                                let data = dialog.get_values();
                                if (!data || !data.items_table || !data.items_table.length) {
                                    frappe.msgprint(__('Please select at least one item.'));
                                    return;
                                }

                                frappe.call({
                                    method: 'auto_po_creation.api.create_purchase_orders',
                                    args: {
                                        material_request: frm.doc.name,
                                        items: JSON.stringify(data.items_table)
                                    },
                                    callback: function(res) {
                                        if (!res.message) return;

                                        let message = '';

                                        if (res.message.created.length) {
                                            message += `<b>Purchase Orders Created:</b><br>`;
                                            res.message.created.forEach(po => {
                                                message += `<a href="/app/purchase-order/${po.name}">${po.name}</a> (Supplier: ${po.supplier})<br>`;
                                            });
                                        }

                                        if (res.message.existing.length) {
                                            message += `<br><b>Existing Purchase Orders:</b><br>`;
                                            res.message.existing.forEach(po => {
                                                message += `Supplier ${po.supplier}: <a href="/app/purchase-order/${po.po_name}">${po.po_name}</a><br>`;
                                            });
                                        }

                                        frappe.msgprint({
                                            title: __('Purchase Order Creation'),
                                            indicator: 'green',
                                            message: message
                                        });

                                        dialog.hide();
                                    }
                                });
                            }
                        });

                        function populate_table(show_only_unordered) {
                            let table_data = [];

                            frm.doc.items.forEach(item => {
                                const poExists = items_with_po.includes(item.item_code);

                                if (!show_only_unordered || !poExists) {
                                    table_data.push({
                                        item_code: item.item_code,
                                        item_name: item.item_name,
                                        qty: item.qty,
                                        supplier: '',
                                        po_created: poExists
                                    });
                                }
                            });

                            dialog.fields_dict.items_table.df.data = table_data;
                            dialog.fields_dict.items_table.grid.refresh();
                        }

                        dialog.fields_dict.filter_unordered.df.onchange = () => {
                            populate_table(dialog.get_value('filter_unordered'));
                        };

                        populate_table(false);
                        dialog.show();
                    }
                });
            });
        }
    }
});

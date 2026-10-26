/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';

export class MarksheetLineListController extends ListController {
    get actionMenuItems() {
        const menuItems = super.actionMenuItems;
        menuItems.print = [];
        return menuItems;
    }
}

registry.category("views").add("view_xe_marksheet_line_tree", {
    ...listView,
    Controller: MarksheetLineListController,
});
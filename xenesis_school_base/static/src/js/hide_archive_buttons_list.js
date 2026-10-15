/** @odoo-module **/
import { onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from '@web/core/utils/hooks';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';

export class StudentArchiveDisabledListController extends ListController {
    setup() {
        super.setup();
        this.user = useService("user");
        onWillStart(async () => {
            this.hide_archive_button = await this.user.hasGroup("xenesis_school_base.group_xe_admin");
        });
    }

    get actionMenuItems() {
        const menuItems = super.actionMenuItems;
        if(!this.hide_archive_button){
            const actionNotToKeep = ["archive", "unarchive"];
            const filteredActions = menuItems.action?.filter(action => !actionNotToKeep.includes(action.key)) || [];
            menuItems.action = filteredActions;
        }
        return menuItems;
    }
}

registry.category("views").add("view_student_tree", {
    ...listView,
    Controller: StudentArchiveDisabledListController,
});
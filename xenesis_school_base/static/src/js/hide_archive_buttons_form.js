/** @odoo-module **/
import { onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { user } from '@web/core/user';
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";

export class StudentArchiveDisabledFormController extends FormController {

    setup() {
        super.setup();
        onWillStart(async () => {
            this.hide_archive_button = await user.hasGroup("xenesis_school_base.group_xe_admin");
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

registry.category("views").add("view_student_form", {
    ...formView,
    Controller: StudentArchiveDisabledFormController,
});
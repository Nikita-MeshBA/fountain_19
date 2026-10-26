/** @odoo-module **/

import { onWillStart } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { user } from '@web/core/user';
import { ListController } from "@web/views/list/list_controller";

patch(ListController.prototype, {
    /**
     * @override
     */

    setup() {
        super.setup();
        onWillStart(async() => {
            this.hide_action_button = await user.hasGroup("xenesis_school_base.group_hide_action");
        });
    },

    get actionMenuItems() {
        const actionMenus = super.actionMenuItems;
        if (this.hide_action_button) {
            actionMenus.action = [];
            actionMenus.print = [];
        }
        return actionMenus;
    }
});
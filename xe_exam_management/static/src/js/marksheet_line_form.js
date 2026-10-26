/** @odoo-module **/
import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";

export class ExamMarksheetLineFormController extends FormController {
    get actionMenuItems() {
        const menuItems = super.actionMenuItems;
        var list_cbc = []
        var list_844 = []
        for(var i=0;i<menuItems.print.length;i++){
            if(this.model.root.data.evaluation_type=='1-3 CBC' && menuItems.print[i].name=='CBC Marksheet Line Report' || menuItems.print[i].name=='CBC Combine Marksheet Line'){
                list_cbc.push(menuItems.print[i])
            }
            if(this.model.root.data.evaluation_type=='8-4-4' && menuItems.print[i].name=='Marksheet Line' || menuItems.print[i].name=='Combine Marksheet Line'){
                list_844.push(menuItems.print[i])
            }
        }

        if(this.model.root.data.evaluation_type=='1-3 CBC'){
            menuItems.print = list_cbc;
        }
        if(this.model.root.data.evaluation_type=='8-4-4'){
            menuItems.print = list_844;
        }
        return menuItems;

    }
}

registry.category("views").add("view_xe_marksheet_line_form", {
    ...formView,
    Controller: ExamMarksheetLineFormController,
});

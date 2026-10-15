/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
// import { core } from "@web/core";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI,unblockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");
const today = luxon.DateTime.now();
import { _t } from "@web/core/l10n/translation";
const actionRegistryreport = registry.category("ir.actions.report handlers");
import { session } from '@web/session';
import { renderToElement } from "@web/core/utils/render";


class pdfPreview {

    preview(url) {
        var result = new $.Deferred();
        result.resolve(renderToElement("PDFjsFrame", {url: '/pdf_print_preview/static/lib/PDFjs/web/viewer.html?file=<%= url %>'}));
        return $.when(result);
    }

}

export default pdfPreview

class PreviewDialog extends owl.Component {

    async setup() {
        super.setup(...arguments);
        this._opened = $.Deferred();
        this.title = title || _t("Preview");
        this.url = url;
		this.$modal = renderToElement("PreviewDialog", {title: this.title, url: this.url});
        this.$modal.on("hidden.bs.modal", _.bind(this.destroy, this));

        if(config.device.isMobileDevice){
            this.$modal.find(".preview-maximize").remove();
            this.$modal.find(".preview-minimize").remove();
        }
        else {
            this.$modal.find(".preview-maximize").on("click", _.bind(this.maximize, this));
            this.$modal.find(".preview-minimize").on("click", _.bind(this.minimize, this));
            this.$modal.find(".preview-minimize").toggle();
        }
        this.$modal.find(".preview-maximize").click(); //this remove the effort of clicking button to maximize the view
    
		this.pdfPreview = pdfPreview;
	}
    async renderElement() {
    // renderElement: function() {
        // this._super();
        var self = this;
        var def = new $.Deferred();
        this.env.preview(this.url).then(function($content) {
            def.resolve(self.$modal.find(".modal-body").append($content));
        });

        return $.when(def);
	}

    async open() {
        var self = this;
        $(".tooltip").remove();
        this.renderElement().then(function(){
            self.$modal.modal("show");
            self._opened.resolve();
        });
        return self;
    }
    // maximize: function(e) {
    async maximize(e) {
        this.$modal.find(".preview-minimize").toggle();
        this.$modal.find(".preview-maximize").toggle();
        this.$modal.find(".modal-dialog").addClass("modal-full");

    }
    async minimize(e) {
    	this.$modal.find(".preview-maximize").toggle();
        this.$modal.find(".preview-minimize").toggle();
        this.$modal.find(".modal-dialog").removeClass("modal-full");
    }
    async close() {
        this.$modal.modal("hide");
    }
    async destroy(reason) {
        $(".tooltip").remove();
        if(this.isDestroyed()) {
            return;
        }
        this.trigger("closed", reason);
        this._super();
        this.$modal.modal("hide");
        this.$modal.remove();
        setTimeout(function () {
            var modals = $("body > .modal").filter(":visible");
            if(modals.length) {
                modals.last().focus();
                $("body").addClass("modal-open");
            }
        }, 0);
    }
};
PreviewDialog.createPreviewDialog = function (parent, url, title) {
    return new PreviewDialog(parent, new pdfPreview(), url, title).open();
};

// });

/**
 * Generates the report url given a report action.
 *
 * @private
 * @param {ReportAction} action
 * @returns {string}
 */
function _getReportUrl(action) {
    let url = `/report/pdf/${action.report_name}`;
    const actionContext = action.context || {};
    let filename = action.name;
    console.log('___ action.data : ', action.data);
    if (action.data && JSON.stringify(action.data) !== "{}") {
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}&`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}?`;
        }
    }
    if(filename !== undefined)
        filename = filename.replace(/[/?%#&=]/g, "") + ".pdf";
    return url += `${filename}`;
}


async function PdfPrintPreview(action, options, env) {
    const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
    const WKHTMLTOPDF_MESSAGES = {
        broken:
            _t(
                "Your installation of Wkhtmltopdf seems to be broken. The report will be shown " +
                    "in html."
            ) + link,
        install:
            _t(
                "Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."
            ) + link,
        upgrade:
            _t(
                "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
                    "get a correct display of headers and footers as well as support for " +
                    "table-breaking between pages."
            ) + link,
        workers: _t(
            "You need to start Odoo with at least two workers to print a pdf version of " +
                "the reports."
        ),
    };

    if (action.report_type === "qweb-pdf" && env.services.menu !== undefined) {
        let wkhtmltopdfStateProm = env.services.rpc("/report/check_wkhtmltopdf");
        const state = await wkhtmltopdfStateProm;
        // display a notification according to wkhtmltopdf's state
        if (state in WKHTMLTOPDF_MESSAGES) {
            env.services.notification.add(WKHTMLTOPDF_MESSAGES[state], {
                sticky: true,
                title: _t("Report"),
            });
        }
        if ((state === "upgrade" || state === "ok") && (session.preview_print || session.automatic_printing)) {
            let url = _getReportUrl(action);
            if(session.preview_print){
                PreviewDialog.createPreviewDialog(self, url,  action.name);
            }
            console.log('___ session.automatic_printing : ', session.automatic_printing);
            if (session.automatic_printing) {
                try {
                    var pdf = window.open(url);
                    pdf.print();
                }
                catch(err) {
                    env.services.notification.add(
                        _t("Please allow pop up in your browser to preview report in another tab."),
                        {
                        sticky: true,
                        title: _t("Report"),
                    });
                }
            }
            return true;
        }

    }

}

actionRegistryreport.add("pdf_print_preview", PdfPrintPreview);

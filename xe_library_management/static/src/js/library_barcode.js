odoo.define('xe_library_barcode.EventScanView', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var Session = require('web.session');
var Notification = require('web.notification').Notification;
var NotificationManager = require('web.notification').NotificationManager;
var FormController = require('web.FormController');
var time = require('web.time');

var QWeb = core.qweb;
var _t = core._t;

// Success Notification with thumbs-up icon
var Success = Notification.extend({
    template: 'xe_library_barcode_success'
});

var NotificationSuccess = NotificationManager.extend({
    success: function(title, text, sticky) {
        return this.display(new Success(this, title, text, sticky));
    }
});

// load widget with main barcode scanning View
var EventScanView = Widget.extend({
    template: 'xe_library_barcode_template',
    events: {
        'keypress #xe_library_barcode': 'on_manual_scan',
        'keypress #xe_library_barcode1': 'on_manual_scan',
        'click .o_event_info1': 'on_manual_scan',
    },

    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.message_demo_barcodes = action.params.message_demo_barcodes;
        this.action = action;
        this.parent = parent;
    },
    
    start: function() {
        var self = this;
        this.notification_manager = new NotificationSuccess();
        this.notification_manager.appendTo(self.parent.$el);
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        return this._super().then(function() {
            if (self.message_demo_barcodes) {
                self.setup_message_demo_barcodes();
            }
        });
    },
    on_manual_scan: function(e) {
        if (e.which === 13) { // Enter
            var self = this;
            var value = $(e.currentTarget).val().trim();
            var MediaValue = document.getElementById('xe_library_barcode').value;
            var LibraryCardValue = document.getElementById('xe_library_barcode1').value;
            var ttype = document.getElementById('mySelect').value;
            if (ttype == 'issue') {
		        var x = 0;
		        var y = 0;
		        if (MediaValue) {
		        	var MediaVal = MediaValue.substring(0, 3);
		        	if (MediaVal == 'MUB') {
		        		var x = MediaValue;
		        	}
		        	if (MediaVal == 'LCB') {
		        		var y = MediaValue;
		        	}
		        }
		        if (LibraryCardValue) {
		        	var LibraryCardVal = LibraryCardValue.substring(0, 3);
		        	if (LibraryCardVal == 'MUB') {
		        		var x = LibraryCardValue;
		        	}
		        	if (LibraryCardVal == 'LCB') {
		        		var y = LibraryCardValue;
		        	}
		        }
		        if ((x == 0) && (y == 0)) {
		        	self.do_warn(_("Warning"), 'Barcode is not valid');
		        }
		        if (x != 0) {
		        	document.getElementById('xe_library_barcode').value = x;
		        } else {
		        	document.getElementById('xe_library_barcode').value = '';
		        }
		        if (y != 0) {
		        	document.getElementById('xe_library_barcode1').value = y;
		        } else {
		        	document.getElementById('xe_library_barcode1').value = '';
		        }
		        if (value && (x != 0) && (y != 0)) {
		            this.on_barcode_scanned_manual(value, MediaValue, LibraryCardValue);
		            $(e.currentTarget).val('');
		        }
            } else {
            	var x = 0;
            	var MediaVal = MediaValue.substring(0, 3);
            	if (MediaVal == 'MUB') {
		        		var x = MediaValue;
		        	}
            	if (x != 0) {
            		this.on_media_scan(MediaValue);
            	} else {
            		self.do_warn(_("Warning"), 'Barcode is not valid');
            	}
            }
        }
    },
    	
    on_media_scan: function(barcode) {
	    var self = this;
	    Session.rpc('/xe_library_barcode/return_media', {
             barcode: barcode,
        }).then(function(result) {
        	if (result.success) {
        		self.notification_manager.success(result.success);
                document.getElementById('xe_library_barcode').value = '';
                document.getElementById('xe_library_barcode1').value = '';
        	} else if (result.warning) {
                self.do_warn(_("Warning"), result.warning);
            }
            if (result.penalty > 0.0) {
            	var msg = "You have to pay %s as a penalty"
            	msg = msg.replace('%s', result.penalty)
            	alert(_(msg));
            }
        });
    },
    _onBarcodeScanned: function(barcode) {
    	if (barcode) {
        	var self = this;
        	var MediaVal = barcode.substring(0, 3);
        	if (MediaVal == 'MUB') {
        		document.getElementById('xe_library_barcode').value = barcode;
        	} else if (MediaVal == 'LCB') {
        		document.getElementById('xe_library_barcode1').value = barcode;
        	}
        	var MediaValue = document.getElementById('xe_library_barcode').value;
            var LibraryCardValue = document.getElementById('xe_library_barcode1').value;
            var ttype = document.getElementById('mySelect').value;
            if (ttype == 'issue') {
		        if (MediaValue && LibraryCardValue) {
				    this.on_barcode_scanned_manual(barcode, MediaValue, LibraryCardValue);
		        }
            } else {
	        	if (MediaValue) {
	        		this.on_media_scan(MediaValue);
	        	} else {
	        		self.do_warn(_("Warning"), 'Barcode is not valid');
	        	}
            }
        }
    },
    on_barcode_scanned_manual: function(barcode, MediaValue, LibraryCardValue) {
        var self = this;
        Session.rpc('/xe_library_barcode/register_attendee', {
             barcode: barcode,
             media_barcode: MediaValue,
             librarycard_barcode: LibraryCardValue,
        }).then(function(result) {
            if (result.success) {
                self.notification_manager.success(result.success);
                document.getElementById('xe_library_barcode').value = '';
                document.getElementById('xe_library_barcode1').value = '';
            } else if (result.warning) {
                self.do_warn(_("Warning"), result.warning);
            }
        });
    },
});

core.action_registry.add('xe_library_barcode.scan_view', EventScanView);

return {
    Success: Success,
    NotificationSuccess: NotificationSuccess,
    EventScanView: EventScanView
};

});

odoo.define('mpesa_transaction_integration.DashBoard', function(require){
    
    var Widget = require('web.Widget');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var core = require('web.core');
    var ajax = require('web.ajax');
    var framework = require('web.framework');
    var datepicker = require('web.datepicker');

    var _t = core._t;
    var QWeb = core.qweb;

    var MpesaCashDashboard = Widget.extend(ControlPanelMixin, {
        template: 'MpesaCashDashboard',
            init: function(parent, action) {
                this._super.apply(this, arguments);
                this.start_date = moment().subtract(29, 'days');
                this.end_date = moment();
                this.transactions = [];
                this.customer_count = 0;
                this.days = 29;
                this.fields = ['Bill Ref-Number', 'Code', 'Date', 'Amount', 'First Name',
                'Last Name', 'Transaction Type', 'Invoice'];
                this.listview_data = [];
                this.days_ago_total_amount = 0;
                this.days_ago_count = 0;
                this.days_ago_cutomer_count = 0;
            },
            _compute_days_ago_values: function() {

            },
            _compute_customer_count: function() {
                var self = this;
                var customers = [];
                _.each(this.transactions, function(tran) {
                    var find = _.findWhere(customers, {
                        'first_name': tran.first_name,
                        'middle_name': tran.middle_name,
                        'last_name': tran.last_name
                    });
                    if(!find){
                        customers.push({
                            'first_name': tran.first_name,
                            'middle_name': tran.middle_name,
                            'last_name': tran.last_name
                        });
                    }
                });
                this.customer_count = customers.length;
            },
            _get_mpesa_transaction: function() {
                var self = this;
                return this._rpc({
                    model: 'mpesa.payment.transaction',
                    method: 'search_read',
                    args: [
                        [
                            ['state', '!=', 'cancel'],
                            ['date', '>=', self.start_date.format('Y-MM-DD')],
                            ["date","<=",self.end_date.format('Y-MM-DD')]
                        ],
                        []
                    ],
                });
            },
            start: function() {
                var self = this;
                var def = this._get_mpesa_transaction().then(function(callback) {
                    self.transactions = callback;
                    self._compute_customer_count();
                    self._compute_days_ago_values();
                    self.render_card();
                    self.render_chart();
                    self.renderlistView();
                });

                return $.when(def, this._super.apply(this, arguments)).then(function() {
                    self.update_cp();
                    self.$el.parent().addClass('oe_background_grey');
                });

            },
            _prepareData: function() {
                var self = this;
                var datasets = [];
                var labels = [];
                var data_draft = [];
                var data_done = [];
                this.listview_data = [];
                _.each(self.transactions, function(tran) {
                    self.listview_data.push({
                        'id': tran.id,
                        'Bill Ref-Number': tran.bill_ref_number,
                        'Code': tran.business_shortcode,
                        'Date': tran.date,
                        'Amount': tran.trans_amount,
                        'First Name': tran.first_name,
                        'Last Name': tran.last_name,
                        'Transaction Type': tran.transaction_type,
                        'Invoice': tran.invoice_name,
                    });
                });
                
                _.each(self.transactions, function(tran) {
                    var dict = {'y': parseFloat(tran.trans_amount), 'x': tran.date};
                    if(tran.state === 'draft'){
                        data_draft.push(dict);
                    }else if(tran.state === 'done'){
                        data_done.push(dict);
                    }
                    labels.push(tran.date);
                });
                datasets.push({
                    'data': data_draft,
                    'label': 'Draft',
                    backgroundColor: 'rgb(255, 99, 132)',
                    borderColor: 'rgb(255, 99, 132)',
                    fill: false,
                });
                datasets.push({
                    'data': data_done,
                    'label': 'Reconciled',
                    backgroundColor: 'rgb(54, 162, 235)',
                    borderColor: 'rgb(54, 162, 235)',
                    fill: false,
                });
                return {
                    datasets: datasets,
                    labels: labels
                }
            },
            renderlistView: function() {
                var self = this;
                this.$('#o_transaction_table').empty();
                var $listview = QWeb.render('MPesaListView', {
                    'widget': self,
                    'fields': self.fields,
                    'datas': self.listview_data
                });
                this.$('#o_transaction_table').append($listview);
                this._destroy_datatable();
                this.init_datatable();
            },
            _destroy_datatable: function() {
                if (this.$Datatable) {
                    this.$Datatable.destroy();
                    this.$('#oe_table tbody').empty();
                }
            },
            init_datatable: function() {
                var self = this;
                var columns1 = [];
                _.each(this.fields, function(field) {
                    columns1.push({
                        'data': field
                    })
                });

                columns1.push({
                    data: "id",
                    'name': "Operation",
                    orderable: false,
                    render: function(data, type, row, meta) {
                        var $print_button = "<button type='button' id=" + data + " data-model=" + row.model + " class='btn btn-primary btn-xs btn-print' style='margin-right:16px;'><span class='fa fa-print'></span></button>";
                        return $print_button;
                    }
                });

                this.$Datatable = this.$('#oe_table').DataTable({
                    'data': self.listview_data,
                    columns: columns1,
                    // "scrollY": "200px",
                    "scrollCollapse": true,
                    'iDisplayLength': 100
                });

                this.$('#oe_table tbody').on('click', '.btn-print', function(event) {
                    var data = self.$Datatable.row($(this).parents('tr')).data();
                    framework.blockUI();
                    self.do_action('mpesa_transaction_integration.report_transactiondetails_report', {
                        additional_context: {
                            active_ids: [data.id],
                        }
                    }).done(function() {
                        framework.unblockUI();
                    }).fail(function() {
                        framework.unblockUI();
                    });
                });
            },
            render_chart: function() {
                var self = this;
                var data = this._prepareData()
                var ctx = this.$('#o_transaction_chart');
                this.chart = new Chart(ctx, {
                    type: 'line',
                    data: data,
                    options: {
                        "scales": {
                            "xAxes": [
                              {
                                "type": "time",
                                "time": {
                                  "parser": "YYYY-MM-DD",
                                  "tooltipFormat": "ll HH:mm"
                                },
                                "scaleLabel": {
                                  "display": true,
                                  "labelString": "Date"
                                }
                              }
                            ],
                            "yAxes": [
                              {
                                "scaleLabel": {
                                  "display": true,
                                  "labelString": "Amount"
                                }
                              }
                            ]
                          }
                    }
                });
            },
            render_card: function() {
                var self = this;
                var total = _.reduce(self.transactions, function(memo, obj){
                     return memo + obj['trans_amount']; 
                }, 0);

                var total_count = self.transactions.length;
                this.$('.o_transaction_card').empty();
                this.$('.o_transaction_card').append(QWeb.render('TransactionCard', {
                    'widget': this,
                    'total': total,
                    'total_count': total_count,
                    'customer_count': this.customer_count,
                    'days_ago_total_amount': this.days_ago_total_amount,
                    'days_ago_cutomer_count': this.days_ago_cutomer_count,
                    'days_ago_count': this.days_ago_count
                }));
            },
            update_cp: function() {
                var self = this;
                var def;
                if (!this.$searchview) {
                    this.$searchview = $(QWeb.render("DateRangePicker", {
                        widget: this,
                    }));
                    def = this.set_up_datetimepickers();
                }

                $.when(def).then(function() {
                    self.update_control_panel({
                        cp_content: {
                            $searchview: self.$searchview,
                            $searchview_buttons: $(),
                        },
                        breadcrumbs: self.getParent().get_breadcrumbs(),
                    });

                    self.$searchview.find('#apply_date').off().on('click', function(event) {
                        event.preventDefault()
                        
                    });
                });
            },
            set_up_datetimepickers: function() {
                var self = this;
                function cb(start, end) {
                    self.$searchview.find('#reportrange span').html(
                        self.start_date.format('MMMM D, YYYY') + ' - ' + self.end_date.format('MMMM D, YYYY'));
                }
                
                if (!this.picker) {
                    this.picker = this.$searchview.find('#reportrange').daterangepicker({
                        startDate: self.start_date,
                        endDate: self.end_date,
                        ranges: {
                            'Today': [moment(), moment()],
                            'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                            'This Month': [moment().startOf('month'), moment().endOf('month')],
                            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
                        }
                    }, cb);
                   cb(self.start_date, self.end_date);
                    this.$searchview.find('#reportrange').on('apply.daterangepicker', function(ev, picker) {
                        self.start_date = picker.startDate;
                        self.end_date = picker.endDate;
                        var diff = picker.endDate.diff(picker.startDate, 'days');
                        self.days = diff + 1;
                        cb(self.start_date, self.end_date);
                        self._get_mpesa_transaction().then(function(callback){
                            self.transactions = callback;
                            self._compute_customer_count();
                            self._compute_days_ago_values();
                            self.render_card();
                            self.render_chart();
                            self.renderlistView();
                        });
                    });
                }

                var def1 = this.picker.appendTo(this.$searchview.find('.reportrange'));
                    return $.when(def1).then(function() {
                });
            },
    });

    core.action_registry.add('mpesa-cash-dashboard', MpesaCashDashboard);

    return MpesaCashDashboard;
});

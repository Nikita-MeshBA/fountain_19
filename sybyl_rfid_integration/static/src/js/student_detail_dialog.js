/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { MainComponentsContainer } from "@web/core/main_components_container";
import { useService, useBus } from "@web/core/utils/hooks";
import { useState, Component, onRendered, onMounted, onWillDestroy } from "@odoo/owl";
import { registry } from "@web/core/registry";
const actionRegistry = registry.category("actions");

class StudentFeesDetails extends Component {
    static components = {
        MainComponentsContainer,
    };
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.student_id = null;
        this.data = null;
        this.timerInterval = null;
        this.timeInterval = null;
        this.close = true;
        this.loaded_student_info = [];
        this.state = useState({
            data: null,
            student_name: null,
            date: null,
            roll_number: null,
            class: null,
            classroom: null,
            image: null,
            fee_balance: null,
            status: null,
        })
        this.load_student_dialog();
        onMounted(async () => {

            var element = document.getElementsByClassName('timerContainer');
            var element1 = $('.timerContainer');
            // this.output = false;
            this.timeLeft = 30;
            $('.timer').text(`Closing in ${this.timeLeft} seconds`);
            const now = new Date();
            const formattedTime = now.toLocaleTimeString();
            const formattedDate = now.toLocaleDateString();
            $('#currentTime').text(`Current Time:${formattedDate} ${formattedTime}`);

            // if (output){
            this.timerInterval = setInterval(() => {
                this.timeLeft -= 1;
                console.log('___ time in 30 : ', $('.timer'));
                $('.timer').text(`Closing in ${this.timeLeft} seconds`);
                const now = new Date();
                const formattedTime = now.toLocaleTimeString();
                const formattedDate = now.toLocaleDateString();
                $('#currentTime').text(`Current Time:${formattedDate} ${formattedTime}`);
                
                if (this.timeLeft <= 0) {
                    this.closeTimer();
                    if(this.close){
                        this.closeSession();
                    }
                }
            }, 1000);

            this.timeInterval = setInterval(this.updateCurrentTime, 1000);

            // Call a function every 2 seconds
            this.twoSecondInterval = setInterval(() => {
                console.log('___ this.timeLeft : ', this.timeLeft);
                if (this.timeLeft > 0) {
                    var output = this.load_student_dialog();
                } else {
                    clearInterval(this.twoSecondInterval); // Clear the interval when this.timeLeft is 0
                }
            }, 2000);
            // }
        });
        onWillDestroy(() => {
            this.timeLeft = 0;
            this.close = false;
        });

    }
    async closePopup() {
        document.getElementById("myModal").style.display = "none";
    }
    async openPopup() {
        document.getElementById("myModal").style.display = "block";
    }
    async cancelPopup() {
        document.getElementById("myModal").style.display = "none";

    }
    
    async closeSession() {
        var session_id = this.props.action.context.active_id
        this.orm.call("rfid.session.configuration", "open_existing_session_cb", [null,{session_id}]);
        var element = document.querySelector('.o_main_navbar');
        element.style.display = '';
        this.action.doAction("sybyl_rfid_integration.open_session_dashboard_kanban")
    }


    closeTimer() {
        clearInterval(this.timerInterval);
        clearInterval(this.timeInterval);
    }

    updateCurrentTime() {
        const now = new Date();
        const formattedTime = now.toLocaleTimeString();
        const formattedDate = now.toLocaleDateString();
        $('#currentTime').text(`Current Time: ${formattedTime}`);
    }
    async load_student_dialog() {
        var session_id = this.props.action.context.active_id
        this.state.data = await this.orm.call("rfid.session.configuration", "fetch_latest_scan", [null,{session_id}]);
        if (this.state.data.student_name){
            if (!this.loaded_student_info.includes(this.state.data.student_name)) {
                this.loaded_student_info = []
                this.loaded_student_info.push(this.state.data.student_name)
                this.timeLeft = 30;
            }

            this.state.student_name = this.state.data.student_name
            this.state.date = this.state.data.date
            this.state.roll_number = this.state.data.roll_number
            this.state.class = this.state.data.class
            this.state.classroom = this.state.data.classroom
            this.state.image = this.state.data.image
            this.state.fee_balance = this.state.data.fee_balance
            this.state.status = this.state.data.status
        }
        var element = document.querySelector('.o_main_navbar');
        element.style.display = 'none';
    }
}


window.addEventListener('popstate', function(event) {
    var element = document.querySelector('.student-profile-card');
    if (element) {
        alert("Session closed!!!");
    }
    var element1 = document.querySelector('.o_main_navbar');
    element1.style.display = '';

});
StudentFeesDetails.template = 'student_details_dialog';
actionRegistry.add("student_dialog", StudentFeesDetails);

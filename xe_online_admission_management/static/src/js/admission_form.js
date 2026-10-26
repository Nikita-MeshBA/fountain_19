/** @odoo-module */

$(document).ready(function () {

    $("#sibling_div").hide();
    $("#sibling_boolean").click(function () {
        if ($(this).is(":checked")) {
            $("#sibling_div").show();
            $(".parent_div").hide();
        } else {
            $("#sibling_div").hide();
            $(".parent_div").show();
        }
        var school = $("#school_id").val()
    });

    $("#school_id").change(function () {
        var school = $("#school_id").val()
        $.ajax({
            url:'/get/courses',
            type: 'post',
            contentType: 'application/json',
            data: JSON.stringify({ params: {'school':school} }),
        }).done(function(course_ids) {
            var options = $('#course_name')
            options.empty()
             course_ids.result.forEach(function(item) {
                var option = $('<option>', { value: item.name, text: item.name,id:item.id});
                options.append(option);
            });
        });
    });

    $("#course_name").change(function () {
        var selectedOption = $(this).find("option:selected");
        var selectedOptionId = selectedOption.attr("id");
        $("#course_id").val(selectedOptionId);
    });



});
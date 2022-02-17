//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//

// Shows and hides the task list when click on dropdown button
function task_list_dropdown(header) {
    const content_div = $(header).closest(".section").children(".content");
    const button = $(header).children(".dropdown_button")

    if ($(button).hasClass("fa-caret-down")) {
        $(button).removeClass("fa-caret-down").addClass("fa-caret-left");
        content_div.slideUp('fast')
    } else {
        $(button).removeClass("fa-caret-left").addClass("fa-caret-down");
        content_div.slideDown('fast')
    }
}
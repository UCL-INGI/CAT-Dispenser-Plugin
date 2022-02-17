//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//

/************************
   Task addition helpers
*************************/

// Sets the content of the task modal according to the currently present tasks in task-list
function demo_disp_prepare_task_modal(target) {
    var placed_task = [];
    $('.task').each(function () {
        placed_task.push(this.id.slice(5));
    });

    $("#modal_task_list .modal_task").filter(function () {
        // remove task already placed in the structure
        const is_placed = placed_task.includes($(this).children("input").val());
        $(this).toggle(!is_placed);
        $(this).toggleClass("disable", is_placed);

        // reset the selection
        $(this).children("input").attr("checked", false);
        $(this).removeClass("bg-primary text-white");
    });

    var no_task_avalaible = $("#modal_task_list .modal_task").not(".disable").length === 0;
    $("#searchTask").val("").toggle(!no_task_avalaible);
    $("#no_task_available").toggle(no_task_avalaible);
}

// Searches in existing tasks names from the filesystem
function demo_disp_search_task(search_field) {
    var value = $(search_field).val().toLowerCase();
    $("#modal_task_list .modal_task").filter(function () {
        const match_search = $(this).children(".task_name").text().toLowerCase().indexOf(value) > -1;
        const is_unplaced = !$(this).hasClass("disable");
        $(this).toggle(match_search && is_unplaced);
    });
}

// Selects task for addition
function demo_disp_select_task(task) {
    $(task).toggleClass("bg-primary text-white");
    const input = $(task).find("input");
    input.attr("checked", !input.attr("checked"));
}

// Adds the select items from the modal to the main tasks-list and register the addition through
// - dispenser_add_task
function demo_disp_add_tasks(button) {
    task_id= $("#new_task_id").val();
    var selected_tasks = [];
    var existing_task = $(button).attr("id") == "add_existing_tasks";
    if(existing_task) {
        $.each($("input[name='task']:checked"), function () {
            selected_tasks.push($(this).val());
        });
    }
    else {
        if(!task_id.match(/^[a-zA-Z0-9_\-]+$/)){
            alert('Task id should only contain alphanumeric characters (in addition to "_" and "-").');
            return;
        }
        selected_tasks.push(task_id);
    }

    const content = $("#tasks-list");
    for (var i = 0; i < selected_tasks.length; i++) {
        warn_before_exit = true;
        if(existing_task)
            content.append($("#task_" + selected_tasks[i] + "_clone").clone().attr("id", 'task_' + selected_tasks[i]));
        else {
            var new_task_clone = $("#new_task_clone").clone();
            new_task_clone.attr("id", 'task_' + selected_tasks[i]);
            new_task_clone.children(".task_name").append(selected_tasks[i]);
            content.append(new_task_clone);
            dispenser_add_task(selected_tasks[i]);
        }
    }
}

/**************************
    Task deletion helpers
***************************/

// Sets the delete modal fields according to the selected task
function demo_disp_prepare_delete_modal(button) {
    $('#delete_task_modal .submit').attr('data-target', button.closest('.task').id);
    $('#delete_task_modal .wipe_tasks').prop("checked", false);
}

// Deletes the task from the task-lists and register deletion trough
// - dispenser_delete_task
// - or; dispenser_wipe_task
function demo_disp_delete_task(button, keep_files){
    $(button).mouseleave().focusout();
    taskid = button.getAttribute('data-target').slice(5);

    if(!keep_files) {
        $("#modal_task_" + taskid).remove()
        dispenser_delete_task(taskid)
    }

    wipe = $('#delete_task_modal .wipe_tasks').prop("checked");
    if(wipe)
        dispenser_wipe_task(taskid);

    const task = $("#task_" + taskid);
    task.remove();
}

/**************
   Submission
***************/

// Generates the json-encoded data to save into the course task dispenser data
// This functions must be named dispenser_structure_{{ dispenser_id }}
function dispenser_structure_demo_dispenser() {
    const tasks_list = [];
    $("#tasks-list .task").each(function (index) {
        tasks_list[index] = this.id.slice(5);
    });
    return JSON.stringify(tasks_list);
}
$(document).ready(function(){

    var url = "/progress/" + job_id + "/status";

    function receiveStatus(data, status, jqXHR) {

        // update the job status
        $("#job_status").html(data.status);

        if (data.status == "submitted") {
            // hide the elements not relevant to this status
            $("#error_container").hide();
            $("#progress_container").hide();
            $("#download_container").hide();

            $("#queue_length").html(data.queue);
            $("#queue_notify").show();
            $("#queue_container").show();
        } else if (data.status == "processing") {
            // hide the elements not relevant to this status
            $("#error_container").hide();
            $("#queue_container").hide();

            var pc = Math.round(data.pc * 10) / 10;
            $("#pc_container").html(pc);
            $("#download_link").html("Download current progress");
            $("#progress_container").show();
            $("#download_container").show();
        } else if (data.status == "error") {
            // hide the elements not relevant to this status
            $("#queue_container").hide();
            $("#progress_container").hide();
            $("#download_container").hide();

            $("#error_message").html(data.message);
            $("#error_container").show();
        } else if (data.status == "complete") {
            // hide the elements not relevant to this status
            $("#error_container").hide();
            $("#queue_container").hide();
            $("#progress_container").hide();

            $("#download_link").html("Download final result");
            $("#download_container").show();
        }

        if (data.status !== "complete" && data.status != "error") {
            setTimeout(updateStatus, 1000);
        }
    }

    function updateStatus() {
        $.ajax(url, {
            cache: false,
            dataType: 'jsonp',
            type: 'GET',
            success: receiveStatus,
            error: function (jqXHR, textStatus, errorThrown) {
                console.log(jqXHR);
                console.log(textStatus);
                console.log(errorThrown);
            }
        });
    }

    updateStatus();
});

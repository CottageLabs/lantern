$(document).ready(function(){
    url = "/progress/" + job_id + "/pc";

    ajaxRequest();

    function ajaxRequest () {
        $.ajax(url, {
                cache: false,
                dataType: 'text',
                type: 'GET',
                success: function (data, status, jqXHR) {
                    var results = data;
                    console.log(data);
                    $('#pc_container').html(results);
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.log(jqXHR);
                    console.log(textStatus);
                    console.log(errorThrown);
                }
        });
        setTimeout(ajaxRequest, 1000);
    };
});

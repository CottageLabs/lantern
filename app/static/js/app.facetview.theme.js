jQuery(document).ready(function($) {

    /****************************************************************
     * Application Facetview Theme
     *****************************
     */

    function discoveryRecordView(options, record) {
        var result = options.resultwrap_start;
        result += "<div class='row-fluid' style='margin-top: 10px; margin-bottom: 10px'>"
        result += "<div class='span12'>"
        result += "<strong style='font-size: 150%'>" + record["id"] + "</strong><br>"
        result += "</div></div>"
        result += options.resultwrap_end;
        return result;
    }

    var facets = []
    facets.push({'field': 'last_updated', 'display': 'Last Updated'})

    $('#facetview').facetview({
        debug: false,
        search_url : query_endpoint, // defined in the template which calls this
        page_size : 25,
        facets : facets,
        search_sortby : [
            {'display':'Last Modified','field':'last_updated'},
            {'display':'Date Created','field':'created_date'}
        ],
        searchbox_fieldselect : [
            {'display':'ID','field':'id'}
        ],
        render_result_record : discoveryRecordView,

    });

});

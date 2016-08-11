/* IIIF Demo Authentication Library
 * For v0.9.2: http://auth_notes.iiif.io/api/auth/0.9/
 * 
 * Required OpenSeadragon 121 or higher.
 * Requires jQuery 1.11 or higher.
 *
 * Based on IIIF Auth 0.9 implementation by Robert Sanderson
 * Simeon Warner - 2016-08-10...
 */

// Use Revealing Module pattern:
// https://addyosmani.com/resources/essentialjsdesignpatterns/book/#revealingmodulepatternjavascript

var iiif_auth = (function () {

var log_id = "#log"
var token_service_uri = "http://localhost:8001/2.1_pil_gauth/token";
var image_uri = "";

// Logging window function to show useful debugging output
//
// Requires an HTML element (such as a <div>) with id="log"
// to which new lines of text are appended on every call.
var linenum = 0;
function log(text) {
    linenum = linenum + 1;
    $(log_id).prepend("[" + linenum + "] " + text + "<br/>");
}

// check for an auth service ... once tileSource has loaded
function on_authed() {
    // first try to get an authorization token from the token service ...
    // via JSONP :(
    // XXX TODO: get the URL from the info.json
    log("Fetching Token");        
    $.getJSON(token_service_uri + "?callback=?", on_tokened);
}


function on_tokened(data) {
    var token, error;
    if (data.hasOwnProperty('access_token')) {
        token = data.access_token;
        error = false;
        log("Got token: " + token);
    } else {
        // error condition
        token = '';
        error = true;
        log("Got error: " + data.error)
    }

    if (error) {
        // Error make unauthed viewer
        make_viewer();
    } else {
        // Okay, make authed viewer
        $('#openseadragon').remove();
        $('#authbox').empty();
        $('#container').append('<div id="openseadragon" style="width: 600px; height: 400px; border: 2px solid purple" ></div>');
        $.ajax({ url: image_uri+"/info.json",
                 headers: {"Authorization": token},
                 cache: false,
                 success: on_got_info });
    }
}

function on_got_info(data) {

    log("Got full info.json")

    process_auth_services(data, 'logout');

    viewer = OpenSeadragon({
        id: "openseadragon",
        tileSources: data,
        showNavigator: true,
        prefixUrl: "openseadragon121/images/"
    });
}

function do_auth(evt) {
    login = $(this).attr('data-login');

    // The redirected to window will self-close
    // open/closed state is the only thing we can see across domains :(
    log("Opening Auth service");
    var win = window.open(login, 'loginwindow');
    var pollTimer   =   window.setInterval(function() { 
        if (win.closed) {
            window.clearInterval(pollTimer);
            on_authed();
        }
    }, 500);
}

function process_auth_services(info, which) {
    log("Looking for "+which+" service")
    if (info.hasOwnProperty('service')) {
        if (info.service.hasOwnProperty('@id')) {
            services = [info.service]
        } else {
            // array of service
            services = info.service
        }
        for (var service,i=0;service=services[i];i++) {
            if (service['profile'] == 'http://iiif.io/api/auth/0/'+which) {
                log("Found "+which+" auth service");
                login = service['@id'];
                $('#authbox').append("<button id='authbutton' data-login='"+login+"'>"+service.label+"</button>");
                $('#authbutton').bind('click', do_auth);
            } else if (which == 'login' &&
                       service['profile'] == 'http://iiif.io/api/auth/0/token') {
                // save token service here...
            }
        }
    } 
}

function handle_open(event) {
    var info = event.eventSource.source;
    // This only gets called when we're NOT authed, so no need to put in logout
    process_auth_services(info, 'login');
}

// Make an OpenSeadragon viewer
function make_viewer(image_uri_in) {
    image_uri = image_uri_in;
    log("Making unauthed viewer");

    $('#openseadragon').remove();
    $('#authbox').empty();
    $('#container').append('<div id="openseadragon" style="width: 600px; height: 400px; border: 2px solid purple" ></div>');
    var where = $("#openseadragon");

    var viewer = OpenSeadragon({
        id: "openseadragon",
        tileSources: image_uri + "/info.json?t=" + new Date().getTime(),
        showNavigator: true,
        prefixUrl: "openseadragon121/images/"
    });

    viewer.addHandler('open', iiif_auth.handle_open)
    viewer.addHandler('failed-open', iiif_auth.handle_open)
}

// Return pointers making certain variables and functions public
return {
    // Variables
    log_id: log_id,
    // Functions
    log: log,
    process_auth_services: process_auth_services,
    handle_open: handle_open
};

})();
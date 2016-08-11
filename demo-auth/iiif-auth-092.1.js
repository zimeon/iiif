/* IIIF Demo Authentication Library
 * For v0.9.2: http://auth_notes.iiif.io/api/auth/0.9/
 * 
 * Requires OpenSeadragon 121 or higher.
 * Requires jQuery 1.11 or higher.
 *
 * Based on IIIF Auth 0.9 implementation by Robert Sanderson
 * Simeon Warner - 2016-08-10...
 */

// Use Revealing Module pattern:
// https://addyosmani.com/resources/essentialjsdesignpatterns/book/#revealingmodulepatternjavascript

var iiif_auth = (function () {

var log_id = "#log";
var token_service_uri = "http://localhost:8001/2.1_pil_gauth/token";
var image_uri = "";

/**
 * Logging window function to show useful debugging output
 * 
 * Requires an HTML element (such as a <div>) with id="log"
 * to which new lines of text are appended on every call.
 */
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
    log("Got full info.json");

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

/** 
 * Find auth service URIs and labels from info.json object
 * 
 * @param {object} info - the info.json object
 * @return {object} - with properties as below:
 *   login - URI of login service (not set if none found)
 *   login_label - a string with default or label given
 *   token - URI of login service (not set if none found)
 * 
 */
function find_auth_services(info) {
    // Result object with default labels
    var svc = {login_label: "Login",
               logout_label: "Logout"};
    log("Looking for auth service descriptions")
    if (info.hasOwnProperty('service')) {
        if (info.service.hasOwnProperty('@id')) {
            // make array from single service entry
            services = [info.service];
        } else {
            // array of service entries
            services = info.service;
        }
        for (var service,i=0; service=services[i]; i++) {
            if (service['profile'] == 'http://iiif.io/api/auth/0/login') {
                svc.login = service['@id'];
                log("Found login service (" + svc.login + ")");
                if (service.hasOwnProperty('label')) {
                    svc.login_label = service['label'];
                }
                login = service;
                break;
            }
        }
        // All bets off if we haven't found the login service, can't
        // look for more
        if (!svc.hasOwnProperty('login')) {
            return svc;
        }
        // Now look for token (required) and logout (optional) as sub-services
        if (login.hasOwnProperty('service')) {
            if (login.service.hasOwnProperty('@id')) {
                // make array from single service entry
                services = [login.service];
            } else {
                // array of service entries
                services = login.service;
            }
            for (var service,i=0; service=services[i]; i++) {
                if (service['profile'] == 'http://iiif.io/api/auth/0/token') {
                    svc.token = service['@id'];
                    log("Found token service (" + svc.token + ")");
                } else if (service['profile'] == 'http://iiif.io/api/auth/0/logout') {
                    svc.logout = service['@id'];
                    log("Found logout service (" + svc.logout + ")");
                    if (service.hasOwnProperty('label')) {
                        svc.logout_label = service['label'];
                    }
                }
            }
        }
        // Login won't work without a token service so delete the
        // login entry if that is the case
        if (!svc.hasOwnProperty('token')) {
            delete svc.login;
        }
    }
    return svc;
}
 
/**
 * Handler for OpenSeadragon event used as hook to get login information
 *
 * @param event
 */
function handle_open(event) {
    var info = event.eventSource.source;
    // This only gets called when we're NOT authed, so no need to put in logout
    var svc = find_auth_services(info);
    if (svc.hasOwnProperty('login')) {
        log("Adding login button")
        $('#authbox').append("<button id='authbutton' data-login='"+svc.login+"'>"+svc.login_label+"</button>");
        $('#authbutton').bind('click', do_auth);
    } else {
        log("No login service");
    }
}

/**
 * Make an OpenSeadragon viewer
 *
 * @param {string} image_uri_in - the IIIF Image URI (no /info.json or /params/) 
 */
function make_viewer(image_uri_in) {
    image_uri = image_uri_in;
    log("Making unauthenticated viewer");

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
    viewer.addHandler('open', handle_open)
    viewer.addHandler('failed-open', handle_open)
}

// Return pointers making certain variables and functions public
return {
    // Variables
    log_id: log_id,
    // Functions
    log: log,
    make_viewer: make_viewer
};

})();
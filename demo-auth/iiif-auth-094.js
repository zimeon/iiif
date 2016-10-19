/* IIIF Demo Authentication Library
 * For v0.9.4: http://auth_notes.iiif.io/api/auth/0.9/
 * 
 * Requires OpenSeadragon 121, 200 or higher.
 * Requires jQuery 1.11 or higher.
 *
 * Starting point was IIIF Auth v0.9 implementation by Robert Sanderson @azaroth42.
 * Simeon Warner @zimeon - 2016-08-10...
 */

/*jslint white: true*/
/*jslint unparam: true*/
/*global $, OpenSeadragon, window, setTimeout*/

// Use Revealing Module pattern:
// https://addyosmani.com/resources/essentialjsdesignpatterns/book/#revealingmodulepatternjavascript

var iiif_auth = (function () {
"use strict";

var osd_prefix_url = "openseadragon200/images/",
    osd_div = '<div id="openseadragon" style="width: 600px; height: 400px; border: 2px solid purple" ></div>',
    osd_id = "#openseadragon",
    iframe_html = '<iframe id="messageFrame" style="margin-top: 10px; height: 3ex; border: 2px solid blue; width: 605px;"></iframe>',
    demo_html =
        '<div id="container" style="width: 605px; height: 405px;"></div>' +
        '<div id="authbox" style="margin-top: 10px; height: 9ex; border: 2px solid red; width: 605px; overflow: auto;"></div>' +
        '<div id="log" style="margin-top: 10px; height: 26ex; border: 2px solid green; width: 605px; overflow: auto;"></div>' +
        '<div id="frameWrapper">' + iframe_html + '</div>',
    container_id = "#container",
    authbox_id="#authbox",
    log_id = "#log",
    message_frame_id = "#messageFrame",
    frame_wrapper_id = "#frameWrapper",
    token_service_uri = "",
    image_uri = "",
    profiles = {'http://iiif.io/api/auth/0/login': 'login',
                'http://iiif.io/api/auth/0/clickthrough': 'clickthrough',
                'http://iiif.io/api/auth/0/kiosk': 'kiosk'},
    viewer, // our instance of OpenSeadragon
    viewer_authed = false,
    linenum = 0, // line number of log text
    make_viewer;

/**
 * Logging window function to show useful debugging output
 * 
 * Requires an HTML element (such as a <div>) with id="log"
 * to which new lines of text are appended on every call. If
 * called with text False then will add a blank line.
 *
 * @param {string} text - a line of log text to display
 */
function log(text) {
    $(log_id).prepend("<br/>");
    if (text) {
        linenum += 1;
        $(log_id).prepend("[" + linenum + "] " + text);
    }
}

/** 
 * Find auth service URIs and labels from info.json object
 * 
 * @param {object} info - the info.json object
 * @return {object} - with properties as below:
 *   uri - URI of auth service (not set if none found)
 *   login_label - a string with default or label given
 *   token - URI of login service (not set if none found)
 * 
 */
function find_auth_services(info) {
    // Result object with default labels
    var services, auth, service, i, len,
        svc = {login_label: "Login",
               logout_label: "Logout",
               confirm_label: "I agree, give me access"};
    log("Looking for auth service descriptions");
    if (info.hasOwnProperty('service')) {
        if (info.service.hasOwnProperty('@id')) {
            // make array from single service entry
            services = [info.service];
        } else {
            // array of service entries
            services = info.service;
        }
        // Look through services and exit at the first recognized authentication
        // service. 
        //
        // FIXME - should handle the case of multiple authentication services
        for (i=0, len=services.length; i < len; i+=1) {
            service=services[i];
            log("service @id " + service['@id']);
            if (profiles.hasOwnProperty(service.profile)) {
                svc.pattern = profiles[service.profile];
                svc.uri = service['@id'];
                log("Found " + svc.pattern +" service (" + svc.uri + ")");
                if (service.hasOwnProperty('label')) {
                    svc.login_label = service.label;
                }
                if (service.hasOwnProperty('confirmLabel')) {
                    svc.confirm_label = service.confirmLabel;
                }
                if (service.hasOwnProperty('header')) {
                    svc.header= service.header;
                }
                if (service.hasOwnProperty('description')) {
                    svc.description = service.description;
                }
                auth = service;
                break;
            }
        }
        // All bets off if we haven't found and auth service with a profile
        // we recognize, can't look for more
        if (!auth) {
            return svc;
        }
        // Now look for token (required) and logout (optional) as sub-services
        if (auth.hasOwnProperty('service')) {
            if (auth.service.hasOwnProperty('@id')) {
                // make array from single service entry
                services = [auth.service];
            } else {
                // array of service entries
                services = auth.service;
            }
            for (i=0, len=services.length; i < len; i+=1) {
                service=services[i];
                if (service.profile === 'http://iiif.io/api/auth/0/token') {
                    svc.token = service['@id'];
                    log("Found token service (" + svc.token + ")");
                } else if (service.profile === 'http://iiif.io/api/auth/0/logout') {
                    svc.logout = service['@id'];
                    log("Found logout service (" + svc.logout + ")");
                    if (service.hasOwnProperty('label')) {
                        svc.logout_label = service.label;
                    }
                }
            }
        }
        // Auth won't work without a token service so delete the
        // auth entry if that is the case
        if (!svc.hasOwnProperty('token')) {
            delete svc.uri;
        }
    }
    return svc;
}

/**
 * Called when the attempt to load full info.json fails.
 *
 * Report failure and then attempt to load the original
 * unauthorized OpenSeadragon again.
 */
function authorization_failure(xhr, error, exception) {
    log("Authorization failed: " + error);
    // Set 3s delay before making viewer again
    setTimeout(function() {
        log();
        make_viewer();
    }, 3000);
}

/**
 * Second part of making authorized viewer, after getting info.json
 * 
 * Called after sucessful load of the authorized info.json. Looks
 * for logout description and displays button if present, then
 * starts OpenSeadragon again with the new info.json object.
 *
 * @param {object} info - the info.json object of the authorized image
 */
function make_authorized_viewer_got_info(info) {
    var svc;
    log("Got full info.json, id=" + info['@id']);
    // Do we have a logout definition?
    svc = find_auth_services(info);
    if (svc.hasOwnProperty('logout')) {
        log("Adding logout button");
        $('#authbox').append("<button id='authbutton' data-auth-svc='" +
            svc.logout + "'>" + svc.logout_label + "</button>");
        $('#authbutton').bind('click', function() {
            log();
            $(frame_wrapper_id).html(iframe_html);
            make_viewer();
        });
    } else {
        log("No logout service");
    }
    // Start OpenSeadragon again with new tile source
    viewer = new OpenSeadragon({
        id: "openseadragon",
        tileSources: info,
        showNavigator: true,
        prefixUrl: osd_prefix_url
    });
}

/**
 * Use token to make authorized viewer
 * 
 * @param {string} token - the access token
 */
function make_authorized_viewer(token) {
    var image_info_uri = image_uri + "/info.json";
    log("Attempting to get " + image_info_uri + " using token");
    $(osd_id).remove();
    $(authbox_id).empty();
    $(container_id).append(osd_div);
    $.ajax({ url: image_info_uri,
             headers: {"Authorization": "Bearer " + token},
             cache: false,
             success: make_authorized_viewer_got_info,
             error: authorization_failure });
}

/**
 * Receive postMessage from iFrame to get access token
 *
 * This code copied from 
 * <http://iiif.io/api/auth/0.9/#example-token-requests-and-responses>
 */
function receive_message(event) {
    var data = event.data,
        token, expires, explanation;
    log("Received postMessage");
    if (data.hasOwnProperty('accessToken')) {
        token = data.accessToken;
        expires = null;
        if (data.hasOwnProperty('expiresIn')) {
            expires = parseInt(data.expiresIn, 10);
        }
        log("Extracted access token (" + token + " , " + expires + ")");
        if (expires > 0) {
            // Set up next request to get access token
            setTimeout(request_access_token, 1000*expires);
        }
        if (!viewer_authed) {
            viewer_authed = true;
            make_authorized_viewer(token);
        }
    } else {
        explanation = "no description in response";
        if (data.hasOwnProperty("description")) {
            explanation = data.description;
        }
        log("Failed to extract access token: " + explanation);
        // restart unauthorized viewer
        log();
        if (viewer_authed) {
            viewer_authed = false;
            make_viewer();
        }
    }
}

/**
 * Get window document origin.
 *
 * Not all browsers support window.location.origin.
 */
function origin() {
    if (!window.location.origin) {
        window.location.origin = window.location.protocol + "//" +
            window.location.hostname +
            (window.location.port ? ':' + window.location.port: '');
    }
    return window.location.origin;
}

/**
 * Attempt to get access token via postMessage to iFrame
 *
 * FIXME - Should add some useful timeout here that gets canceled if
 * a message is received. Otherwise we just get a hang if no postMessage
 * comes back.
 */
function request_access_token() {
    // register an event listener to receive a cross domain message:
    window.addEventListener("message", receive_message);
    // now attempt to get token by accessing token service from iFrame
    log("Requesting access token via iFrame");    
    $(message_frame_id).attr({'src': token_service_uri +
        '?messageId=1&origin=' + origin()});
}

/**
 * Handler for login action
 *
 * When the login button has been pressed, clickthrough completed, or
 * immediately in the case of kiosk interaction, we must then open a new 
 * window to interact with the login service. 
 *
 * In the case of login interaction this is where the user will interact 
 * with the login service, in other cases there will be no user interaction
 * in the new window. All we can tell is when that window is closed, at 
 * which point we try to get an access token (which is expected to work 
 * only if auth was successful).
 */
function do_auth(event) {
    var login = $(this).attr('data-auth-svc'),
        win, pollTimer;
    viewer_authed = false;
    // The redirected to window will self-close
    // open/closed state is the only thing we can see across domains :(
    log();
    log("Opening window for login");
    win = window.open(login, 'loginwindow');
    // Check for window close at 0.1s intervals
    pollTimer = window.setInterval(function() { 
        if (win.closed) {
            window.clearInterval(pollTimer);
            log("Detected login window close (success or not unknown)");
            request_access_token();
        }
    }, 100);
}

/**
 * Santize HTML received before displaying
 *
 * FIXME - Do something other than pass-through...
 */
function sanitize_html(html) {
    return html;
}

/**
 * Handler for OpenSeadragon event used as hook to get login information
 *
 * The action of the clicking the login button is tied to the
 * do_auth(..) method.
 *
 * @param event
 */
function add_auth_options(info) {
    var svc;
    svc = find_auth_services(info);
    // This only gets called when we're NOT authed, so no need to put in logout
    if (svc.hasOwnProperty('uri')) {
        // Show header and/or description if givem
        if (svc.hasOwnProperty('header')) {
            $('#authbox').append("<b>" + sanitize_html(svc.header) + "</b><br/>");
        }
        if (svc.hasOwnProperty('description')) {
            $('#authbox').append(sanitize_html(svc.description) + "<br/>");
        }
        token_service_uri = svc.token; // FIXME - stash token URI for later
        if (svc.pattern === 'kiosk') {
            log("Kiosk pattern so no user interaction required");
            $('#authbox').append("<button id='authbutton' " +
                "style='display: none' data-auth-svc='" + 
                svc.uri + '?origin=' + origin() + "'>x</button>");
        } else if (svc.pattern === 'clickthrough') {
            log("Adding clickthrough button");
            $('#authbox').append("<button id='authbutton' data-auth-svc='" + 
                svc.uri + '?origin=' + origin() + "'>" +
                svc.confirm_label + "</button>");
        } else {
            log("Adding login button");
            $('#authbox').append("<button id='authbutton' data-auth-svc='" + 
                svc.uri + '?origin=' + origin() + "'>" +
                svc.login_label + "</button>");
        }
        $('#authbutton').bind('click', do_auth);
        if (svc.pattern === 'kiosk') {
           $('#authbutton').click();
        }
    } else {
        log("No authentication service");
    }
}


function make_viewer_got_info(info, status) {
    $(osd_id).remove();
    $(container_id).append(osd_div);
    if (status === 200) {
        log("Starting viewer for " + info['@id'] + " (" + status + ")");
        var viewer = new OpenSeadragon({
            id: "openseadragon",
            tileSources: info,
            showNavigator: true,
            prefixUrl: osd_prefix_url
        });
    } else {
        log("HTTP status " + status + ", not starting viewer for " + info['@id']);
    }
}

/**
 * Make an OpenSeadragon viewer
 *
 * @param {string} image_uri_in - optionally the IIIF Image URI (no /info.json or /params/) 
 */
make_viewer = function (image_uri_in) {
    var info = {};
    if (image_uri_in !== undefined) {
        image_uri = image_uri_in;
    }
    log("Getting image information for " + image_uri);
    var client = new XMLHttpRequest();
    var image_info_uri = image_uri + '/info.json';
    client.onload = function() {
        info = $.parseJSON(this.response);
        $('#authbox').empty();
        if (info) {
            add_auth_options(info);
            make_viewer_got_info(info, this.status);
        } else {
            log("Failed to parse image information from " + image_info_uri);
        }
    }
    client.error = function() {
        log("Failed to load image information from " + image_info_uri);
    }
    client.open("GET", image_info_uri);
    client.send();
};

/**
 * Build body of demo page with OpenSeadragon, log, etc.
 *
 * Add all elements of demo page to the <div> with id="demo",
 * and then call make_viewer(image_uri_in).
 *
 * @param {string} image_uri_in - IIIF Image URI (no /info.json or /params/) 
 * @param {string} demo_id - optional override for default <div> id
 */
function make_demo_page(image_uri_in, demo_id) {
    demo_id = demo_id !== undefined ? demo_id : '#demo';
    $(demo_id).empty();
    $(demo_id).append(demo_html);
    $(demo_id).append('<p>IIIF image id: <code><input type="text" size="80" id="image_id" value="' +
                      image_uri_in + '"/></code> <button id="uri_button">Update</button></p>');
    $('#uri_button').bind('click', function() {
        log();
        viewer_authed = false;
        make_viewer($('#image_id').val());
    })
    make_viewer(image_uri_in);
}

return {
    // Public functions
    log: log,
    make_viewer: make_viewer,
    make_demo_page: make_demo_page
};

}());

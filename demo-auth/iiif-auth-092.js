/* IIIF Demo Authentication Library
 * For v0.9.2: http://auth_notes.iiif.io/api/auth/0.9/
 * 
 * Requires OpenSeadragon 121, 200 or higher.
 * Requires jQuery 1.11 or higher.
 *
 * Based on IIIF Auth v0.9 implementation by Robert Sanderson @azaroth42.
 * Simeon Warner @zimeon - 2016-08-10...
 */

/*jslint white: true*/
/*jslint unparam: true*/
/*global $, OpenSeadragon, window, document, setTimeout*/

// Use Revealing Module pattern:
// https://addyosmani.com/resources/essentialjsdesignpatterns/book/#revealingmodulepatternjavascript

var iiif_auth = (function () {
"use strict";

var osd_prefix_url = "openseadragon200/images/",
    osd_div = '<div id="openseadragon" style="width: 600px; height: 400px; border: 2px solid purple" ></div>',
    osd_id = "#openseadragon",
    demo_html =
        '<div id="container" style="width: 605px; height: 405px;"></div>' +
        '<div id="authbox" style="margin-top: 10px; height: 3ex; border: 2px solid red; width: 605px;"></div>' +
        '<div id="log" style="margin-top: 10px; height: 20ex; border: 2px solid green; width: 605px; overflow: auto;"></div>' +
        '<iframe id="messageFrame" style="margin-top: 10px; height: 3ex; border: 2px solid blue; width: 605px;"></iframe>',
    container_id = "#container",
    authbox_id="#authbox",
    log_id = "#log",
    message_frame_id = "#messageFrame",
    token_service_uri = "",
    image_uri = "",
    viewer, // our instance of OpenSeadragon
    linenum = 0, // line number of log text
    make_viewer;

/**
 * Logging window function to show useful debugging output
 * 
 * Requires an HTML element (such as a <div>) with id="log"
 * to which new lines of text are appended on every call.
 *
 * @param {string} text - a line of log text to display
 */
function log(text) {
    linenum += 1;
    $(log_id).prepend("[" + linenum + "] " + text + "<br/>");
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
    var services, login, service, i, len,
        svc = {login_label: "Login",
               logout_label: "Logout"};
    log("Looking for auth service descriptions");
    if (info.hasOwnProperty('service')) {
        if (info.service.hasOwnProperty('@id')) {
            // make array from single service entry
            services = [info.service];
        } else {
            // array of service entries
            services = info.service;
        }
        for (i=0, len=services.length; i < len; i+=1) {
            service=services[i];
            if (service.profile === 'http://iiif.io/api/auth/0/login') {
                svc.login = service['@id'];
                log("Found login service (" + svc.login + ")");
                if (service.hasOwnProperty('label')) {
                    svc.login_label = service.label;
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
        // Login won't work without a token service so delete the
        // login entry if that is the case
        if (!svc.hasOwnProperty('token')) {
            delete svc.login;
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
        log("");
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
    log("Got full info.json");
    // Do we have a logout definition?
    svc = find_auth_services(info);
    if (svc.hasOwnProperty('logout')) {
        log("Adding logout button");
        $('#authbox').append("<button id='authbutton' data-login='" +
            svc.logout + "'>" + svc.logout_label + "</button>");
        $('#authbutton').bind('click', function() {
            log("");
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
    $(osd_id).remove();
    $(authbox_id).empty();
    $(container_id).append(osd_div);
    $.ajax({ url: image_uri+"/info.json",
             headers: {"Authorization": token},
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
        token, explanation;
    log("Received postMessage");
    if (data.hasOwnProperty('accessToken')) {
        token = data.accessToken;
        log("Extracted access token (" + token + ")");
        make_authorized_viewer(token);
    } else {
        explanation = "no description in response";
        if (data.hasOwnProperty("description")) {
            explanation = data.description;
        }
        log("Failed to extract access token: " + explanation);
        // restart unauthorized viewer
        log("");
        make_viewer();
    }
}

/**
 * Attempt to get access token via postMessage to iFrame
 *
 * FIXME - Should spec say something specific about the need to create an iFrame
 * in any particular way?
 *
 * FIXME - Should add some useful timeout here that gets canceled if
 * a message is recieved. Otherwise we just get a hang if no postMessage
 * comes back.
 */
function request_access_token() {
    // register an event listener to receive a cross domain message:
    window.addEventListener("message", receive_message);
    // now attempt to get token by accessing token service from iFrame
    log("Requesting access token via iFrame");        
    document.getElementById(message_frame_id).src = token_service_uri + '?messageId=1234';
}

/**
 * Handler for login action
 *
 * When the login button has been pressed we mus then open a new window
 * where the user will interact with the login service. All we can 
 * tell is when that window is closed, at which point we try to get 
 * an access token (which is expected to work only if auth was successful).
 */
function do_auth(event) {
    var login = $(this).attr('data-login'),
        win, pollTimer;
    // The redirected to window will self-close
    // open/closed state is the only thing we can see across domains :(
    log("Opening window for login");
    win = window.open(login, 'loginwindow');
    pollTimer = window.setInterval(function() { 
        if (win.closed) {
            window.clearInterval(pollTimer);
            log("Detected login window close (success or not unknown)");
            request_access_token();
        }
    }, 500);
}

/**
 * Handler for OpenSeadragon event used as hook to get login information
 *
 * The action of the clicking the login button is tied to the
 * do_auth(..) method.
 *
 * @param event
 */
function handle_open(event) {
    var info = event.eventSource.source,
        svc = find_auth_services(info);
    // This only gets called when we're NOT authed, so no need to put in logout
    if (svc.hasOwnProperty('login')) {
        log("Adding login button");
        $('#authbox').append("<button id='authbutton' data-login='" + 
            svc.login + "'>" + svc.login_label + "</button>");
        $('#authbutton').bind('click', do_auth);
        token_service_uri = svc.token; // FIXME - stash token URI for later
    } else {
        log("No login service");
    }
}

/**
 * Make an OpenSeadragon viewer
 *
 * @param {string} image_uri_in - optionally the IIIF Image URI (no /info.json or /params/) 
 */
make_viewer = function (image_uri_in) {
    if (image_uri_in !== undefined) {
        image_uri = image_uri_in;
    }
    log("Making unauthenticated viewer");

    $('#openseadragon').remove();
    $('#authbox').empty();
    $('#container').append(osd_div);
    var viewer = new OpenSeadragon({
        id: "openseadragon",
        tileSources: image_uri + "/info.json?t=" + new Date().getTime(),
        showNavigator: true,
        prefixUrl: osd_prefix_url
    });
    viewer.addHandler('open', handle_open);
    viewer.addHandler('failed-open', handle_open);
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
    $(demo_id).append('<p>Relies upon image at <code><a href="' +
                      image_uri_in + '">' + image_uri_in + '</a></code>.</p>');
    make_viewer(image_uri_in);
}

return {
    // Public functions
    log: log,
    make_viewer: make_viewer,
    make_demo_page: make_demo_page
};

}());
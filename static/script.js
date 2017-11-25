var googleUser = {};

function onLoad() {
    gapi.load('auth2', function () {
        // Retrieve the singleton for the GoogleAuth library and set up the client.
        auth2 = gapi.auth2.init({
            client_id: '<CLIENT_ID>',
            cookiepolicy: 'single_host_origin',
        });
        if (document.getElementById('customBtn') != null){
            attachSignin(document.getElementById('customBtn'));
        }
    });
};

function attachSignin(element) {
    console.log(element.id);
    auth2.attachClickHandler(element, {},
        function (googleUser) {

            var id_token = googleUser.getAuthResponse().id_token;

            var xhr = new XMLHttpRequest();

            xhr.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {
                    window.location.replace(window.location.href);
                }
            }

            xhr.open('POST', '/gconnect');
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.send('id_token=' + id_token);

        }, function (error) {
            alert(JSON.stringify(error, undefined, 2));
        });
}

function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut();

    var xhr = new XMLHttpRequest();

    xhr.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            window.location.replace(window.location.href);
        }
    }

    xhr.open('GET', '/gdisconnect');
    xhr.send();
}


var socket = io.connect('http://' + document.domain + ':' + location.port);
var status = null;
socket.on('connect', function() {
  $('.status').html("Connected")
  socket.emit('status', {})
});
socket.on('connect_error', function() {
  $('.status').html("Error connecting");
});
socket.on('connect_timeout', function() {
  $('.status').html("Connection timeout");
});

socket.on('disconnect', function() {
  $('.status').html("Disconnected");
  status = null;
});

socket.on('status', function(data) {
  if (data.status === undefined) {
    error("Bad status response");
    return;
  }
  console.log("status: " + JSON.stringify(data));
  status = data.status.code;
  $('.status').html(data.status.text);
  $('.credit').html(data.status.creditText);
});

socket.on('error', function(data) {
  if (data.error === undefined) {
    error("Bad error response");
    return;
  }
  console.log("Error code: " + data.error.code);
  error(data.error.message);
});

socket.on('heartbeat', function(msg) {
  console.log("Heartbeat: " + msg);
});
socket.on('refresh', function(msg) {
  window.location.reload(true);
});

function removeError() {
  $('.error').addClass("hide");
}
function error(msg) {
  $('.error').html(msg);
  $('.error').removeClass("hide");
  window.setTimeout(removeError, 5000);
}

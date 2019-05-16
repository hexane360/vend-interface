$(document).ready(function() {
  $('#vend-request').submit(function(e) {
    event.preventDefault(); //don't actually submit
    $.ajax({
      url: "/api/vend",
      method:"POST",
      data:$(this).serialize(),
      error: function(xhr, status, text) {
      	switch (status) {
          case "timeout": break; //socket should handle connection messages
          case "parsererror": error("Vend address does not exist"); break;
          case "abort": break; //unknown
        }
        console.log(xhr.responseText);
        var data = JSON.parse(xhr.responseText);
        switch (xhr.status) {
          case 404: error("api not found"); break;
          case 400: if (data.error !== undefined)
              error(data.error);
            else
          	  error("Vend address does not exist");
          break;
          case 402: error("Insufficient credit"); break;
          case 409: error("Vending in progress"); break;
          //returned when server is off but haproxy is working:
          case 503: error("Server unavailable"); break;
          default: error("Error requesting vend: " + xhr.status + text);
        }
      },
      success:function(data) {
        //alert("Submitted")
        console.log(data)
      }
    });
  });
  var oldVal = "";
  $('#vend-addr').on('keyup keypress blur change', function(e) {
    //console.log("changed")
    if ($(this).val().length == 2) {
      if ($(this).val() == oldVal) return;
      $.ajax({
        url: "/api/channels/" + $(this).val() + "/price",
        error: function(xhr, status, text) {
          switch (status) {
            case "timeout": break;
            case "parsererror": error("Invalid price received"); break;
            case "abort": break;
          }
          switch (xhr.status) {
            case 404: case 400: $('#vend-addr').val(""); break;
            case 503: error("Server unavailable"); break;
            default: error("Error getting price: " + xhr.status + text);
          }
          $(".price").html("");
          price = null;
        },
        success: function(data) {
          console.log("price: " + data.price)
          $(".price").html(data.text);
          price = data.price;
        }
      });
    } else {
      if ($(this).val().length > 2) { //clear user input
        $(this).val("");
      }
      $(".price").html(""); //price not known, clear it
    }
    oldVal = $(this).val()
  });
  $('body').on('click', function(e) {
    $('#vend-addr').delay(500).select(); //re-select vend address after click
  });
});
$(window).load(function() {
  $('#vend-addr').select(); //auto-select input on load
});

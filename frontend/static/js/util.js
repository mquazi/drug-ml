var imgService = "http://tripod.nih.gov/servlet/renderServletv16";

$(function () {
  var $target = $(".adjustable");
  $("#switch").click(function () {
    if ($target.hasClass("container")) {
      $target.removeClass("container").addClass("container-fluid");
    } else {
      $target.removeClass("container-fluid").addClass("container");
    }
  });
});

function isValid(str, errorMsg) {
  if (str == null || str.trim().length <= 0) {
    alert(errorMsg);
    return false;
  }
  return true;
}

function setActiveMenu(id) {
  $("#" + id).addClass("current-menu-item");
}

$.fn.serializeObject = function () {
  var o = {};
  var a = this.serializeArray();
  $.each(a, function () {
    if (o[this.name] !== undefined) {
      if (!o[this.name].push) {
        o[this.name] = [o[this.name]];
      }
      o[this.name].push(this.value || null);
    } else {
      o[this.name] = this.value || null;
    }
  });
  return o;
};

jQuery.fn.center = function () {
  this.css("position", "absolute");
  this.css(
    "top",
    Math.max(
      0,
      ($(window).height() - $(this).outerHeight()) / 2 + $(window).scrollTop()
    ) + "px"
  );
  this.css(
    "left",
    Math.max(
      0,
      ($(window).width() - $(this).outerWidth()) / 2 + $(window).scrollLeft()
    ) + "px"
  );
  return this;
};
function getURLParameter(name) {
  return (
    decodeURIComponent(
      (new RegExp("[?|&]" + name + "=" + "([^&;]+?)(&|#|;|$)").exec(
        location.search
      ) || [, ""])[1].replace(/\+/g, "%20")
    ) || null
  );
}

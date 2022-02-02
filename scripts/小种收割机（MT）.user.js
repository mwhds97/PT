// ==UserScript==
// @name         小种收割机（MT）
// @version      1.3
// @description  批量下载小体积种子（MT）
// @include      /^https?:\/\/.*m-team.*\/(torrents|adult|movie|music)\.php.*$/
// @grant        GM_download
// @noframes
// ==/UserScript==

(function() {
  'use strict';

  var torrents = document.getElementsByClassName("torrents")[0].rows;
  var buttons = document.getElementById("form_torrent").getElementsByTagName("a");
  for(var i = 1; i < torrents.length; i++) {
    var size = torrents[i].cells[4].textContent;
    var uploader = Number(torrents[i].cells[5].textContent.replace(",", ""));
    if(uploader >= 20 && (size[size.length - 2] === "K" || size[size.length - 2] === "M" && Number(size.substr(0, size.length - 2)) <= 300)) {
      var link = torrents[i].cells[1].getElementsByTagName("a")[0].href;
      var id = link.substr(link.indexOf("=") + 1, link.indexOf("&") - link.indexOf("=") - 1);
      var url = "https://pt.m-team.cc/download.php?id=" + id + "&passkey=&https=1";
      var name = "torrents/" + id + ".torrent";
      GM_download(url, name);
    }
  }
  buttons[buttons.length - 1].click();
})();

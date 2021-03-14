// ==UserScript==
// @name         绝对保种（TTG）
// @version      1.0
// @match        https://totheglory.im/*
// @grant        GM_download
// @noframes
// ==/UserScript==

(function() {
  'use strict';

  var torrents = document.getElementById("torrent_table").rows;
  var buttons = document.getElementsByClassName("mainouter")[0].getElementsByTagName("a");
  for(var i = 1; i < torrents.length; i++){
    var size = torrents[i].cells[6].textContent;
    var peer = torrents[i].cells[8].textContent;
    var uploader = Number(peer.substr(0, peer.indexOf("/")).replace(",", ""));
    if(uploader >= 3 && uploader <= 4 && size[size.length - 2] == "G" && Number(size.substr(0, size.length - 2)) > 1 && Number(size.substr(0, size.length - 2)) <= 1.1){
      var link = torrents[i].cells[1].getElementsByTagName("a")[0].href;
      var id = link.substr(link.lastIndexOf("t") + 2, link.length - link.lastIndexOf("t") - 3);
      var url = "https://totheglory.im/dl/" + id + "/";
      var name = "torrents/" + id + ".torrent";
      GM_download(url, name);
    }
  }
  buttons[buttons.length - 2].click();
})();
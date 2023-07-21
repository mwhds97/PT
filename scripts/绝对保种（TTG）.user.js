// ==UserScript==
// @name         绝对保种（TTG）
// @version      1.5
// @description  批量下载绝对保种积分高的种子（TTG）
// @include      /^https?:\/\/.*totheglory.*\/browse\.php.*$/
// @grant        GM_download
// @noframes
// @downloadURL  https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E7%BB%9D%E5%AF%B9%E4%BF%9D%E7%A7%8D%EF%BC%88TTG%EF%BC%89.user.js
// @updateURL    https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E7%BB%9D%E5%AF%B9%E4%BF%9D%E7%A7%8D%EF%BC%88TTG%EF%BC%89.user.js
// ==/UserScript==

(function() {
  'use strict';

  var torrents = document.getElementById("torrent_table").rows;
  var buttons = document.getElementsByClassName("mainouter")[0].getElementsByTagName("a");
  for(var i = 1; i < torrents.length; i++) {
    var size = torrents[i].cells[6].textContent;
    var peer = torrents[i].cells[8].textContent;
    var uploader = Number(peer.substr(0, peer.indexOf("/")).replace(",", ""));
    if(uploader >= 3 && uploader <= 4 && size[size.length - 2] === "G" && Number(size.substr(0, size.length - 2)) > 1 && Number(size.substr(0, size.length - 2)) <= 1.1) {
      var link = torrents[i].cells[1].getElementsByTagName("a")[0].href;
      var id = link.substr(link.lastIndexOf("t") + 2, link.length - link.lastIndexOf("t") - 3);
      var url = "https://totheglory.im/dl/" + id + "/";
      var name = "torrents/" + id + ".torrent";
      GM_download(url, name);
    }
  }
  buttons[buttons.length - 2].click();
})();

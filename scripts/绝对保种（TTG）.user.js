// ==UserScript==
// @name         绝对保种（TTG）
// @version      1.6
// @description  批量下载绝对保种积分高的种子（TTG）
// @match        http*://*.totheglory.im/browse.php*
// @grant        GM_download
// @noframes
// @downloadURL  https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E7%BB%9D%E5%AF%B9%E4%BF%9D%E7%A7%8D%EF%BC%88TTG%EF%BC%89.user.js
// @updateURL    https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E7%BB%9D%E5%AF%B9%E4%BF%9D%E7%A7%8D%EF%BC%88TTG%EF%BC%89.user.js
// ==/UserScript==

(function() {
  'use strict';

  let torrents = document.getElementById("torrent_table").rows;
  let buttons = document.getElementsByClassName("mainouter")[0].getElementsByTagName("a");
  for(let torrent of torrents) {
    let size = torrent.cells[6].textContent;
    let peer = torrent.cells[8].textContent;
    let uploader = Number(peer.substr(0, peer.indexOf("/")).replace(",", ""));
    if(uploader >= 3 && uploader <= 4 && size[size.length - 2] === "G" && Number(size.substr(0, size.length - 2)) > 1 && Number(size.substr(0, size.length - 2)) <= 1.1) {
      let link = torrent.cells[1].getElementsByTagName("a")[0].href;
      let id = link.substr(link.lastIndexOf("t") + 2, link.length - link.lastIndexOf("t") - 3);
      let url = "https://totheglory.im/dl/" + id + "/";
      let name = "torrents/" + id + ".torrent";
      GM_download(url, name);
    }
  }
  buttons[buttons.length - 2].click();
})();

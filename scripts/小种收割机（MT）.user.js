// ==UserScript==
// @name         小种收割机（MT）
// @version      1.7
// @description  批量下载小体积种子（MT）
// @match        http*://*.m-team.cc/torrents.php*
// @match        http*://*.m-team.cc/adult.php*
// @match        http*://*.m-team.cc/movie.php*
// @match        http*://*.m-team.cc/music.php*
// @grant        GM_download
// @noframes
// @downloadURL  https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E5%B0%8F%E7%A7%8D%E6%94%B6%E5%89%B2%E6%9C%BA%EF%BC%88MT%EF%BC%89.user.js
// @updateURL    https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E5%B0%8F%E7%A7%8D%E6%94%B6%E5%89%B2%E6%9C%BA%EF%BC%88MT%EF%BC%89.user.js
// ==/UserScript==

(function() {
    'use strict';

    let torrents = document.getElementsByClassName("torrents")[0].rows;
    let buttons = document.getElementById("form_torrent").getElementsByTagName("a");
    for(let torrent of torrents) {
        let size = torrent.cells[4].textContent;
        let uploader = Number(torrent.cells[5].textContent.replace(",", ""));
        if(uploader >= 20 && (size[size.length - 2] === "K" || size[size.length - 2] === "M" && Number(size.substr(0, size.length - 2)) <= 300)) {
            let link = torrent.cells[1].getElementsByTagName("a")[0].href;
            let id = link.substr(link.indexOf("=") + 1, link.indexOf("&") - link.indexOf("=") - 1);
            let url = "https://pt.m-team.cc/download.php?id=" + id + "&passkey=&https=1";
            let name = "torrents/" + id + ".torrent";
            GM_download(url, name);
        }
    }
    buttons[buttons.length - 1].click();
})();

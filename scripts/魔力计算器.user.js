// ==UserScript==
// @name         魔力计算器
// @version      1.7
// @author       mwhds97
// @match        *.u2.dmhy.org/mpseed.php*
// @match        *.m-team.cc/mybonus.php*
// @match        *.hdchina.org/mybonus.php*
// @match        *.chdbits.co/mybonus.php*
// @match        *.hdsky.me/mybonus.php*
// @match        *.ourbits.club/mybonus.php*
// @match        *.open.cd/mybonus.php*
// @match        *.u2.dmhy.org/torrents.php*
// @match        *.m-team.cc/torrents.php*
// @match        *.m-team.cc/adult.php*
// @match        *.m-team.cc/movie.php*
// @match        *.hdchina.org/torrents.php*
// @match        *.chdbits.co/torrents.php*
// @match        *.hdsky.me/torrents.php*
// @match        *.ourbits.club/torrents.php*
// @match        *.ourbits.club/rescue.php*
// @match        *.open.cd/torrents.php*
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function() {
  'use strict';

  if(typeof(GM_getValue("first")) == "undefined" && (document.URL.includes("torrents.php") || document.URL.includes("adult.php") || document.URL.includes("movie.php") || document.URL.includes("rescue.php"))) {
    alert("请点击列表标题以获取或更新必要参数");
    GM_setValue("first", "blood");
  }

  function calcU(S, L, SD, U, D, type) {
    var params = GM_getValue("U2");
    var P = Math.max(/DVDISO|BDMV|Lossless/.test(type) ? params.Pa : params.Pb, Math.max(2 - U, 0) * Math.min(D, 1));
    if(L < params.Lmin) {
      L = 0;
    }
    if(L > params.Lmax) {
      L = params.Lmax;
    }
    return params.d + P * ((params.b * S / params.S0) + (params.e * L * params.SD0 / SD));
  }
  function calcA(S, T, N, site) {
    var params = GM_getValue(site);
    return (1 - Math.pow(10, -T / params.T0)) * S * (1 + Math.sqrt(2) * Math.pow(10, -(N - 1) / (params.N0 - 1)));
  }
  function calcA_HDC(S, T, N, official) {
    var params = GM_getValue("HDC");
    if(S * 1024 < params.Smin) {
      return 0;
    }
    if(official) {
      return (1 - Math.pow(10, -T / params.T0)) * S * (1 + Math.sqrt(2) * Math.pow(10, -(N - 1) / (params.N0 - 1))) * (params.M / (params.M + N - 1)) * params.Ra;
    }
    else {
      return (1 - Math.pow(10, -T / params.T0)) * (400 / Math.PI * Math.atan(S / 100)) * (1 + Math.sqrt(2) * Math.pow(10, -(N - 1) / (params.N0 - 1))) * (params.M / (params.M + N - 1)) * params.Rb;
    }
  }
  function calcA_HDS(S, T, N, official) {
    var params = GM_getValue("HDS");
    return (1 - Math.pow(10, -T / params.T0)) * S * (official ? params.Ka : params.Kb) * (1 + Math.sqrt(2) * Math.pow(10, -(N - 1) / (params.N0 - 1))) * (params.M / (N + 1));
  }
  function calcB(A, site) {
    var params = GM_getValue(site);
    return params.B0 * 2 / Math.PI * Math.atan(A / params.L);
  }
  function size_G(size_str) {
    var size = /(\d+(?:\.\d+)?)[\n\s]*([KMGT])?i?B/.exec(size_str);
    if(typeof(size[2]) == "undefined") {
      return parseFloat(size[1]) / 1073741824;
    }
    else if(size[2] == "K") {
      return parseFloat(size[1]) / 1048576;
    }
    else if(size[2] == "M") {
      return parseFloat(size[1]) / 1024;
    }
    else if(size[2] == "G") {
      return parseFloat(size[1]);
    }
    else {
      return parseFloat(size[1]) * 1024;
    }
  }

  var params = {};
  if(document.URL.includes("u2.dmhy.org/mpseed.php")) {
    params = /S0=(\d+(?:\.\d+)?)G[\s\S]*b=(\d+(?:\.\d+)?)[\s\S]*d=(\d+(?:\.\d+)?)[\s\S]*E\D*(\d+(?:\.\d+)?)\D*L\D*(\d+(?:\.\d+)?)[\s\S]*SD0=(\d+(?:\.\d+)?)[\s\S]*e=(\d+(?:\.\d+)?)[\s\S]*Pmin\D*(\d+(?:\.\d+)?)\D*(\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("embedded")[1].innerText);
    GM_setValue("U2", {"S0": parseFloat(params[1]), "b": parseFloat(params[2]), "d": parseFloat(params[3]), "Lmin": parseFloat(params[4]), "Lmax": parseFloat(params[5]), "SD0": parseFloat(params[6]), "e": parseFloat(params[7]), "Pa": parseFloat(params[8]), "Pb": parseFloat(params[9])});
  }
  if(document.URL.includes("m-team.cc/mybonus.php")) {
    params = /(\d+(?:\.\d+)?)\D*(\d+(?:\.\d+)?)[\s\S]*T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*-\s*(\d+(?:\.\d+)?).*(?:\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("MT", {"d": parseFloat(params[1]), "Umax": parseFloat(params[2]), "T0": parseFloat(params[3]), "N0": parseFloat(params[4]), "B0": parseFloat(params[5]), "L": parseFloat(params[6]), "sum": parseFloat(params[7])});
  }
  if(document.URL.includes("hdchina.org/mybonus.php")) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*M = (\d+(?:\.\d+)?)[\s\S]*{\n(\d+(?:\.\d+)?),\n(\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?)[\s\S]*\D+(\d+(?:\.\d+)?)M/.exec(document.getElementsByClassName("normal_tab mybonus")[2].innerText);
    GM_setValue("HDC", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "M": parseFloat(params[5]), "Ra": parseFloat(params[6]), "Rb": parseFloat(params[7]), "A0": parseFloat(params[8]), "Smin": parseFloat(params[9])});
  }
  if(document.URL.includes("chdbits.co/mybonus.php")) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("CHD", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(document.URL.includes("hdsky.me/mybonus.php")) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*M=(\d+(?:\.\d+)?)[\s\S]*K=(\d+(?:\.\d+)?).*K=(\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("HDS", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "M": parseFloat(params[5]), "Ka": parseFloat(params[6]), "Kb": parseFloat(params[7]), "A0": parseFloat(params[8])});
  }
  if(document.URL.includes("ourbits.club/mybonus.php")) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("OB", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(document.URL.includes("open.cd/mybonus.php")) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("OCD", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }

  var i, L, S, T, N, SD, U, D, A, table, index_A, index_B;
  if(document.URL.includes("u2.dmhy.org/torrents.php")) {
    table = document.getElementsByClassName("torrents")[0];
    index_A = table.rows[0].cells.length;
    index_B = table.rows[0].cells.length + 1;
    table.rows[0].insertCell(index_A);
    table.rows[0].insertCell(index_B);
    table.rows[0].cells[index_A].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mpseed.php">UCoin</a></td>';
    table.rows[0].cells[index_B].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mpseed.php">麻瓜</a></td>';
    for(i = 1; i < table.rows.length; i++) {
      var type = table.rows[i].cells[0].innerText;
      var pro = /pro.*alt="([\w\s%]+)"/.exec(table.rows[i].cells[1].innerHTML);
      L = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[3].innerHTML)[1]).getTime()) / 86400;
      S = size_G(table.rows[i].cells[4].innerText);
      SD = parseFloat(table.rows[i].cells[5].innerText);
      if(pro === null) {
        U = 1.0;
        D = 1.0;
      }
      else if(pro[1] == "FREE") {
        U = 1.0;
        D = 0.0;
      }
      else if(pro[1] == "2X") {
        U = 2.0;
        D = 1.0;
      }
      else if(pro[1] == "2X Free") {
        U = 2.0;
        D = 0.0;
      }
      else if(pro[1] == "50%") {
        U = 1.0;
        D = 0.5;
      }
      else if(pro[1] == "2X 50%") {
        U = 2.0;
        D = 0.5;
      }
      else if(pro[1] == "30%") {
        U = 1.0;
        D = 0.3;
      }
      else {
        var factors = /<b>(\d+(?:\.\d+)?)X<\/b>.*<b>(\d+(?:\.\d+)?)X<\/b>/.exec(table.rows[i].cells[1].innerHTML);
        U = parseFloat(factors[1]);
        D = parseFloat(factors[2]);
      }
      table.rows[i].insertCell(index_A);
      table.rows[i].insertCell(index_B);
      table.rows[i].cells[index_A].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_B].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_A].innerText = calcU(S, L ,SD + 1, U, D, type).toFixed(3);
      table.rows[i].cells[index_B].innerText = calcU(S, L ,SD + 1, 1.0, 1.0, type).toFixed(3);
    }
  }
  if(document.URL.includes("m-team.cc/torrents.php") || document.URL.includes("m-team.cc/adult.php") || document.URL.includes("m-team.cc/movie.php")) {
    table = document.getElementsByClassName("torrents")[0];
    index_A = table.rows[0].cells.length - 2;
    index_B = table.rows[0].cells.length - 1;
    table.rows[0].insertCell(index_A);
    table.rows[0].insertCell(index_B);
    table.rows[0].cells[index_A].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">A值</a></td>';
    table.rows[0].cells[index_B].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">B值增量</a></td>';
    var seeding = parseFloat(/gif"\>(\d+)/.exec(document.getElementById("info_block").innerHTML)[1]);
    if(seeding > GM_getValue("MT").Umax) {
      seeding = GM_getValue("MT").Umax;
    }
    var A0 = GM_getValue("MT").L * Math.tan((GM_getValue("MT").sum - seeding * GM_getValue("MT").d) * Math.PI / (2 * GM_getValue("MT").B0));
    for(i = 1; i < table.rows.length; i++) {
      T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[3].innerHTML)[1]).getTime()) / 604800;
      S = size_G(table.rows[i].cells[4].innerText);
      N = parseFloat(table.rows[i].cells[5].innerText);
      A = calcA(S, T, N + 1, "MT");
      table.rows[i].insertCell(index_A);
      table.rows[i].insertCell(index_B);
      table.rows[i].cells[index_A].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_B].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_A].innerText = A.toFixed(3);
      table.rows[i].cells[index_B].innerText = (calcB(A0 + A, "MT") - calcB(A0, "MT")).toFixed(3);
    }
  }
  if(document.URL.includes("hdchina.org/torrents.php")) {
    table = document.getElementsByClassName("torrent_list")[0];
    index_A = table.rows[0].cells.length - 1;
    index_B = table.rows[0].cells.length;
    table.rows[0].insertCell(index_A);
    table.rows[0].insertCell(index_B);
    table.rows[0].cells[index_A].outerHTML = '<th style="text-decoration: underline;"><a href="mybonus.php">A值</a></th>';
    table.rows[0].cells[index_B].outerHTML = '<th style="text-decoration: underline;"><a href="mybonus.php">B值增量</a></th>';
    for(i = 1; i < table.rows.length; i++) {
      T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[3].innerHTML)[1]).getTime()) / 604800;
      S = size_G(table.rows[i].cells[4].innerText);
      N = parseFloat(table.rows[i].cells[5].innerText);
      A = calcA_HDC(S, T, N + 1, /HDChina|HDCTV|HDWinG|HDWTV|HDC/.test(table.rows[i].cells[1].innerText));
      table.rows[i].insertCell(index_A);
      table.rows[i].insertCell(index_B);
      table.rows[i].cells[index_A].outerHTML = '<td class="t_size" style="font-size: 12px;"></td>';
      table.rows[i].cells[index_B].outerHTML = '<td class="t_time" style="font-size: 12px;"></td>';
      table.rows[i].cells[index_A].innerText = A.toFixed(3);
      table.rows[i].cells[index_B].innerText = (calcB(GM_getValue("HDC").A0 + A, "HDC") - calcB(GM_getValue("HDC").A0, "HDC")).toFixed(3);
    }
  }
  if(document.URL.includes("chdbits.co/torrents.php")){
    table = document.getElementsByClassName("torrents")[0];
    index_A = table.rows[0].cells.length - 2;
    index_B = table.rows[0].cells.length - 1;
    table.rows[0].insertCell(index_A);
    table.rows[0].insertCell(index_B);
    table.rows[0].cells[index_A].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">A值</a></td>';
    table.rows[0].cells[index_B].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">B值增量</a></td>';
    for(i = 1; i < table.rows.length; i++) {
      T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[3].innerHTML)[1]).getTime()) / 604800;
      S = size_G(table.rows[i].cells[4].innerText);
      N = parseFloat(table.rows[i].cells[5].innerText);
      A = calcA(S, T, N + 1, "CHD");
      table.rows[i].insertCell(index_A);
      table.rows[i].insertCell(index_B);
      table.rows[i].cells[index_A].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_B].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_A].innerText = A.toFixed(3);
      table.rows[i].cells[index_B].innerText = (calcB(GM_getValue("CHD").A0 + A, "CHD") - calcB(GM_getValue("CHD").A0, "CHD")).toFixed(3);
    }
  }
  if(document.URL.includes("hdsky.me/torrents.php")){
    table = document.getElementsByClassName("torrents progresstable")[0];
    index_A = table.rows[0].cells.length - 2;
    index_B = table.rows[0].cells.length - 1;
    table.rows[0].insertCell(index_A);
    table.rows[0].insertCell(index_B);
    table.rows[0].cells[index_A].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">A值</a></td>';
    table.rows[0].cells[index_B].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">B值增量</a></td>';
    for(i = 1; i < table.rows.length; i++) {
      T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[3].innerHTML)[1]).getTime()) / 604800;
      S = size_G(table.rows[i].cells[4].innerText);
      N = parseFloat(table.rows[i].cells[5].innerText);
      A = calcA_HDS(S, T, N + 1, /HDSky|HDS|HDS3D|HDSTV|HDSWEB|HDSPad|HDSCD|HDSpecial|HDSAB/.test(table.rows[i].cells[1].innerText));
      table.rows[i].insertCell(index_A);
      table.rows[i].insertCell(index_B);
      table.rows[i].cells[index_A].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_B].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_A].innerText = A.toFixed(3);
      table.rows[i].cells[index_B].innerText = (calcB(GM_getValue("HDS").A0 + A, "HDS") - calcB(GM_getValue("HDS").A0, "HDS")).toFixed(3);
    }
  }
  if(document.URL.includes("ourbits.club/torrents.php") || document.URL.includes("ourbits.club/rescue.php")){
    table = document.getElementsByClassName("torrents")[0];
    index_A = table.rows[0].cells.length - 2;
    index_B = table.rows[0].cells.length - 1;
    table.rows[0].insertCell(index_A);
    table.rows[0].insertCell(index_B);
    table.rows[0].cells[index_A].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">A值</a></td>';
    table.rows[0].cells[index_B].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">B值增量</a></td>';
    for(i = 1; i < table.rows.length; i++) {
      T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[3].innerHTML)[1]).getTime()) / 604800;
      S = size_G(table.rows[i].cells[4].innerText);
      N = parseFloat(table.rows[i].cells[5].innerText);
      A = calcA(S, T, N + 1, "OB");
      table.rows[i].insertCell(index_A);
      table.rows[i].insertCell(index_B);
      table.rows[i].cells[index_A].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_B].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_A].innerText = A.toFixed(3);
      table.rows[i].cells[index_B].innerText = (calcB(GM_getValue("OB").A0 + A, "OB") - calcB(GM_getValue("OB").A0, "OB")).toFixed(3);
    }
  }
  if(document.URL.includes("open.cd/torrents.php")){
    table = document.getElementsByClassName("torrents")[0];
    index_A = table.rows[0].cells.length - 1;
    index_B = table.rows[0].cells.length;
    table.rows[0].insertCell(index_A);
    table.rows[0].insertCell(index_B);
    table.rows[0].cells[index_A].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">A值</a></td>';
    table.rows[0].cells[index_B].outerHTML = '<td class="colhead" style="text-decoration: underline;"><a href="mybonus.php">B值增量</a></td>';
    for(i = 1; i < table.rows.length; i++) {
      T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[5].innerHTML)[1]).getTime()) / 604800;
      S = size_G(table.rows[i].cells[6].innerText);
      N = parseFloat(table.rows[i].cells[7].innerText);
      A = calcA(S, T, N + 1, "OCD");
      table.rows[i].insertCell(index_A);
      table.rows[i].insertCell(index_B);
      table.rows[i].cells[index_A].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_B].outerHTML = '<td class="rowfollow nowrap"></td>';
      table.rows[i].cells[index_A].innerText = A.toFixed(3);
      table.rows[i].cells[index_B].innerText = (calcB(GM_getValue("OCD").A0 + A, "OCD") - calcB(GM_getValue("OCD").A0, "OCD")).toFixed(3);
    }
  }
})();

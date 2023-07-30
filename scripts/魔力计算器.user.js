// ==UserScript==
// @name         魔力计算器
// @version      2.14
// @description  计算部分站点各个种子的魔力参数
// @author       mwhds97
// @match        http*://*.u2.dmhy.org/mpseed.php*
// @match        http*://*.u2.dmhy.org/torrents.php*
// @match        http*://*.m-team.cc/mybonus.php*
// @match        http*://*.m-team.cc/torrents.php*
// @match        http*://*.m-team.cc/adult.php*
// @match        http*://*.m-team.cc/movie.php*
// @match        http*://*.m-team.cc/music.php*
// @match        http*://*.hdchina.org/mybonus.php*
// @match        http*://*.hdchina.org/torrents.php*
// @match        http*://*.ptchdbits.co/mybonus.php*
// @match        http*://*.ptchdbits.co/torrents.php*
// @match        http*://*.hdsky.me/mybonus.php*
// @match        http*://*.hdsky.me/torrents.php*
// @match        http*://*.ourbits.club/mybonus.php*
// @match        http*://*.ourbits.club/torrents.php*
// @match        http*://*.open.cd/mybonus.php*
// @match        http*://*.open.cd/torrents.php*
// @match        http*://*.springsunday.net/mybonus.php*
// @match        http*://*.springsunday.net/torrents.php*
// @match        http*://*.springsunday.net/rescue.php*
// @grant        GM_setValue
// @grant        GM_getValue
// @downloadURL  https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E9%AD%94%E5%8A%9B%E8%AE%A1%E7%AE%97%E5%99%A8.user.js
// @updateURL    https://raw.githubusercontent.com/mwhds97/PT/master/scripts/%E9%AD%94%E5%8A%9B%E8%AE%A1%E7%AE%97%E5%99%A8.user.js
// ==/UserScript==

(function() {
  'use strict';

  if(typeof GM_getValue("first") === "undefined" && /(torrents|adult|movie|music|rescue)\.php/.test(document.URL)) {
    alert("请进入魔力页面（U2为做种UCoin日志页面）获取或更新必要参数，否则可能无法正常显示！");
    GM_setValue("first", "blood");
  }

  function calcU(S, L, SD, U, D, type) {
    let params = GM_getValue("U2");
    let P = Math.max(/DVDISO|BDMV|Lossless/.test(type) ? params.Pa : params.Pb, Math.max(2 - U, 0) * Math.min(D, 1));
    if(L < params.Lmin) {
      L = 0;
    }
    if(L > params.Lmax) {
      L = params.Lmax;
    }
    return params.d + P * ((params.b * S / params.S0) + (params.e * L * params.SD0 / SD));
  }
  function calcA(S, T, N, site) {
    let params = GM_getValue(site);
    return (1 - Math.pow(10, -T / params.T0)) * S * (1 + Math.sqrt(2) * Math.pow(10, -(N - 1) / (params.N0 - 1)));
  }
  function calcA_HDC(S, T, N, official) {
    let params = GM_getValue("HDC");
    if(S < params.Smin) {
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
    let params = GM_getValue("HDS");
    return (1 - Math.pow(10, -T / params.T0)) * S * (official ? params.Ka : params.Kb) * (1 + Math.sqrt(2) * Math.pow(10, -(N - 1) / (params.N0 - 1))) * (params.M / (N + 1));
  }
  function calcA_SSD(S, T, N) {
    let params = GM_getValue("SSD");
    return Math.pow(S, S < 1 ? 2 : 0.5) * (0.25 + 0.32 * Math.log(1 + T)) * (0.5 + 2.5 * Math.pow(10, -(N - 1) / (params.N0 - 1)));
  }
  function calcB(A, site) {
    let params = GM_getValue(site);
    return params.B0 * 2 / Math.PI * Math.atan(A / params.L);
  }
  function calcB_SSD(A) {
    let params = GM_getValue("SSD");
    return params.E * Math.log(1 + A / params.D);
  }
  function size_G(size_str) {
    let size = /(\d+(?:\.\d+)?)[\n\s]*([KMGT])?i?B?/.exec(size_str);
    if(typeof size[2] === "undefined") {
      return parseFloat(size[1]) / 1073741824;
    }
    else if(size[2] === "K") {
      return parseFloat(size[1]) / 1048576;
    }
    else if(size[2] === "M") {
      return parseFloat(size[1]) / 1024;
    }
    else if(size[2] === "G") {
      return parseFloat(size[1]);
    }
    else {
      return parseFloat(size[1]) * 1024;
    }
  }
  function CountRows(table) {
    let count = 1;
    for(let i = 1; i < table.rows.length; i++) {
      if(table.rows[i].cells.length === table.rows[0].cells.length) {
        count++;
      }
    }
    return count;
  }

  function Sort(table, key) {
    let len = CountRows(table);
    let rows = new Array(len - 1), values = new Array(len - 1);
    for(let i = 1; i < len; i++) {
      rows[i - 1] = table.rows[i].outerHTML;
      values[i - 1] = parseFloat(table.rows[i].cells[key].innerText);
    }
    for(let i = 0; i < values.length - 1; i++) {
      for(let j = 0; j < values.length - 1 - i; j++) {
        if(values[j] < values[j + 1]) {
          let temp = values[j];
          values[j] = values[j + 1];
          values[j + 1] = temp;
          temp = rows[j];
          rows[j] = rows[j + 1];
          rows[j + 1] = temp;
        }
      }
    }
    for(let i = 1; i < len; i++) {
      table.rows[i].outerHTML = rows[i - 1];
    }
  }

  function MakeMagic(site, table, index_T, index_S, index_N, ...theArgs) {
    let len = CountRows(table);
    switch(site) {
      case "U2": {
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].insertCell(theArgs[2]);
        table.rows[0].insertCell(theArgs[3]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortU">UCoin↓</a></td>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortE">效率↓</a></td>';
        table.rows[0].cells[theArgs[2]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortUM">麻瓜↓</a></td>';
        table.rows[0].cells[theArgs[3]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortEM">效率↓</a></td>';
        document.getElementById("sortU").addEventListener("click", () => {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortE").addEventListener("click", () => {
          Sort(table, theArgs[1]);
        }, false);
        document.getElementById("sortUM").addEventListener("click", () => {
          Sort(table, theArgs[2]);
        }, false);
        document.getElementById("sortEM").addEventListener("click", () => {
          Sort(table, theArgs[3]);
        }, false);
        for(let i = 1; i < len; i++) {
          table.rows[i].insertCell(theArgs[0]);
          table.rows[i].insertCell(theArgs[1]);
          table.rows[i].insertCell(theArgs[2]);
          table.rows[i].insertCell(theArgs[3]);
          table.rows[i].cells[theArgs[0]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[1]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[2]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[3]].outerHTML = '<td class="rowfollow nowrap"></td>';
        }
        break;
      }
      case "HDC": {
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].insertCell(theArgs[2]);
        table.rows[0].insertCell(theArgs[3]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<th><a href="javascript:;" id="sortS">体积↓</a></th>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<th><a href="javascript:;" id="sortA">A值↓</a></th>';
        table.rows[0].cells[theArgs[2]].outerHTML = '<th><a href="javascript:;" id="sortB">ΔB↓</a></th>';
        table.rows[0].cells[theArgs[3]].outerHTML = '<th><a href="javascript:;" id="sortE">效率↓</a></th>';
        document.getElementById("sortS").addEventListener("click", () => {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortA").addEventListener("click", () => {
          Sort(table, theArgs[1]);
        }, false);
        document.getElementById("sortB").addEventListener("click", () => {
          Sort(table, theArgs[2]);
        }, false);
        document.getElementById("sortE").addEventListener("click", () => {
          Sort(table, theArgs[3]);
        }, false);
        for(let i = 1; i < len; i++) {
          table.rows[i].insertCell(theArgs[0]);
          table.rows[i].insertCell(theArgs[1]);
          table.rows[i].insertCell(theArgs[2]);
          table.rows[i].insertCell(theArgs[3]);
          table.rows[i].cells[theArgs[0]].outerHTML = '<td class="t_size" style="font-size: 12px;"></td>';
          table.rows[i].cells[theArgs[1]].outerHTML = '<td class="t_time" style="font-size: 12px;"></td>';
          table.rows[i].cells[theArgs[2]].outerHTML = '<td class="t_size" style="font-size: 12px;"></td>';
          table.rows[i].cells[theArgs[3]].outerHTML = '<td class="t_time" style="font-size: 12px;"></td>';
        }
        break;
      }
      case "SSD": {
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortA">初始A值↓</a></td>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortE">效率↓</a></td>';
        document.getElementById("sortA").addEventListener("click", () => {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortE").addEventListener("click", () => {
          Sort(table, theArgs[1]);
        }, false);
        for(let i = 1; i < len; i++) {
          table.rows[i].insertCell(theArgs[0]);
          table.rows[i].insertCell(theArgs[1]);
          table.rows[i].cells[theArgs[0]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[1]].outerHTML = '<td class="rowfollow nowrap"></td>';
        }
        break;
      }
      default: {
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].insertCell(theArgs[2]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortA">A值↓</a></td>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortB">ΔB↓</a></td>';
        table.rows[0].cells[theArgs[2]].outerHTML = '<td class="colhead"><a href="javascript:;" id="sortE">效率↓</a></td>';
        document.getElementById("sortA").addEventListener("click", () => {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortB").addEventListener("click", () => {
          Sort(table, theArgs[1]);
        }, false);
        document.getElementById("sortE").addEventListener("click", () => {
          Sort(table, theArgs[2]);
        }, false);
        for(let i = 1; i < len; i++) {
          table.rows[i].insertCell(theArgs[0]);
          table.rows[i].insertCell(theArgs[1]);
          table.rows[i].insertCell(theArgs[2]);
          table.rows[i].cells[theArgs[0]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[1]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[2]].outerHTML = '<td class="rowfollow nowrap"></td>';
        }
        break;
      }
    }
    switch(site) {
      case "U2": {
        for(let i = 1; i < len; i++) {
          let type = table.rows[i].cells[0].innerText;
          let pro = /pro.*alt="([\w\s%]+)"/.exec(table.rows[i].cells[1].innerHTML);
          let U = 1.0, D = 1.0;
          if(pro !== null) {
            switch(pro[1]) {
              case "FREE": {
                U = 1.0;
                D = 0.0;
                break;
              }
              case "2X": {
                U = 2.0;
                D = 1.0;
                break;
              }
              case "2X Free": {
                U = 2.0;
                D = 0.0;
                break;
              }
              case "50%": {
                U = 1.0;
                D = 0.5;
                break;
              }
              case "2X 50%": {
                U = 2.0;
                D = 0.5;
                break;
              }
              case "30%": {
                U = 1.0;
                D = 0.3;
                break;
              }
              default: {
                let factor_up = /class="arrowup".+?<b>(\d+(?:\.\d+)?)X<\/b>/.exec(table.rows[i].cells[1].innerHTML);
                let factor_down = /class="arrowdown".+?<b>(\d+(?:\.\d+)?)X<\/b>/.exec(table.rows[i].cells[1].innerHTML);
                U = factor_up === null ? 1.0 : parseFloat(factor_up[1]);
                D = factor_down === null ? 1.0 : parseFloat(factor_down[1]);
                break;
              }
            }
          }
          let T = (new Date().getTime() - new Date(/(\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2})/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 86400000;
          let S = size_G(table.rows[i].cells[index_S].innerText);
          let N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          let UC = calcU(S, T, N + 1, U, D, type);
          let UCM = calcU(S, T, N + 1, 1.0, 1.0, type);
          table.rows[i].cells[theArgs[0]].innerText = UC.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = (UC / S).toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = UCM.toFixed(3);
          table.rows[i].cells[theArgs[3]].innerText = (UCM / S).toFixed(3);
        }
        break;
      }
      case "MT": {
        let seeding = parseFloat(/gif"\>(\d+)/.exec(document.getElementById("info_block").innerHTML)[1]);
        if(seeding > GM_getValue("MT").Umax) {
          seeding = GM_getValue("MT").Umax;
        }
        let A0 = GM_getValue("MT").L * Math.tan((GM_getValue("MT").sum - seeding * GM_getValue("MT").d) * Math.PI / (2 * GM_getValue("MT").B0));
        for(let i = 1; i < len; i++) {
          let T = (new Date().getTime() - new Date(/(\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2})/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          let S = size_G(table.rows[i].cells[index_S].innerText);
          let N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          let A = calcA(S, T, N + 1, "MT");
          let dB = calcB(A0 + A, "MT") - calcB(A0, "MT");
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = (A / S).toFixed(3);
        }
        break;
      }
      case "HDC": {
        for(let i = 1; i < len; i++) {
          let T = (new Date().getTime() - new Date(/(\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2})/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          let S = size_G(table.rows[i].cells[index_S].innerText);
          let N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          let A = calcA_HDC(S, T, N + 1, /(-|@)HD[CW]/.test(table.rows[i].cells[1].innerText));
          let dB = calcB(GM_getValue("HDC").A0 + A, "HDC") - calcB(GM_getValue("HDC").A0, "HDC");
          table.rows[i].cells[theArgs[0]].innerText = (/(-|@)HD[CW]/.test(table.rows[i].cells[1].innerText) ? S : 400 / Math.PI * Math.atan(S / 100)).toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[3]].innerText = (A / S).toFixed(3);
        }
        break;
      }
      case "HDS": {
        for(let i = 1; i < len; i++) {
          let T = (new Date().getTime() - new Date(/(\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2})/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          let S = size_G(table.rows[i].cells[index_S].innerText);
          let N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          let A = calcA_HDS(S, T, N + 1, /(-|@)HDS/.test(table.rows[i].cells[1].innerText));
          let dB = calcB(GM_getValue("HDS").A0 + A, "HDS") - calcB(GM_getValue("HDS").A0, "HDS");
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = (A / S).toFixed(3);
        }
        break;
      }
      case "SSD": {
        for(let i = 1; i < len; i++) {
          let T = (new Date().getTime() - new Date(/(\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2})/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          let S = size_G(table.rows[i].cells[index_S].innerText);
          let N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          let A = calcA_SSD(S, 0, N + 1);
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = (A / S).toFixed(3);
        }
        break;
      }
      default: {
        for(let i = 1; i < len; i++) {
          let T = (new Date().getTime() - new Date(/(\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2})/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          let S = size_G(table.rows[i].cells[index_S].innerText);
          let N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          let A = calcA(S, T, N + 1, site);
          let dB = calcB(GM_getValue(site).A0 + A, site) - calcB(GM_getValue(site).A0, site);
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = (A / S).toFixed(3);
        }
        break;
      }
    }
  }

  if(/u2\.dmhy.*mpseed\.php/.test(document.URL)) {
    let params = /(?<!U)S0=(\d+(?:\.\d+)?[KMGT]i?B?)[\s\S]+?b=(\d+(?:\.\d+)?)[\s\S]+?d=(\d+(?:\.\d+)?)[\s\S]+?(\d+(?:\.\d+)?).+?(\d+(?:\.\d+)?)[\s\S]+?SD0=(\d+(?:\.\d+)?)[\s\S]+?e=(\d+(?:\.\d+)?)[\s\S]+?Pmin.+?(\d+(?:\.\d+)?).+?(\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("embedded")[1].innerText);
    GM_setValue("U2", {"S0": size_G(params[1]), "b": parseFloat(params[2]), "d": parseFloat(params[3]), "Lmin": parseFloat(params[4]), "Lmax": parseFloat(params[5]), "SD0": parseFloat(params[6]), "e": parseFloat(params[7]), "Pa": parseFloat(params[8]), "Pb": parseFloat(params[9])});
  }
  if(/m-team.*mybonus\.php/.test(document.URL)) {
    let params = /(\d+(?:\.\d+)?).+?(\d+(?:\.\d+)?)[\s\S]+?T0 = (\d+(?:\.\d+)?)[\s\S]+?N0 = (\d+(?:\.\d+)?)[\s\S]+?B0 = (\d+(?:\.\d+)?)[\s\S]+?L = (\d+(?:\.\d+)?)[\s\S]+?-.+?(\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("MT", {"d": parseFloat(params[1]), "Umax": parseFloat(params[2]), "T0": parseFloat(params[3]), "N0": parseFloat(params[4]), "B0": parseFloat(params[5]), "L": parseFloat(params[6]), "sum": parseFloat(params[7])});
  }
  if(/hdchina.*mybonus\.php/.test(document.URL)) {
    let params = /T0 = (\d+(?:\.\d+)?)[\s\S]+?N0 = (\d+(?:\.\d+)?)[\s\S]+?B0 = (\d+(?:\.\d+)?)[\s\S]+?L = (\d+(?:\.\d+)?)[\s\S]+?M = (\d+(?:\.\d+)?)[\s\S]+?R=[\s\S]+?(\d+(?:\.\d+)?)[\s\S]+?(\d+(?:\.\d+)?)[\s\S]+?A = (\d+(?:\.\d+)?).+?A = (\d+(?:\.\d+)?).+?(\[.+\[)?[\s\S]+?(\d+(?:\.\d+)?[KMGT]i?B?)/.exec(document.getElementsByClassName("normal_tab mybonus")[2].innerText);
    GM_setValue("HDC", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "M": parseFloat(params[5]), "Ra": parseFloat(params[6]), "Rb": parseFloat(params[7]), "A0": parseFloat(params[typeof params[10] === "undefined" ? 9 : 8]), "Smin": size_G(params[11])});
  }
  if(/ptchdbits.*mybonus\.php/.test(document.URL)) {
    let params = /T0 = (\d+(?:\.\d+)?)[\s\S]+?N0 = (\d+(?:\.\d+)?)[\s\S]+?B0 = (\d+(?:\.\d+)?)[\s\S]+?L = (\d+(?:\.\d+)?)[\s\S]+?A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("CHD", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(/hdsky.*mybonus\.php/.test(document.URL)) {
    let params = /T0 = (\d+(?:\.\d+)?)[\s\S]+?N0 = (\d+(?:\.\d+)?)[\s\S]+?B0 = (\d+(?:\.\d+)?)[\s\S]+?L = (\d+(?:\.\d+)?)[\s\S]+?M=(\d+(?:\.\d+)?)[\s\S]+?K=(\d+(?:\.\d+)?).+?K=(\d+(?:\.\d+)?)[\s\S]+?A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("HDS", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "M": parseFloat(params[5]), "Ka": parseFloat(params[6]), "Kb": parseFloat(params[7]), "A0": parseFloat(params[8])});
  }
  if(/ourbits.*mybonus\.php/.test(document.URL)) {
    let params = /T0 = (\d+(?:\.\d+)?)[\s\S]+?N0 = (\d+(?:\.\d+)?)[\s\S]+?B0 = (\d+(?:\.\d+)?)[\s\S]+?L = (\d+(?:\.\d+)?)[\s\S]+?A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("OB", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(/open\.cd.*mybonus\.php/.test(document.URL)) {
    let params = /T0 = (\d+(?:\.\d+)?)[\s\S]+?N0 = (\d+(?:\.\d+)?)[\s\S]+?B0 = (\d+(?:\.\d+)?)[\s\S]+?L = (\d+(?:\.\d+)?)[\s\S]+?A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("OCD", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(/springsunday.*mybonus\.php/.test(document.URL)) {
    let params = /N0 = (\d+(?:\.\d+)?)[\s\S]+?E = (\d+(?:\.\d+)?)[\s\S]+?D = (\d+(?:\.\d+)?)[\s\S]+?(?:[\d\,]+(?:\.\d+)?\s+){5}([\d\,]+(?:\.\d+)?)\s+(?:[\d\,]+(?:\.\d+)?\s+){2}([\d\,]+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("SSD", {"N0": parseFloat(params[1]), "E": parseFloat(params[2]), "D": parseFloat(params[3]), "A0": parseFloat(params[4].replace(/\,/g, "")), "ratio": parseFloat(params[5])});
  }

  if(/u2\.dmhy.*torrents\.php/.test(document.URL)) {
    MakeMagic("U2", document.getElementsByClassName("torrents")[0], 3, 4, 5, 8, 9, 10, 11);
  }
  if(/m-team.*(torrents|adult|movie|music)\.php/.test(document.URL)) {
    MakeMagic("MT", document.getElementsByClassName("torrents")[0], 3, 4, 5, 8, 9, 10);
  }
  if(/hdchina.*torrents\.php/.test(document.URL)) {
    MakeMagic("HDC", document.getElementsByClassName("torrent_list")[0], 3, 4, 5, 8, 9, 10, 11);
  }
  if(/ptchdbits.*torrents\.php/.test(document.URL)) {
    MakeMagic("CHD", document.getElementsByClassName("torrents")[0], 3, 4, 5, 8, 9, 10);
  }
  if(/hdsky.*torrents\.php/.test(document.URL)) {
    MakeMagic("HDS", document.getElementsByClassName("torrents progresstable")[0], 3, 4, 5, 8, 9, 10);
  }
  if(/ourbits.*(torrents|rescue)\.php/.test(document.URL)) {
    MakeMagic("OB", document.getElementsByClassName("torrents")[0], 3, 4, 5, 8, 9, 10);
  }
  if(/open\.cd.*torrents\.php/.test(document.URL)) {
    MakeMagic("OCD", document.getElementsByClassName("torrents")[0], 5, 6, 7, 10, 11, 12);
  }
  if(/springsunday.*(torrents|rescue)\.php/.test(document.URL)) {
    MakeMagic("SSD", document.getElementsByClassName("torrents")[0], 3, 4, 5, 8, 9);
  }
})();

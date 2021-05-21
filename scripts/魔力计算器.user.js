// ==UserScript==
// @name         魔力计算器
// @version      2.4
// @author       mwhds97
// @include      /^https?:\/\/.*(u2.*dmhy|m-team|hdchina|chdbits|hdsky|ourbits|open.*cd|springsunday).*\/(mpseed|mybonus|torrents|rescue|adult|movie|music)\.php.*$/
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function() {
  'use strict';

  if(typeof (GM_getValue("first")) == "undefined" && /(torrents|adult|movie|music|rescue)\.php/.test(document.URL)) {
    alert("请进入魔力页面（U2为做种UCoin日志页面）获取或更新必要参数，否则可能无法正常显示！");
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
  function calcA_SSD(S, T, N) {
    var params = GM_getValue("SSD");
    return Math.sqrt(S) * (0.25 + 0.32 * Math.log(1 + T)) * (0.5 + 2.5 * Math.pow(10, -(N - 1) / (params.N0 - 1)));
  }
  function calcB(A, site) {
    var params = GM_getValue(site);
    return params.B0 * 2 / Math.PI * Math.atan(A / params.L);
  }
  function calcB_SSD(A) {
    var params = GM_getValue("SSD");
    return params.E * Math.log(1 + A / params.D);
  }
  function size_G(size_str) {
    var size = /(\d+(?:\.\d+)?)[\n\s]*([KMGT])?i?B/.exec(size_str);
    if(typeof (size[2]) == "undefined") {
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
  function CountRows(table) {
    var count = 1;
    for(var i = 1; i < table.rows.length; i++) {
      if(table.rows[i].cells.length == table.rows[0].cells.length) {
        count++;
      }
    }
    return count;
  }

  function Sort(table, key) {
    var len = CountRows(table);
    var temp, i, j, rows = new Array(len - 1), values = new Array(len - 1);
    for(i = 1; i < len; i++) {
      rows[i - 1] = table.rows[i].outerHTML;
      values[i - 1] = parseFloat(table.rows[i].cells[key].innerText);
    }
    for(i = 0; i < values.length - 1; i++) {
      for(j = 0; j < values.length - 1 - i; j++) {
        if(values[j] < values[j + 1]) {
          temp = values[j];
          values[j] = values[j + 1];
          values[j + 1] = temp;
          temp = rows[j];
          rows[j] = rows[j + 1];
          rows[j + 1] = temp;
        }
      }
    }
    for(i = 1; i < len; i++) {
      table.rows[i].outerHTML = rows[i - 1];
    }
  }

  function MakeMagic(site, table, index_T, index_S, index_N, ...theArgs) {
    var i, S, T, N, U, D, A, dB, UC, UCM;
    var len = CountRows(table);
    switch(site) {
      case "U2":
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].insertCell(theArgs[2]);
        table.rows[0].insertCell(theArgs[3]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortU">UCoin↓</a></td>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortE">效率↓</a></td>';
        table.rows[0].cells[theArgs[2]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortUM">麻瓜↓</a></td>';
        table.rows[0].cells[theArgs[3]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortEM">效率↓</a></td>';
        document.getElementById("sortU").addEventListener("click", function() {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortE").addEventListener("click", function() {
          Sort(table, theArgs[1]);
        }, false);
        document.getElementById("sortUM").addEventListener("click", function() {
          Sort(table, theArgs[2]);
        }, false);
        document.getElementById("sortEM").addEventListener("click", function() {
          Sort(table, theArgs[3]);
        }, false);
        for(i = 1; i < len; i++) {
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
      case "HDC":
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].insertCell(theArgs[2]);
        table.rows[0].insertCell(theArgs[3]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<th><a href="javascript:void(0)" id="sortS">体积↓</a></th>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<th><a href="javascript:void(0)" id="sortA">A值↓</a></th>';
        table.rows[0].cells[theArgs[2]].outerHTML = '<th><a href="javascript:void(0)" id="sortB">ΔB↓</a></th>';
        table.rows[0].cells[theArgs[3]].outerHTML = '<th><a href="javascript:void(0)" id="sortE">效率↓</a></th>';
        document.getElementById("sortS").addEventListener("click", function() {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortA").addEventListener("click", function() {
          Sort(table, theArgs[1]);
        }, false);
        document.getElementById("sortB").addEventListener("click", function() {
          Sort(table, theArgs[2]);
        }, false);
        document.getElementById("sortE").addEventListener("click", function() {
          Sort(table, theArgs[3]);
        }, false);
        for(i = 1; i < len; i++) {
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
      case "SSD":
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortA">初始A值↓</a></td>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortE">效率↓</a></td>';
        document.getElementById("sortA").addEventListener("click", function() {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortE").addEventListener("click", function() {
          Sort(table, theArgs[1]);
        }, false);
        for(i = 1; i < len; i++) {
          table.rows[i].insertCell(theArgs[0]);
          table.rows[i].insertCell(theArgs[1]);
          table.rows[i].cells[theArgs[0]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[1]].outerHTML = '<td class="rowfollow nowrap"></td>';
        }
        break;
      default:
        table.rows[0].insertCell(theArgs[0]);
        table.rows[0].insertCell(theArgs[1]);
        table.rows[0].insertCell(theArgs[2]);
        table.rows[0].cells[theArgs[0]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortA">A值↓</a></td>';
        table.rows[0].cells[theArgs[1]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortB">ΔB↓</a></td>';
        table.rows[0].cells[theArgs[2]].outerHTML = '<td class="colhead"><a href="javascript:void(0)" id="sortE">效率↓</a></td>';
        document.getElementById("sortA").addEventListener("click", function() {
          Sort(table, theArgs[0]);
        }, false);
        document.getElementById("sortB").addEventListener("click", function() {
          Sort(table, theArgs[1]);
        }, false);
        document.getElementById("sortE").addEventListener("click", function() {
          Sort(table, theArgs[2]);
        }, false);
        for(i = 1; i < len; i++) {
          table.rows[i].insertCell(theArgs[0]);
          table.rows[i].insertCell(theArgs[1]);
          table.rows[i].insertCell(theArgs[2]);
          table.rows[i].cells[theArgs[0]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[1]].outerHTML = '<td class="rowfollow nowrap"></td>';
          table.rows[i].cells[theArgs[2]].outerHTML = '<td class="rowfollow nowrap"></td>';
        }
        break;
    }
    switch(site) {
      case "U2":
        for(i = 1; i < len; i++) {
          var type = table.rows[i].cells[0].innerText;
          var pro = /pro.*alt="([\w\s%]+)"/.exec(table.rows[i].cells[1].innerHTML);
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
          T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 86400000;
          S = size_G(table.rows[i].cells[index_S].innerText);
          N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          UC = calcU(S, T, N + 1, U, D, type);
          UCM = calcU(S, T, N + 1, 1.0, 1.0, type);
          table.rows[i].cells[theArgs[0]].innerText = UC.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = (UC / S).toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = UCM.toFixed(3);
          table.rows[i].cells[theArgs[3]].innerText = (UCM / S).toFixed(3);
        }
        break;
      case "MT":
        var seeding = parseFloat(/gif"\>(\d+)/.exec(document.getElementById("info_block").innerHTML)[1]);
        if(seeding > GM_getValue("MT").Umax) {
          seeding = GM_getValue("MT").Umax;
        }
        var A0 = GM_getValue("MT").L * Math.tan((GM_getValue("MT").sum - seeding * GM_getValue("MT").d) * Math.PI / (2 * GM_getValue("MT").B0));
        for(i = 1; i < len; i++) {
          T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          S = size_G(table.rows[i].cells[index_S].innerText);
          N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          A = calcA(S, T, N + 1, "MT");
          dB = calcB(A0 + A, "MT") - calcB(A0, "MT");
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = (A / S).toFixed(3);
        }
        break;
      case "HDC":
        for(i = 1; i < len; i++) {
          T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          S = size_G(table.rows[i].cells[index_S].innerText);
          N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          A = calcA_HDC(S, T, N + 1, /(-|@)HD[CW]/.test(table.rows[i].cells[1].innerText));
          dB = calcB(GM_getValue("HDC").A0 + A, "HDC") - calcB(GM_getValue("HDC").A0, "HDC");
          table.rows[i].cells[theArgs[0]].innerText = (/(-|@)HD[CW]/.test(table.rows[i].cells[1].innerText) ? S : 400 / Math.PI * Math.atan(S / 100)).toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[3]].innerText = (A / S).toFixed(3);
        }
        break;
      case "HDS":
        for(i = 1; i < len; i++) {
          T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          S = size_G(table.rows[i].cells[index_S].innerText);
          N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          A = calcA_HDS(S, T, N + 1, /(-|@)HDS/.test(table.rows[i].cells[1].innerText));
          dB = calcB(GM_getValue("HDS").A0 + A, "HDS") - calcB(GM_getValue("HDS").A0, "HDS");
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = (A / S).toFixed(3);
        }
        break;
      case "SSD":
        for(i = 1; i < len; i++) {
          T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          S = size_G(table.rows[i].cells[index_S].innerText);
          N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          A = calcA_SSD(S, 0, N + 1);
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = (A / S).toFixed(3);
        }
        break;
      default:
        for(i = 1; i < len; i++) {
          T = (new Date().getTime() - new Date(/title="(.+)"/.exec(table.rows[i].cells[index_T].innerHTML)[1]).getTime()) / 604800000;
          S = size_G(table.rows[i].cells[index_S].innerText);
          N = parseFloat(table.rows[i].cells[index_N].innerText.replace(/\D/g, ""));
          A = calcA(S, T, N + 1, site);
          dB = calcB(GM_getValue(site).A0 + A, site) - calcB(GM_getValue(site).A0, site);
          table.rows[i].cells[theArgs[0]].innerText = A.toFixed(3);
          table.rows[i].cells[theArgs[1]].innerText = dB.toFixed(3);
          table.rows[i].cells[theArgs[2]].innerText = (A / S).toFixed(3);
        }
        break;
    }
  }

  var params = {};
  if(/u2.*mpseed\.php/.test(document.URL)) {
    params = /S0=(\d+(?:\.\d+)?)G[\s\S]*b=(\d+(?:\.\d+)?)[\s\S]*d=(\d+(?:\.\d+)?)[\s\S]*E\D*(\d+(?:\.\d+)?)\D*L\D*(\d+(?:\.\d+)?)[\s\S]*SD0=(\d+(?:\.\d+)?)[\s\S]*e=(\d+(?:\.\d+)?)[\s\S]*Pmin\D*(\d+(?:\.\d+)?)\D*(\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("embedded")[1].innerText);
    GM_setValue("U2", {"S0": parseFloat(params[1]), "b": parseFloat(params[2]), "d": parseFloat(params[3]), "Lmin": parseFloat(params[4]), "Lmax": parseFloat(params[5]), "SD0": parseFloat(params[6]), "e": parseFloat(params[7]), "Pa": parseFloat(params[8]), "Pb": parseFloat(params[9])});
  }
  if(/m-team.*mybonus\.php/.test(document.URL)) {
    params = /(\d+(?:\.\d+)?)\D*(\d+(?:\.\d+)?)[\s\S]*T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*-\s*(\d+(?:\.\d+)?).*(?:\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("MT", {"d": parseFloat(params[1]), "Umax": parseFloat(params[2]), "T0": parseFloat(params[3]), "N0": parseFloat(params[4]), "B0": parseFloat(params[5]), "L": parseFloat(params[6]), "sum": parseFloat(params[7])});
  }
  if(/hdchina.*mybonus\.php/.test(document.URL)) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*M = (\d+(?:\.\d+)?)[\s\S]*{\n(\d+(?:\.\d+)?),\n(\d+(?:\.\d+)?)[\s\S]*(?:A = (\d+(?:\.\d+)?).*A = (?=.*\[.*\[)|A = (\d+(?:\.\d+)?)(?!.*\[.*\[))[\s\S]*\D+(\d+(?:\.\d+)?)M/.exec(document.getElementsByClassName("normal_tab mybonus")[2].innerText);
    GM_setValue("HDC", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "M": parseFloat(params[5]), "Ra": parseFloat(params[6]), "Rb": parseFloat(params[7]), "A0": parseFloat(params[typeof (params[9]) == "undefined" ? 8 : 9]), "Smin": parseFloat(params[10])});
  }
  if(/chdbits.*mybonus\.php/.test(document.URL)) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("CHD", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(/hdsky.*mybonus\.php/.test(document.URL)) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*M=(\d+(?:\.\d+)?)[\s\S]*K=(\d+(?:\.\d+)?).*K=(\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?).*A = /.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("HDS", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "M": parseFloat(params[5]), "Ka": parseFloat(params[6]), "Kb": parseFloat(params[7]), "A0": parseFloat(params[8])});
  }
  if(/ourbits.*mybonus\.php/.test(document.URL)) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?)/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("OB", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(/open.*cd.*mybonus\.php/.test(document.URL)) {
    params = /T0 = (\d+(?:\.\d+)?)[\s\S]*N0 = (\d+(?:\.\d+)?)[\s\S]*B0 = (\d+(?:\.\d+)?)[\s\S]*L = (\d+(?:\.\d+)?)[\s\S]*A = (\d+(?:\.\d+)?).*A = /.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("OCD", {"T0": parseFloat(params[1]), "N0": parseFloat(params[2]), "B0": parseFloat(params[3]), "L": parseFloat(params[4]), "A0": parseFloat(params[5])});
  }
  if(/springsunday.*mybonus\.php/.test(document.URL)) {
    params = /N0 = (\d+(?:\.\d+)?)[\s\S]*E = (\d+(?:\.\d+)?)[\s\S]*D = (\d+(?:\.\d+)?)[\s\S]*(?:[\d\,]+(?:\.\d+)?\s+){5}([\d\,]+(?:\.\d+)?)\s+(?:[\d\,]+(?:\.\d+)?\s+){2}([\d\,]+(?:\.\d+)?)\s+[\d\,]+(?:\.\d+)?/.exec(document.getElementsByClassName("text")[2].innerText);
    GM_setValue("SSD", {"N0": parseFloat(params[1]), "E": parseFloat(params[2]), "D": parseFloat(params[3]), "A0": parseFloat(params[4].replace(/\,/g, "")), "ratio": parseFloat(params[5])});
  }

  var table;
  if(/u2.*torrents\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrents")[0];
    MakeMagic("U2", table, 3, 4, 5, 8, 9, 10, 11);
  }
  if(/m-team.*(torrents|adult|movie|music)\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrents")[0];
    MakeMagic("MT", table, 3, 4, 5, 8, 9, 10);
  }
  if(/hdchina.*torrents\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrent_list")[0];
    MakeMagic("HDC", table, 3, 4, 5, 8, 9, 10, 11);
  }
  if(/chdbits.*torrents\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrents")[0];
    MakeMagic("CHD", table, 3, 4, 5, 8, 9, 10);
  }
  if(/hdsky.*torrents\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrents progresstable")[0];
    MakeMagic("HDS", table, 3, 4, 5, 8, 9, 10);
  }
  if(/ourbits.*(torrents|rescue)\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrents")[0];
    MakeMagic("OB", table, 3, 4, 5, 8, 9, 10);
  }
  if(/open.*cd.*torrents\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrents")[0];
    MakeMagic("OCD", table, 5, 6, 7, 10, 11, 12);
  }
  if(/springsunday.*(torrents|rescue)\.php/.test(document.URL)) {
    table = document.getElementsByClassName("torrents")[0];
    MakeMagic("SSD", table, 4, 5, 6, 9, 10);
  }
})();

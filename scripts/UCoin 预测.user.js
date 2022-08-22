// ==UserScript==
// @name         UCoin 预测
// @version      1.4
// @description  预测当天的 UCoin 收益
// @author       mwhds97
// @include      /^https?:\/\/.*u2.*dmhy.*\/mpseed\.php.*$/
// @grant        none
// @downloadURL  https://cdn.jsdelivr.net/gh/mwhds97/PT@master/scripts/UCoin%20%E9%A2%84%E6%B5%8B.user.js
// @updateURL    https://cdn.jsdelivr.net/gh/mwhds97/PT@master/scripts/UCoin%20%E9%A2%84%E6%B5%8B.user.js
// ==/UserScript==

(function() {
  'use strict';

  var table = document.getElementById("SeedBonusTable").getElementsByTagName("table")[0];
  var index = table.rows.length - 1;
  var lastCell = table.rows[0].cells.length - 1;
  table.insertRow(index);
  for(var i = 0; i <= lastCell; i++) {
    table.rows[index].insertCell(i);
    if(i === 0) {
      table.rows[index].cells[i].innerText = "预测";
    }
    else if(i === lastCell) {
      table.rows[index].cells[i].innerText = "96";
    }
    else {
      table.rows[index].cells[i].innerText = (parseFloat(table.rows[index - 1].cells[i].innerText) / parseFloat(table.rows[index - 1].cells[lastCell].innerText) * 96).toFixed(3);
    }
  }
})();

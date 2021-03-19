// ==UserScript==
// @name         UCoin 预测
// @version      1.0
// @author       mwhds97
// @match        *.u2.dmhy.org/mpseed.php*
// @grant        none
// ==/UserScript==

(function() {
  'use strict';

  var table = document.getElementById("SeedBonusTable").getElementsByTagName("table")[0];
  var index = table.rows.length - 1;
  var lastCell = table.rows[0].cells.length - 1;
  table.insertRow(index);
  for(var i = 0; i <= lastCell; i++) {
    table.rows[index].insertCell(i);
    if(i == 0) {
      table.rows[index].cells[i].innerText = "预测";
    }
    else if(i == lastCell) {
      table.rows[index].cells[i].innerText = "96";
    }
    else {
      table.rows[index].cells[i].innerText = (parseFloat(table.rows[index - 1].cells[i].innerText) / parseFloat(table.rows[index - 1].cells[lastCell].innerText) * 96).toFixed(3);
    }
  }
})();

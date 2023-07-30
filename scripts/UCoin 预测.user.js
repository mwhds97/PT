// ==UserScript==
// @name         UCoin 预测
// @version      1.7
// @description  预测当天的 UCoin 收益
// @author       mwhds97
// @match        http*://*.u2.dmhy.org/mpseed.php*
// @grant        none
// @downloadURL  https://raw.githubusercontent.com/mwhds97/PT/master/scripts/UCoin%20%E9%A2%84%E6%B5%8B.user.js
// @updateURL    https://raw.githubusercontent.com/mwhds97/PT/master/scripts/UCoin%20%E9%A2%84%E6%B5%8B.user.js
// ==/UserScript==

(function() {
    'use strict';

    let table = document.getElementById("SeedBonusTable").getElementsByTagName("table")[0];
    let index = table.rows.length - 1;
    let lastCell = table.rows[0].cells.length - 1;
    table.insertRow(index);
    for(let i = 0; i <= lastCell; i++) {
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

// ==UserScript==
// @name         U2娘+
// @version      1.0
// @author       mwhds97
// @match        *.u2.dmhy.org/*
// @grant        none
// @noframes
// ==/UserScript==

(function() {
  'use strict';

  function CreateButton(form, index, name, value, word) {
    var btn_new = document.createElement("input");
    form.insertBefore(btn_new, form.childNodes[index]);
    btn_new.outerHTML = '<input type="button" id="btn_' + name + '" class="btn" name="btn_' + name + '" value="' + value + '">';
    document.getElementById("btn_" + name).addEventListener("click", function() {
      document.getElementsByName("shbox_text")[0].value = "U2娘 " + word;
      document.getElementById("hbsubmit").click();
    }, false);
  }

  var shbox = document.getElementsByName("shbox")[0];
  for(var i in shbox.childNodes) {
    if(shbox.childNodes[i].value == "清除") {
      i = parseInt(i);
      break;
    }
  }

  CreateButton(shbox, i + 1, "income", "赚分速度", "我的赚分速度");
  CreateButton(shbox, i + 2, "ucoin", "UCoin", "我的UCoin");
  CreateButton(shbox, i + 3, "rich", "比我壕", "U2有多少人比我壕");
  CreateButton(shbox, i + 4, "ratio", "分享率", "我的分享率");
  CreateButton(shbox, i + 5, "real", "实际分享率", "我的实际分享率");
  CreateButton(shbox, i + 6, "skill", "技能", "我的技能");
  CreateButton(shbox, i + 7, "photo", "头像", "看看我的头像");
  CreateButton(shbox, i + 8, "title", "长标题", "长标题");
  CreateButton(shbox, i + 9, "love", "我爱你", "我爱你");
  CreateButton(shbox, i + 10, "warm", "暖被窝", "暖被窝");
  CreateButton(shbox, i + 11, "sex", "求交尾", "求交尾");
  CreateButton(shbox, i + 12, "fall", "平地摔", "平地摔");
  CreateButton(shbox, i + 13, "choc", "巧克力", "巧克力");
  CreateButton(shbox, i + 14, "creed", "教义", "教义");
  CreateButton(shbox, i + 15, "eternal", "+1s", "+1s");
})();

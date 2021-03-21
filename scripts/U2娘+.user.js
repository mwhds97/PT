// ==UserScript==
// @name         U2娘+
// @version      1.5
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
  CreateButton(shbox, i + 2, "myuc", "我的UC", "我的UCoin");
  CreateButton(shbox, i + 3, "alluc", "全站UC", "全站UC存量");
  CreateButton(shbox, i + 4, "rich", "比我壕", "U2有多少人比我壕");
  CreateButton(shbox, i + 5, "afford", "买得起药", "多少人买得起邀请");
  CreateButton(shbox, i + 6, "ratio", "分享率", "我的分享率");
  CreateButton(shbox, i + 7, "real", "实际分享率", "我的实际分享率");
  CreateButton(shbox, i + 8, "sign", "签名条", "签名条");
  CreateButton(shbox, i + 9, "skill", "技能", "我的技能");
  CreateButton(shbox, i + 10, "photo", "头像", "看看我的头像");
  CreateButton(shbox, i + 11, "so", "取向", "我的取向");
  CreateButton(shbox, i + 12, "harem", "后宫", "我的后宫");
  CreateButton(shbox, i + 13, "power", "战斗力", "我的战斗力");
  CreateButton(shbox, i + 14, "ohayo", "早安", "早安");
  CreateButton(shbox, i + 15, "oyasumi", "晚安", "晚安");
  CreateButton(shbox, i + 16, "boy", "男生", "U2有多少男生");
  CreateButton(shbox, i + 17, "girl", "女生", "U2有多少女生");
  CreateButton(shbox, i + 18, "newhalf", "伪娘", "U2有多少伪娘");
  CreateButton(shbox, i + 19, "comfort", "求安慰", "求安慰");
  CreateButton(shbox, i + 20, "daddy", "求包养", "求包养");
  CreateButton(shbox, i + 21, "merge", "求合体", "求合体");
  CreateButton(shbox, i + 22, "date", "求交往", "求交往");
  CreateButton(shbox, i + 23, "sex", "求交尾", "求交尾");
  CreateButton(shbox, i + 24, "sm", "求虐", "求虐");
  CreateButton(shbox, i + 25, "train", "求调教", "求调教");
  CreateButton(shbox, i + 26, "invite", "求邀请", "求邀请");
  CreateButton(shbox, i + 27, "creampie", "求中出", "求中出");
  CreateButton(shbox, i + 28, "lollipop", "棒棒糖", "棒棒糖");
  CreateButton(shbox, i + 29, "transform", "变身", "变身");
  CreateButton(shbox, i + 30, "bkb", "兵库北", "兵库北");
  CreateButton(shbox, i + 31, "title", "长标题", "长标题");
  CreateButton(shbox, i + 32, "roll", "抽种子", "手气不错");
  CreateButton(shbox, i + 33, "comeout", "出柜", "出柜");
  CreateButton(shbox, i + 34, "gohome", "带回家", "跟我回家去");
  CreateButton(shbox, i + 35, "pour", "倒茶", "倒茶");
  CreateButton(shbox, i + 36, "creed", "教义", "教义");
  CreateButton(shbox, i + 37, "dignity", "节操", "掉节操");
  CreateButton(shbox, i + 38, "donate", "捐赠", "捐赠");
  CreateButton(shbox, i + 39, "loli", "萝莉", "萝莉");
  CreateButton(shbox, i + 40, "mahjong", "麻将", "麻将");
  CreateButton(shbox, i + 41, "moe", "卖萌", "卖个萌");
  CreateButton(shbox, i + 42, "head", "摸摸头", "摸摸头");
  CreateButton(shbox, i + 43, "mhsj", "魔法少女", "魔法少女");
  CreateButton(shbox, i + 44, "warm", "暖被窝", "暖被窝");
  CreateButton(shbox, i + 45, "pants", "胖次", "胖次");
  CreateButton(shbox, i + 46, "fall", "平地摔", "平地摔");
  CreateButton(shbox, i + 47, "choc", "巧克力", "巧克力");
  CreateButton(shbox, i + 48, "tea", "请用茶", "请用茶");
  CreateButton(shbox, i + 49, "body", "身体检查", "身体检查");
  CreateButton(shbox, i + 50, "bithday", "生日", "生日");
  CreateButton(shbox, i + 51, "world", "世界线", "世界线");
  CreateButton(shbox, i + 52, "model", "手办", "你的手办多少钱");
  CreateButton(shbox, i + 53, "rabbit", "兔纸", "兔纸");
  CreateButton(shbox, i + 54, "push", "推倒", "推倒");
  CreateButton(shbox, i + 55, "love", "我爱你", "我爱你");
  CreateButton(shbox, i + 56, "back", "我回来了", "我回来了");
  CreateButton(shbox, i + 57, "bath", "洗澡", "洗澡");
  CreateButton(shbox, i + 58, "play", "羞耻play", "羞耻play");
  CreateButton(shbox, i + 59, "eternal", "+1秒", "+1s");
})();

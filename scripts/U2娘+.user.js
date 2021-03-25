// ==UserScript==
// @name         U2娘+
// @version      1.6
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

  var buttons = [{"name": "income", "value": "赚分速度", "word": "我的赚分速度"},
                 {"name": "myuc", "value": "我的UC", "word": "我的UCoin"},
                 {"name": "alluc", "value": "全站UC", "word": "全站UC存量"},
                 {"name": "rich", "value": "比我壕", "word": "U2有多少人比我壕"},
                 {"name": "afford", "value": "买得起药", "word": "多少人买得起邀请"},
                 {"name": "ratio", "value": "分享率", "word": "我的分享率"},
                 {"name": "real", "value": "实际分享率", "word": "我的实际分享率"},
                 {"name": "sign", "value": "签名条", "word": "签名条"},
                 {"name": "skill", "value": "技能", "word": "我的技能"},
                 {"name": "photo", "value": "头像", "word": "看看我的头像"},
                 {"name": "so", "value": "取向", "word": "我的取向"},
                 {"name": "harem", "value": "后宫", "word": "我的后宫"},
                 {"name": "power", "value": "战斗力", "word": "我的战斗力"},
                 {"name": "ohayo", "value": "早安", "word": "早安"},
                 {"name": "oyasumi", "value": "晚安", "word": "晚安"},
                 {"name": "boy", "value": "男生", "word": "U2有多少男生"},
                 {"name": "girl", "value": "女生", "word": "U2有多少女生"},
                 {"name": "newhalf", "value": "伪娘", "word": "U2有多少伪娘"},
                 {"name": "comfort", "value": "求安慰", "word": "求安慰"},
                 {"name": "daddy", "value": "求包养", "word": "求包养"},
                 {"name": "merge", "value": "求合体", "word": "求合体"},
                 {"name": "date", "value": "求交往", "word": "求交往"},
                 {"name": "sex", "value": "求交尾", "word": "求交尾"},
                 {"name": "sm", "value": "求虐", "word": "求虐"},
                 {"name": "train", "value": "求调教", "word": "求调教"},
                 {"name": "invite", "value": "求邀请", "word": "求邀请"},
                 {"name": "creampie", "value": "求中出", "word": "求中出"},
                 {"name": "lollipop", "value": "棒棒糖", "word": "棒棒糖"},
                 {"name": "transform", "value": "变身", "word": "变身"},
                 {"name": "bkb", "value": "兵库北", "word": "兵库北"},
                 {"name": "title", "value": "长标题", "word": "长标题"},
                 {"name": "roll", "value": "抽种子", "word": "手气不错"},
                 {"name": "comeout", "value": "出柜", "word": "出柜"},
                 {"name": "gohome", "value": "带回家", "word": "跟我回家去"},
                 {"name": "pour", "value": "倒茶", "word": "倒茶"},
                 {"name": "creed", "value": "教义", "word": "教义"},
                 {"name": "dignity", "value": "节操", "word": "掉节操"},
                 {"name": "donate", "value": "捐赠", "word": "捐赠"},
                 {"name": "loli", "value": "萝莉", "word": "萝莉"},
                 {"name": "mahjong", "value": "麻将", "word": "麻将"},
                 {"name": "moe", "value": "卖萌", "word": "卖个萌"},
                 {"name": "head", "value": "摸摸头", "word": "摸摸头"},
                 {"name": "mhsj", "value": "魔法少女", "word": "魔法少女"},
                 {"name": "warm", "value": "暖被窝", "word": "暖被窝"},
                 {"name": "pants", "value": "胖次", "word": "胖次"},
                 {"name": "fall", "value": "平地摔", "word": "平地摔"},
                 {"name": "choc", "value": "巧克力", "word": "巧克力"},
                 {"name": "tea", "value": "请用茶", "word": "请用茶"},
                 {"name": "body", "value": "身体检查", "word": "身体检查"},
                 {"name": "bithday", "value": "生日", "word": "生日"},
                 {"name": "world", "value": "世界线", "word": "世界线"},
                 {"name": "model", "value": "手办", "word": "你的手办多少钱"},
                 {"name": "rabbit", "value": "兔纸", "word": "兔纸"},
                 {"name": "push", "value": "推倒", "word": "推倒"},
                 {"name": "love", "value": "我爱你", "word": "我爱你"},
                 {"name": "back", "value": "我回来了", "word": "我回来了"},
                 {"name": "bath", "value": "洗澡", "word": "洗澡"},
                 {"name": "play", "value": "羞耻play", "word": "羞耻play"},
                 {"name": "eternal", "value": "+1秒", "word": "+1s"}];

  var shbox = document.getElementsByName("shbox")[0];
  for(var i in shbox.childNodes) {
    if(shbox.childNodes[i].value == "清除") {
      i = parseInt(i);
      break;
    }
  }
  for(var j = 0; j < buttons.length; j++) {
    CreateButton(shbox, i + j + 1, buttons[j].name, buttons[j].value, buttons[j].word);
  }
})();

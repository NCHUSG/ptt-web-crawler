# ptt-web-crawler (PTT 網路版爬蟲) [![Build Status](https://travis-ci.org/jwlin/ptt-web-crawler.svg?branch=master)](https://travis-ci.org/jwlin/ptt-web-crawler)

[Live demo](http://app.castman.net/ptt-web-crawler)

特色

* 支援單篇及多篇文章抓取
* 過濾資料內空白、空行及特殊字元
* JSON 格式輸出
* 支援 Python 2.6 - 3.4

輸出 JSON 格式

    {
            "article_id": "M.1263537261.A.EA5",
            "article_title": "[心得] 通識/556/台灣紀錄片賞析/紀文章",
            "author": "twfir (台灣杉)",
            "board": "NCHU-Courses",
            "content": {
                "class_t": "556",
                "dept": "新制通識 可採計舊制歷史",
                "enrol_seme": "981",
                "feeling": "點名是傳張紙點名 報告寫的是上課影片的觀後感 很輕鬆\n\n             播放的紀錄片都很有內容 也有國外的片子\n\n             就通識而言 這可能是最輕鬆的一門 看看電影就有學分 收穫也很大",
                "history_record": "",
                "judge": "出席期中期末報告(1000字的影片觀後感",
                "note": "搶很兇 高年級才有機會加簽(4>3>>>>>2)\n            上課跟看電影一樣 請挑個好位子 不要被擋到",
                "prof": "紀文章",
                "textbook": "在綜大1樓的視聽教室播放紀錄片\n                           時間允許的話 會在片後作講解 不用課本或筆記"
            },
            "date": "Fri Jan 15 14:34:19 2010",
            "ip": "None",
            "message_conut": {
                "all": 1,
                "boo": 0,
                "count": 1,
                "neutral": 0,
                "push": 1
            },
            "messages": [{
                "push_content": "好課！",
                "push_ipdatetime": "125.226.24.88 02/01 23:15",
                "push_tag": "推",
                "push_userid": "bpbpbp"
            }]
    }

### 執行方式
    python crawler.py -b 看板名稱 -i 起始索引 結束索引 
    python crawler.py -b 看板名稱 -a 文章ID 

### 範例
    python crawler.py -b PublicServan -i 100 200

會爬取 PublicServan 板第 100 頁 (https://www.ptt.cc/bbs/PublicServan/index100.html) 到第 200 頁 (https://www.ptt.cc/bbs/PublicServan/index200.html) 的內容，輸出至 `PublicServan-100-200.json`

    python crawler.py -b PublicServan -a M.1413618360.A.4F0

會爬取 PublicServan 板文章 ID 為 M.1413618360.A.4F0 (https://www.ptt.cc/bbs/PublicServan/M.1413618360.A.4F0.html) 的內容，輸出至 `PublicServan-M.1413618360.A.4F0.json`

### 測試
    python test.py

***

ptt-web-crawler is a crawler for the web version of PTT, the largest online community in Taiwan. 

    usage: python crawler.py [-h] -b BOARD_NAME (-i START_INDEX END_INDEX | -a ARTICLE_ID) [-v]
    optional arguments:
      -h, --help                  show this help message and exit
      -b BOARD_NAME               Board name
      -i START_INDEX END_INDEX    Start and end index
      -a ARTICLE_ID               Article ID
      -v, --version               show program's version number and exit

Output would be `BOARD_NAME-START_INDEX-END_INDEX.json` (or `BOARD_NAME-ID.json`)

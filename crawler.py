# vim: set ts=4 sw=4 et: -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import re
import sys
import json
import requests
import argparse
import time
import codecs
from bs4 import BeautifulSoup
from six import u

__version__ = '1.0'

# if python 2, disable verify flag in requests.get()
VERIFY = True
if sys.version_info[0] < 3:
    VERIFY = False
    requests.packages.urllib3.disable_warnings()
#全域字典，中文轉英文

chi2en = {
    '修業學年度/學期':'enrol_seme',
    '上課時段':'class_t',
    '課程名稱/授課教師':'prof',
    '所屬類別/開課系所':'dept',
    '上課方式/用書':'textbook',
    '評分方式':'judge',
    '注意事項':'note',
    '心得/結語':'feeling',
    '成績參考':'history_record',

}

def crawler(cmdline=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
        A crawler for the web version of PTT, the largest online community in Taiwan.
        Input: board name and page indices (or articla ID)
        Output: BOARD_NAME-START_INDEX-END_INDEX.json (or BOARD_NAME-ID.json)
    ''')
    parser.add_argument('-b', metavar='BOARD_NAME', help='Board name', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', metavar=('START_INDEX', 'END_INDEX'), type=int, nargs=2, help="Start and end index")
    group.add_argument('-a', metavar='ARTICLE_ID', help="Article ID")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    if cmdline:
        args = parser.parse_args(cmdline)
    else:
       args = parser.parse_args()
    board = args.b
    PTT_URL = 'https://www.ptt.cc'
    if args.i:
        start = args.i[0]
        end = args.i[1]
        index = start
        filename = board + '-' + str(start) + '-' + str(end) + '.json'
        store(filename, u'{"articles": [\n', 'w')
        for i in range(end-start+1):
            index = start + i
            print('Processing index:', str(index))
            resp = requests.get(
                url=PTT_URL + '/bbs/' + board + '/index' + str(index) + '.html',
                cookies={'over18': '1'}, verify=VERIFY
            )
            if resp.status_code != 200:
                print('invalid url:', resp.url)
                continue
            soup = BeautifulSoup(resp.text)
            divs = soup.find_all("div", "r-ent")
            for div in divs:
                try:
                    # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                    href = div.find('a')['href']
                    link = PTT_URL + href
                    article_id = re.sub('\.html', '', href.split('/')[-1])
                    if div == divs[-1] and i == end-start:  # last div of last page
                        store(filename, parse(link, article_id, board) + '\n', 'a')
                    else:
                        store(filename, parse(link, article_id, board) + ',\n', 'a')
                except:
                    pass
            time.sleep(0.1)
        store(filename, u']}', 'a')
    else:  # args.a
        article_id = args.a
        link = PTT_URL + '/bbs/' + board + '/' + article_id + '.html'
        filename = board + '-' + article_id + '.json'
        store(filename, parse(link, article_id, board), 'w')


def parse(link, article_id, board):
    print('Processing article:', article_id)
    resp = requests.get(url=link, cookies={'over18': '1'}, verify=VERIFY)
    if resp.status_code != 200:
        print('invalid url:', resp.url)
        return json.dumps({"error": "invalid url"}, indent=4, sort_keys=True, ensure_ascii=False)
    soup = BeautifulSoup(resp.text)
    main_content = soup.find(id="main-content")
    metas = main_content.select('div.article-metaline')
    author = ''
    title = ''
    date = ''
    if metas:
        author = metas[0].select('span.article-meta-value')[0].string if metas[0].select('span.article-meta-value')[0] else author
        title = metas[1].select('span.article-meta-value')[0].string if metas[1].select('span.article-meta-value')[0] else title
        if '[心得]' not in title:return#因為我們只要課程新的的文，所以就只篩選心得、RE開頭的標題


        date = metas[2].select('span.article-meta-value')[0].string if metas[2].select('span.article-meta-value')[0] else date

        # remove meta nodes
        for meta in metas:
            meta.extract()
        for meta in main_content.select('div.article-metaline-right'):
            meta.extract()

    # remove and keep push nodes
    pushes = main_content.find_all('div', class_='push')
    for push in pushes:
        push.extract()

    try:
        ip = main_content.find(text=re.compile(u'※ 發信站:'))
        ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group()
    except:
        ip = "None"

    # 移除 '※ 發信站:' (starts with u'\u203b'), '◆ From:' (starts with u'\u25c6'), 空行及多餘空白
    # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
    filtered = [ v for v in main_content.stripped_strings if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--'] ]
    expr = re.compile(u(r'[^\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\s\w:/-_.?~%()]'))
    for i in range(len(filtered)):
        filtered[i] = re.sub(expr, '', filtered[i])
    
    filtered = [_f for _f in filtered if _f]  # remove empty strings
    filtered = [x for x in filtered if article_id not in x]  # remove last line containing the url of the article

    content = parse_content(filtered)  
    # content = ' '.join(filtered)
    # content = re.sub(r'(\s)+', ' ', content)
    # print 'content', content

    # push messages
    p, b, n = 0, 0, 0
    messages = []
    for push in pushes:
        if not push.find('span', 'push-tag'):
            continue
        push_tag = push.find('span', 'push-tag').string.strip(' \t\n\r')
        push_userid = push.find('span', 'push-userid').string.strip(' \t\n\r')
        # if find is None: find().strings -> list -> ' '.join; else the current way
        push_content = push.find('span', 'push-content').strings
        push_content = ' '.join(push_content)[1:].strip(' \t\n\r')  # remove ':'
        push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
        messages.append( {'push_tag': push_tag, 'push_userid': push_userid, 'push_content': push_content, 'push_ipdatetime': push_ipdatetime} )
        if push_tag == u'推':
            p += 1
        elif push_tag == u'噓':
            b += 1
        else:
            n += 1

    # count: 推噓文相抵後的數量; all: 推文總數
    message_count = {'all': p+b+n, 'count': p-b, 'push': p, 'boo': b, "neutral": n}

    # print 'msgs', messages
    # print 'mscounts', message_count

    # json data
    data = {
        'board': board,
        'article_id': article_id,
        'article_title': title,
        'author': author,
        'date': date,
        'content': content,
        'ip': ip,
        'message_conut': message_count,
        'messages': messages
    }
    # print 'original:', d
    return json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)


def store(filename, data, mode):
    with codecs.open(filename, mode, encoding='utf-8') as f:
        f.write(data)

def parse_content(filtered):
    #filterd是陣列型態的本文資料
    key = ['修業學年度/學期','上課時段','課程名稱/授課教師','所屬類別/開課系所','上課方式/用書','評分方式','注意事項','心得/結語','成績參考']
    start_index=end_index=1#initialization
    content_dict = {}
    truncate_head(filtered,key)#把前面多餘的字砍掉 
    for i in enumerate(key):       
        string = ""               
        for j in enumerate(filtered):
            if i[0] < len(key)-1:
                #general situation,因為下面的判斷式會用到i[0]+1,如果已經是最後一個還這麼做就index out of range
                if j[1] == key[i[0]+1]:
                    #end_index是for要停下來的位置，因為end_index是下一個key的位置              
                    end_index = j[0]
                    break
            else:
                #this is final iteration
                if j[1] == key[i[0]]:                    
                    end_index = len(filtered)-1
                    break

        key_i = []
        eng_key = convert_key(filtered[start_index-1])
        key_i.append(eng_key)#拿到key
        start_index,string = concatenate(start_index,end_index,filtered,string)
                       
        string_l = []
        string_l.append(string)
        row = zip(key_i,string_l)#two argument of zip can only be iterable, so 'list, tuple etc' is suitable!!!
        content_dict.update(row)        
    return content_dict

def concatenate(start_index,end_index,filtered,string):
    for i in enumerate(filtered):
        if i[0] == end_index:
            return (i[0]+1,string)
        elif i[0] >= start_index and i[0] < end_index:
            string += i[1]#i[1] is string, i[0] is index

def truncate_head(filtered,key):
    while filtered[0] != key[0]:
        filtered.pop(0)
        #把不是修業學年度開頭的文字去掉，讓filtered都固定從同樣的key開始遞迴

def convert_key(key):
    return chi2en[key]#it will return it's eng key.

if __name__ == '__main__':
    crawler()

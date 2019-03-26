#!/usr/bin/python3
# -*-codig=utf8-*-

'''
http://snapshot.sogou/agent/wget.php?help=1
http://parse.task.sogou/
'''


import sys
import requests
import re
from urllib.parse import quote
from functools import reduce

fetch_service = "http://snapshot.sogou/agent/wget.php?"


def log_error(str):
    sys.stderr.write('%s\n' % str)
    sys.stderr.flush()

def utf8stdout(in_str):
    utf8stdout = open(1, 'w', encoding='utf-8', closefd=False) # fd 1 is stdout
    print(in_str, file=utf8stdout)

def fetch_res(engine, query):
    url = fetch_service + "engine=" + engine + "&query=" + quote(query)
    print(url)
    try:
        res = requests.get(url)
        return res.text
    except Exception as err:
        log_error('[fetch_res]: %s' % err)


def fetch(data, lstr, rstr):
    lst = []
    left, right = 0, 0
    while left != -1 and right != -1:
        left = data.find(lstr, right)
        if left != -1:
            right = data.find(rstr, left + len(lstr))
            if right != -1:
                lst.append(data[left + len(lstr): right])
    return lst


def fetch_list(data, lstr_lst, rstr_lst):
    lst = []
    min_left, min_right = 0, 0
    min_lstr, min_rstr = '', ''
    while min_left != -1 and min_right != -1:
        tmp_left = -1
        for lstr in lstr_lst:
            left = data.find(lstr, min_right)
            if left < tmp_left and left != -1 or tmp_left == -1:
                tmp_left, min_lstr = left, lstr
        min_left = tmp_left
        #left = data.find(lstr, right)
        if min_left != -1:
            tmp_right = -1
            for rstr in rstr_lst:
                right = data.find(rstr, min_left + len(min_lstr))
                if right < tmp_right and right != -1 or tmp_right == -1:
                    tmp_right, min_rstr = right, rstr
            min_right = tmp_right
            #right = data.find(rstr, left + len(lstr))
            if min_right != -1:
                lst.append(data[min_left + len(min_lstr): min_right])
    return lst


def parse_baidu(html):
    pat = re.compile('<.*?>')
    res = []
    #html = dinfo['snapshot']
    if not html:
        return res
    tmp = fetch(html, '<textarea', '</textarea>')
    query = tmp[0].split('>', 1)[-1] if tmp else ''
    #blocks = fetch(html, '<div class="result c-result', '<div class="result c-result')
    blocks = fetch_list(html, ['<div class="result c-result', '<div class="c-result result'], ['<div class="result c-result', '<div class="c-result result'])
    if not blocks:
        return res
    for block in blocks[:3]:
        block = block.replace("&#39;", "'")
        tmp = fetch(block, '\'mu\':\'', '\'')
        url = tmp[0] if tmp else ''
        #tmp = fetch(block, '&#39;mu&#39;:&#39;', '&#39;')
        #url = tmp[0] if tmp else ''
        label = 'normal'
        key_lst = ['wenda-abstract-title', 'wenda-abstract-text']
        #if block.find('wa-wenda-abstract-title') != -1:
        #if filter(lambda x: block.find(x) != -1, key_lst):
        if reduce(lambda init, itm: init or itm, [block.find(x) != -1 for x in key_lst], False):
            lizhi_key = list(filter(lambda x: block.find(x) != -1, key_lst))[0]
            label = 'Lizhi'
            #tmp = fetch(block[block.rfind('wa-wenda-abstract-title'):], '>', '</span>')
            tmp = fetch(block[block.rfind(lizhi_key):], '>', '</span>')
            title = tmp[0] if tmp else ''
            content = ''
            if block.find('wa-wenda-abstract-quotes') != -1:
                tmp = fetch(block, '<span class="wa-wenda-abstract-quotes">', '<span class="wa-wenda-abstract-quotes">')
                content = tmp[0] if tmp else ''
            if not content and block.find('wa-wenda-abstract-list-num') != -1:
                tmp = fetch(block, '<div class="wa-wenda-abstract-list-num">', '</p>')
                content = ''.join(pat.split(' '.join(tmp).replace('&nbsp;', ' '))) if tmp else ''
            if not content and block.find('c-font-big wenda-abstract') != -1:
                tmp = fetch(block, 'c-font-big wenda-abstract', '<span')
                content = tmp[0]
            if not content and block.find('wenda-abstract-list-num') != -1: # new list
                tmp = fetch(block[block.rfind('wenda-abstract-title'):], '>', '</span>')
                title = tmp[0] if tmp else ''
                tmp = fetch(block, '<div class="c-color', '</div>')
                content = ''.join(pat.split(' '.join(tmp).replace('&nbsp;', ' '))) if tmp else ''
            if not content and block.find('c-gap-inner') != -1: # new list2
                tmp = fetch(block, 'c-gap-inner', '</div>')
                content = 'list2' + ' '.join([itm.split('>')[1] for itm in tmp])
        elif block.find('vid-meta-content') != -1: # youzhiwenda
            label = 'normal'
            tmp = fetch(block, '<div class="c-row', '</div>')
            title = fetch(tmp[0], '<span>', '</span>')
            if title:
                title = title[0]
            content = fetch(tmp[-1], '<span>', '</span>')
            if content:
                content = content[0]
            elif len(tmp) > 1:
                content = fetch(tmp[1], '<span>', '</span>')
                if content:
                    content = content[0]
            url = 'youzhi'
        elif block.find('\xe7\x99\xbe\xe5\xba\xa6\xe7\x9f\xa5\xe8\xaf\x86\xe5\x9b\xbe\xe8\xb0\xb1') != -1: # baiduzhishitupu
            label = 'Tupu'
            title = 'tupu'
            url = 'tupu'
            content = 'content'
        else:
            tmp = fetch(block, '<h3', '</h3>')
            title = tmp[0].split('>', 1)[-1] if tmp else ''
            tmp = fetch(block, '<p class="c-abstract', '</p>')
            if tmp:
                content = tmp[0].split('>', 1)[-1]
            else:
                tmp = fetch(block, '<p class="c-color', '</p>')
                content = tmp[0].split('>', 1)[-1] if tmp else ''
        if url and title and content:
            res.append((query, label, url, title.replace('<em>', '').replace('</em>', ''), content.replace('<em>', '').replace('</em>', '')))
    return res



if __name__ == "__main__":

    res = fetch_res("wap_baidu", "冯远征和梁丹妮")
    #utf8stdout(res)
    res = res.strip('\n')
    baidu_res = parse_baidu(res)
    print(baidu_res)

    #lst2 = fetch_list(res, ['<div class="result c-result', '<div class="c-result result'], ['<div class="result c-result', '<div class="c-result result'])
    #for i in range(len(lst2)):
        #pass
        #print("第%s个元素是%s：" % (i, lst2[i]))

    '''
    data = "111 aaa 222 111 bbb 222 333 ccc 444 333 ddd 444 111 eee 444 333 fff 222 444 ggg 333"
    lst3 = fetch_list(data, ['111', '333'], ['222', '444'])
    for i in range(len(lst3)):
        print("第%s个元素是:%s" % (i, lst3[i]))
    '''


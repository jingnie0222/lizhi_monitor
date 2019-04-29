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
from lxml import etree
from bs4 import BeautifulSoup
import pysnooper

fetch_service = "http://snapshot.sogou/agent/wget.php?"
#regex_first = r'<div id="results"(.*?)order="1"(.*)<div class=.*order="2"'
#regex_first = r'<div id="results"(.*)order="1"(.*)<div class=.*order="2"'
regex_first = r'<div id="results"(.*)<div class="c-result result".*order="2"'

baidu_kmap_list = ['tpl="ks_general"', 'tpl="person_couple"', 'tpl="wise_word_poem"', 'tpl="kg_answer_poem"', 'tpl="sg_answer_poem"', 'tpl="kg_law"' , 'tpl="kg_qanda"', '百度知识图谱']
baidu_baike_list = ['tpl="bk_polysemy"', 'tpl="sg_kg_entity"']
baidu_official_list = ['tpl="www_sitelink_normal"', 'aria-label="标签.官网."', 'aria-label="标签.来自官方."']


def log_error(str):
    sys.stderr.write('%s\n' % str)
    sys.stderr.flush()

def utf8stdout(in_str):
    utf8stdout = open(1, 'w', encoding='utf-8', closefd=False) #fd 1 is stdout
    print(in_str, file=utf8stdout)

def fetch_res(engine, query):
    url = fetch_service + "engine=" + engine + "&query=" + quote(query)
    print(url)
    try:
        res = requests.get(url)
        res.encoding = "utf-8"
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

def extract_first_res(page):
    try:
        parsed_html = BeautifulSoup(page, "html.parser")
        first_res = parsed_html.select_one("div[order=\"1\"]")
        if first_res:
            #first_res是bs4.element.tag类型，将其转化为str
            return str(first_res)
        else:
            print('[extract_baidu_first_res]:没有找到首条结果')
            return None

    except Exception as err:
        print('[extract_baidu_first_res]:%s' % err)
        return None

def is_Official(first_result):
    try:
        if r'tpl="www_sitelink_normal"' in first_result or r'aria-label="标签.官网."' in first_result:
            return True
        else:
            return False
    except Exception as err:
        print("[is_baidu_Official]:%s" % err)
        return False


def parse_baidu(page):

    result = {'res_type':'',
              'vrid':'',
              'error':''}
    try:
        first_result = extract_first_res(page)
        #print("frist_res : %s" % first_result)

        if not first_result:
            result['error'] = "[parse_baidu]extract first res error"
            result['res_type'] = "Error"
            return result

        #百度的精选摘要结果，标识为srcid="wenda_abstract",tpl="wenda_abstract" 对标搜狗的通用立知
        #百度的优质问答结果，标识为tpl="wenda_abstract"，srcid是一个五位数 对标搜狗的优质问答
        #这两类统一归类为Lizhi结果
        if r'tpl="wenda_abstract"' in first_result:
            result['res_type'] = 'Lizhi'
            result['vrid'] = "wenda_abstract"
            return result

        #如果命中baidu_kmap_list中的内容，归类为图谱结果，对标搜狗的图谱结果,归类为立知结果
        for mark in baidu_kmap_list:
            if mark in first_result:
                result['res_type'] = 'Lizhi'
                result['vrid'] = mark
                return result

        #如果命中baidu_baike_list中的内容，归类为百科结果
        for mark in baidu_baike_list:
            if mark in first_result:
                result['res_type'] = 'Baike'
                result['vrid'] = mark
                return result

        #如果命中baidu_official_list中的内容，归类为官网结果
        for mark in baidu_official_list:
            if mark in first_result:
                result['res_type'] = 'Official'
                result['vrid'] = mark
                return result

        #其他结果包括VR结果，归为普通结果
        result['res_type'] = "Other"
        return result

    except Exception as err:
        result['error'] = "[parse_baidu]" + err
        result['res_type'] = "Error"
        return result


def extract_baidu_result_new(html):
    pat = re.compile('<.*?>')
    res = []
    #html = dinfo['snapshot']
    if not html:
        return res
    tmp = fetch(html, '<textarea', '</textarea>')
    query = tmp[0].split('>', 1)[-1] if tmp else ''
    # blocks = fetch(html, '<div class="result c-result', '<div class="result c-result')
    blocks = fetch_list(html, ['<div class="result c-result', '<div class="c-result result'],
                        ['<div class="result c-result', '<div class="c-result result'])
    if not blocks:
        return res
    for block in blocks[:3]:
        block = block.replace("&#39;", "'")
        tmp = fetch(block, '\'mu\':\'', '\'')
        url = tmp[0] if tmp else ''
        # tmp = fetch(block, '&#39;mu&#39;:&#39;', '&#39;')
        # url = tmp[0] if tmp else ''
        label = 'normal'
        key_lst = ['wenda-abstract-title', 'wenda-abstract-text']
        # if block.find('wa-wenda-abstract-title') != -1:
        # if filter(lambda x: block.find(x) != -1, key_lst):
        if reduce(lambda init, itm: init or itm, [block.find(x) != -1 for x in key_lst], False):
            lizhi_key = list(filter(lambda x: block.find(x) != -1, key_lst))[0]
            label = 'lizhi'
            # tmp = fetch(block[block.rfind('wa-wenda-abstract-title'):], '>', '</span>')
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
            if not content and block.find('wenda-abstract-list-num') != -1:  # new list
                tmp = fetch(block[block.rfind('wenda-abstract-title'):], '>', '</span>')
                title = tmp[0] if tmp else ''
                tmp = fetch(block, '<div class="c-color', '</div>')
                content = ''.join(pat.split(' '.join(tmp).replace('&nbsp;', ' '))) if tmp else ''
            if not content and block.find('c-gap-inner') != -1:  # new list2
                tmp = fetch(block, 'c-gap-inner', '</div>')
                content = 'list2' + ' '.join([itm.split('>')[1] for itm in tmp])
        elif block.find('vid-meta-content') != -1:  # youzhiwenda
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
        elif block.find(
                '\xe7\x99\xbe\xe5\xba\xa6\xe7\x9f\xa5\xe8\xaf\x86\xe5\x9b\xbe\xe8\xb0\xb1') != -1:  # baiduzhishitupu
            label = 'lizhi'
            title = 'tupu'
            url = 'tupu'
            content = 'content'

        elif block.find('wa-ks-general') != -1:
            label = 'lizhi'
            title = 'wa-ks-general'
            url = 'wa-ks-general'
            tmp = fetch(block, '<p class="c-line-clamp3', '/p>')
            if tmp:
                content = fetch(tmp[0], '>', '<')
                content = content[0]
            else:
                content = 'wa-ks-general'

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
            res.append((query, label, url, title.replace('<em>', '').replace('</em>', ''),
                        content.replace('<em>', '').replace('</em>', '')))
    return res

def extract_tupu_content(page):

    try:
        parsed_html = BeautifulSoup(page, "html.parser")
        bigdiv = parsed_html.select_one("div[order=\"1\"]")
        content = ""
        print("bigdiv = %s" % bigdiv.prettify())

        if 'tpl="ks_general"' in bigdiv:
            lable = bigdiv.select_one(".c-container").select("p")
            for el in lable:
                content += el.text
            return content

        if 'tpl="person_couple"' in bigdiv:
            lable = bigdiv.select_one(".c-row")
            return lable.text

        if 'tpl="kg_answer_poem"' in bigdiv:
            lable = bigdiv.select_one(".wa-kg-answer-poem-wrapping")
            return lable.text

        if 'tpl="kg_qanda"' in bigdiv:
            lable = bigdiv.select_one(".c-border")
            return lable.text

    except Exception as err:
        print("[extract_tupu_content]:%s" % err)


if __name__ == "__main__":
    page = fetch_res("wap_baidu", "企业更改名字要多久")
    res_dict = parse_baidu(page)
    print(res_dict)





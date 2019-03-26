#!/usr/bin/python3
# -*-codig=utf8-*-

import sys
import requests
import re
from urllib.parse import quote
import DataFile
import parse_sogou
import parse_baidu
import multiprocessing
import datetime

fetch_service = "http://snapshot.sogou/agent/wget.php?"

#sogou_wordlist = ['马来西亚官方语言', '平头哥是什么动物', '绿茶婊是什么意思', '电阻的作用', '相对原子质量', 'zuzu化妆品怎么样','冯远征和梁丹妮']

sogou_wordlist = DataFile.read_file_into_list("./sogou")
#baidu_wordlist = DataFile.read_file_into_list("./baidu")

'''
def fetch_page(engine, query):
    url = fetch_service + "engine=" + engine + "&query=" + quote(query)
    print(url)
    try:
        res = requests.get(url)
        return res.text
    except Exception as err:
        log_error('[fetch_res]: %s' % err)
'''
def sg_fetch_page(query):
    url = fetch_service + "engine=wap_sogou" + "&query=" + quote(query)
    print(url)
    try:
        res = requests.get(url)
        return res.text
    except Exception as err:
        log_error('[sg_fetch_res]: %s' % err)

def bd_fetch_page(query):
    url = fetch_service + "engine=wap_baidu" + "&query=" + quote(query)
    print(url)
    try:
        res = requests.get(url)
        return res.text
    except Exception as err:
        log_error('[bd_fetch_res]: %s' % err)


def fetch_page(query):
    res = {'sg_page':'',
           'bd_page':''}

    sg_url = fetch_service + "engine=wap_sogou" + "&query=" + quote(query)
    print(sg_url)
    bd_url = fetch_service + "engine=wap_baidu" + "&query=" + quote(query)
    print(bd_url)
    try:
        res['sg_page'] = requests.get(sg_url).text
        res['bd_page'] = requests.get(bd_url).text
        return res
    except Exception as err:
        log_error('[fetch_page]: %s' % err)
        return None

def static_by_sg_word():
    static_res = dict()
    static_res['sogou'] = {'vr':0,
                           'lizhi':0,
                           'tupu':0,
                           'other':0}
    static_res['baidu'] = {'vr': 0,
                           'lizhi': 0,
                           'tupu': 0,
                           'other': 0}

    for word in sogou_wordlist:

        sogou_page = fetch_page('wap_sogou', word)
        sg_ret = parse_sogou.parse_sogou(sogou_page)

        if sg_ret:
            sg_res_type = sg_ret['res_type']

            if 'VR' == sg_res_type:
                static_res['sogou']['vr'] += 1
            elif 'Lizhi' == sg_res_type:
                static_res['sogou']['lizhi'] += 1
            elif 'Tupu' == sg_res_type:
                static_res['sogou']['tupu'] += 1
            else:
                static_res['sogou']['other'] += 1
        else:
            static_res['sogou']['other'] += 1


        baidu_page = fetch_page('wap_baidu', word)
        bd_ret = parse_baidu.parse_baidu(baidu_page)

        if bd_ret:
            bd_res_type = bd_ret[0][1]
            print("bd_res_type=%s" % bd_res_type)

            if 'VR' == bd_res_type:
                static_res['baidu']['vr'] += 1
            elif 'Lizhi' == bd_res_type:
                static_res['baidu']['lizhi'] += 1
            elif 'Tupu' == bd_res_type:
                static_res['baidu']['tupu'] += 1
            else:
                static_res['baidu']['other'] += 1
        else:
            static_res['baidu']['other'] += 1

    print(static_res)


#static_by_sg_word()



if __name__ == '__main__':

    #初始化多线程
    cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=cores)
   
    start = datetime.datetime.now()
    sg_page_lst = pool.map(fetch_page, sogou_wordlist)
    #sg_page_lst = pool.map(sg_fetch_page, sogou_wordlist)
    #bd_page_lst = pool.map(bd_fetch_page, sogou_wordlist)

    #for word in sogou_wordlist:
        #sg_fetch_page(word)
    end = datetime.datetime.now()
    cost = (end - start).seconds
    print("total_cost=%s" % cost)

    while True:
        pass

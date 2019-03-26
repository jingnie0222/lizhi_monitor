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

fetch_service = "http://snapshot.sogou/agent/wget.php?"

regex_vr = '\<div.*id=\"sogou_vr_(.*?)_'
regex_lizhi = '\<div .* id=\"sogou_vr_kmap_(.*?)_'
regex_tupu = '\<div .* id=\"lz-top-(.*?)\"'
regex_tupu_8_1 = 'id=\"kmap-jzvr-81-container\"'


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

def extract_first_res(page):
    try:
        #在前端源码中通过data-v="101"标识来提取首条结果，正则必须使用多行模式
        if 'data-v="101"' in page:
            pat_first_res = re.search(r'<div(.*?)id=(.*) data-v="101">(.*?)</div>', page, flags=re.DOTALL)

            if pat_first_res:
                first_res = pat_first_res.group(0)
                return first_res
        else:
            print('[extract_first_res]:没有找到首条结果，没有data-v="101"标记')
            return None

    except Exception as err:
        print('[extract_first_res]:%s' % err)
        return None


def extract_lizhi_icon(first_result):

    #判断结果是否有立知icon
    lizhi_flag = False
    try:
        if first_result:
            if "class=\"icon-known\"" in first_result:
                lizhi_flag = True

        return lizhi_flag

    except Exception as err:
        print('[extract_lizhi_icon]:%s' % err)
        return False

def classify_res(first_result):

    result = {'res_type':'',
              'vrid':'',
              'error':''}

    #根据vrid的正则规则判断结果类别

    try:
        pat_vr = re.search(regex_vr, first_result)
        pat_lizhi = re.search(regex_lizhi, first_result)
        pat_tupu = re.search(regex_tupu, first_result)
        pat_tupu_8_1 = re.search(regex_tupu_8_1, first_result)

        if pat_vr:
            result['vrid'] = pat_vr.group(1)
            if vr_vrid.startswith(('1', '2', '4', '7')):
                result['res_type'] = "VR"

        if pat_lizhi:
            result['vrid'] = pat_lizhi.group(1)
            result['res_type'] = "Lizhi"

        if pat_tupu:
            result['vrid'] = pat_tupu.group(1)
            result['res_type'] = "Tupu"

        #图谱结果中的特例，query=描写冬天冷的词语，vrid=kmap-jzvr-81-container
        if pat_tupu_8_1:
            result['vrid'] = "kmap-jzvr-81-container"
            result['res_type'] = "Tupu"

        return result

    except Exception as err:
        print('[classify_res]:%s' % err)
        return None


def parse_sogou(first_result):

    lizhi_flag = extract_lizhi_icon(first_result)
    result = classify_res(first_result)

    if lizhi_flag:
        #print("res_type=%s, vrid=%s" % (res_type, vrid))
        return result

    if not lizhi_flag:
        if "50026601" == result['vrid'] or "50026401" == result['vrid'] or "50026301" == result['vrid'] or "kmap-jzvr-81-container" == result['vrid']:
            #print("res_type=%s, vrid=%s" % (res_type, vrid))
            return result
        else:
            return None

if __name__ == "__main__":

    res = fetch_res("wap_sogou", "菠萝怎么吃")
    #utf8stdout(res)
    first_res = extract_first_res(res)
    #utf8stdout(first_res)
    lizhi_flag = extract_lizhi_icon(first_res)
    print("lizhi_flag=%s" % lizhi_flag)
    #classify_res(first_res)
    res_dict = parse_sogou(first_res)
    if res_dict:
        for key in res_dict:
            print('key:%s  value:%s' % (key, res_dict[key]))


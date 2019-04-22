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

sogou_lizhi_med_list = ['50026601', '50026401', '50026301', 'kmap-jzvr-81-container']
sogou_baike_list = ['30010100', '30010163', '30010161', '30010097', '30000101']


def log_error(str):
    sys.stderr.write('%s\n' % str)
    sys.stderr.flush()

def utf8stdout(in_str):
    utf8stdout = open(1, 'w', encoding='utf-8', closefd=False) # fd 1 is stdout
    print(in_str, file=utf8stdout)

def fetch_res(engine, query):
    url = fetch_service + "engine=" + engine + "&query=" + quote(query)
    #url = "http://wap.sogou.com.inner/web/searchList.jsp?keyword=" + quote(query)
    print(url)
    try:
        res = requests.get(url)
        res.encoding = 'utf-8'
        #print(res.text)
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
            print('[extract_sogou_first_res]:没有找到首条结果，没有data-v="101"标记')
            return None

    except Exception as err:
        print('[extract_sogou_first_res]:%s' % err)
        return None


def extract_lizhi_icon(page):

    #判断结果是否有立知icon
    lizhi_flag = False
    try:
        if "class=\"icon-known\"" in page:
            lizhi_flag = True

        return lizhi_flag

    except Exception as err:
        print('[extract_lizhi_icon]:%s' % err)
        return False
'''
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
            if result['vrid'].startswith(('1', '2', '4', '7')):
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
        print('[classify_sogou_res]:%s' % err)
        return None
'''

def extract_vrid(first_result):

    vrid = ""
    #根据vrid的正则规则判断结果类别

    try:
        pat_vr = re.search(regex_vr, first_result)
        pat_lizhi = re.search(regex_lizhi, first_result)
        pat_tupu = re.search(regex_tupu, first_result)
        pat_tupu_8_1 = re.search(regex_tupu_8_1, first_result)

        if pat_vr:
            vrid = pat_vr.group(1)

        if pat_lizhi:
            vrid = pat_lizhi.group(1)

        if pat_tupu:
            vrid = pat_tupu.group(1)

        #图谱结果中的特例，query=描写冬天冷的词语，vrid=kmap-jzvr-81-container
        if pat_tupu_8_1:
            vrid = "kmap-jzvr-81-container"

        return vrid

    except Exception as err:
        print('[extract_vrid]:%s' % err)
        return vrid

def is_Official(first_result):
    try:
        if r'class="web-tag tag-official">官网' in first_result or r'class="web-tag">官网' in first_result:
            return True
        else:
            return False
    except Exception as err:
        print("[is_sogou_Official]:%s" % err)
        return False

def parse_sogou(page):

    result = {'res_type':'',
              'vrid':'',
              'error':''}

    try:
        first_result = extract_first_res(page)
        if not first_result:
            result['error'] = "[parse_sogou]extract first res error"
            result['res_type'] = "Error"
            return result

        lizhi_flag = extract_lizhi_icon(page)
        vrid = extract_vrid(first_result)

        if lizhi_flag:
            result['res_type'] = 'Lizhi'
            result['vrid'] = vrid
            return result

        if not lizhi_flag:
            if vrid in sogou_lizhi_med_list:
                result['res_type'] = 'Lizhi'
                result['vrid'] = vrid
                return result

        if vrid.startswith(('1', '2', '4', '7')):
            result['res_type'] = 'VR'
            result['vrid'] = vrid
            return result

        if vrid in sogou_baike_list:
            result['res_type'] = 'Baike'
            result['vrid'] = vrid
            return result

        if is_Official(first_result):
            result['res_type'] = 'Official'
            result['vrid'] = vrid
            return result

        #普通结果
        result['res_type'] = "Other"
        return result

    except Exception as err:
        result['error'] = "[parse_sogou]" + err
        result['res_type'] = "Error"
        return result

if __name__ == "__main__":

    page = fetch_res("wap_sogou", "艾滋病")
    #utf8stdout(page)
    first_res = extract_first_res(page)
    #utf8stdout(first_res)
    lizhi_flag = extract_lizhi_icon(first_res)
    print("lizhi_flag=%s" % lizhi_flag)
    #classify_res(first_res)
    res_dict = parse_sogou(page)
    print(res_dict)



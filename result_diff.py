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
import time
import Template
import Mail

fetch_service = "http://snapshot.sogou/agent/wget.php?"

# sogou_wordlist = ['马来西亚官方语言', '平头哥是什么动物', '绿茶婊是什么意思', '电阻的作用', '相对原子质量', 'zuzu化妆品怎么样','冯远征和梁丹妮']

sogou_wordlist = DataFile.read_file_into_list("./sogou")
baidu_wordlist = DataFile.read_file_into_list("./baidu")

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
    #print(url,query)
    try:
        res = requests.get(url)
        return res.text
    except Exception as err:
        log_error('[sg_fetch_res]: %s' % err)


def bd_fetch_page(query):
    url = fetch_service + "engine=wap_baidu" + "&query=" + quote(query)
    #print(url,query)
    try:
        res = requests.get(url)
        return res.text
    except Exception as err:
        log_error('[bd_fetch_res]: %s' % err)


def fetch_and_analysis(word_list, queue):
    #同一个query在搜狗侧和百度侧分别抓取并对结果分类
    for query in word_list:
        try:
            #fetch from sogou
            sogou_page = sg_fetch_page(query)
            sg_ret = parse_sogou.parse_sogou(sogou_page)

            if sg_ret:
                sg_res_type = sg_ret['res_type']
                #queue的内容为线程状态、engine、结果类别
                queue.put(("working", "SG", sg_res_type))
            else:
                queue.put(("working", "SG", "Other"))

            #fetch from baidu
            baidu_page = bd_fetch_page(query)
            bd_ret =  parse_baidu.parse_baidu(baidu_page)

            if bd_ret:
                bd_res_type = bd_ret[0][1]
                queue.put(("working", "BD", bd_res_type))
            else:
                queue.put(("working", "BD", "Other"))

        except Exception as err:
            print("[process]:%s" % err)
            continue

    queue.put(("quit", None, None))


def split_wordlist(wordlist, n, i):
    # 将列表切分为n份,返回第i份
    total_len = len(wordlist)
    try:
        step = total_len//n
        if i < n-1 :
            return wordlist[i*step:(i+1)*step]
        if i == n-1 :
            return wordlist[i*step:]

    except Exception as err:
        print("[split_wordlist]:%s" % err)


def parallel_process(wordlist):

    cores = multiprocessing.cpu_count()
    print(cores)
    queue = multiprocessing.Queue()
    p_list = []
    quit_count = 0

    static_res = dict()
    static_res['Sogou'] = {'VR': 0,
                        'Lizhi': 0,
                        'Tupu': 0,
                        'Other': 0}
    static_res['Baidu'] = {'VR': 0,
                        'Lizhi': 0,
                        'Tupu': 0,
                        'Other': 0}
    try:
        #生成与核数对应的进程数，多进程执行fetch_and_analysis，将词表按进程数切分，每个进程处理对应的词表
        for i in range(cores):
            p = multiprocessing.Process(target=fetch_and_analysis, args=(split_wordlist(wordlist, cores, i), queue))
            p.start()
            p_list.append(p)

        while True:
            # queue的内容为线程状态、engine、结果类别
            (status, engine, result) = queue.get()
            print(status, engine, result)

            if 'SG' == engine:
                if "VR" == result:
                    static_res['Sogou']['VR'] += 1
                elif "Lizhi" == result:
                    static_res['Sogou']['Lizhi'] += 1
                elif "Tupu" == result:
                    static_res['Sogou']['Tupu'] += 1
                else:
                    static_res['Sogou']['Other'] += 1

            elif 'BD' == engine:
                if "VR" == result:
                    static_res['Baidu']['VR'] += 1
                elif "Lizhi" == result:
                    static_res['Baidu']['Lizhi'] += 1
                elif "Tupu" == result:
                    static_res['Baidu']['Tupu'] += 1
                else:
                    static_res['Baidu']['Other'] += 1

            if status == "quit":
                quit_count += 1

            if quit_count == cores:
                break

        for p in p_list:
            p.join()

        return static_res

    except Exception as err:
        print("[parallel_process]:%s" % err)


def html_table(data, table_head = [], dict_keys = []):
    return_data = []
    return_data.append("<table border=\"2\">")
    return_data.append("<tr>")
    if(len(table_head) > 0):   #处理表格头部信息
        return_data.append('<th>')
        return_data.append("</th><th>".join(table_head))
        return_data.append('</th></tr>')

    if(len(data) > 0):
        for row in data:
            return_data.append('<tr><td>')
            return_data.append(row)

            inst_data_row = []
            for s_key in dict_keys:
                inst_data_row.append(str(data[row].get(s_key, ""))) #这里做str的处理，省得传入int的时候失败
            row = inst_data_row
            return_data.append('</td><td>')
            return_data.append("</td><td>".join(row))
            return_data.append("</td></tr>\n")
    return "".join(return_data) + "</table>"


if __name__ == '__main__':

    #多进程抓取和数据分析
    start = time.time()

    sogou_word_static_res = parallel_process(sogou_wordlist)
    print("sogou word:%s" % sogou_word_static_res)

    baidu_word_static_res = parallel_process(baidu_wordlist)
    print("baidu word:%s" % baidu_word_static_res)

    end = time.time()

    #汇总邮件内容
    table_head = ['数据抓取', '首条为vr', '首条为立知', '首条为图谱', '首条为其他']
    static_item = ['VR', 'Lizhi', 'Tupu', 'Other']

    #抓取耗时
    runtime_html = Template.html_p_time(start, end)
    #搜狗词总量
    sogou_word_count_html = Template.html_p("搜狗日志取词总量：" + str(len(sogou_wordlist)))
    #搜狗词抓取结果统计
    sogou_table_html = html_table(sogou_word_static_res, table_head, static_item)

    #百度词总量
    baidu_word_count_html = Template.html_p("百度搜索取词总量：" + str(len(baidu_wordlist)))
    #搜狗词抓取结果统计
    baidu_table_html = html_table(baidu_word_static_res, table_head, static_item)

    report_tmp_path = "lizhi_monitor.html"
    report_content = "".join([Template.html_general_css(), Template.html_h3_title("立知效果-召回对比"), runtime_html,
                              sogou_word_count_html, sogou_table_html, baidu_word_count_html, baidu_table_html])
    DataFile.write_full_file(report_tmp_path, report_content)

    #发送邮件
    maillist = "yinjingjing@sogou-inc.com"
    Mail.sendMail("立知效果专项监控", report_tmp_path, maillist)
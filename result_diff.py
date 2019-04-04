#!/usr/bin/python3
# -*-codig=utf8-*-

import sys,os
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
import my_screenshot
import shutil


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
    #url = "http://wap.sogou.com.inner/web/searchList.jsp?keyword=" + quote(query)
    #print(url,query)
    try:
        res = requests.get(url)
        res.encoding = 'utf-8'
        return res.text
    except Exception as err:
        log_error('[sg_fetch_res]: %s' % err)


def bd_fetch_page(query):
    url = fetch_service + "engine=wap_baidu" + "&query=" + quote(query)
    #print(url,query)
    try:
        res = requests.get(url)
        res.encoding = 'utf-8'
        return res.text
    except Exception as err:
        log_error('[bd_fetch_res]: %s' % err)


def fetch_and_analysis(word_list, queue):
    #同一个query在搜狗侧和百度侧分别抓取并对结果分类
    for query in word_list:
        try:
            print(query)
            #fetch from sogou
            sogou_page = sg_fetch_page(query)
            sg_ret = parse_sogou.parse_sogou(sogou_page)
            #print("sg_ret=%s" % sg_ret)

            # fetch from baidu
            baidu_page = bd_fetch_page(query)
            bd_ret = parse_baidu.parse_baidu(baidu_page)
            #print("bd_ret=%s" % bd_ret)

            sg_res_type = sg_ret['res_type']
            sg_res_err = sg_ret['error']
            bd_res_type = bd_ret['res_type']
            bd_res_err = bd_ret['error']
            #queue的内容为线程状态、engine、搜狗结果类别、百度结果类别
            queue.put(("working", "SG", sg_res_type, bd_res_type))
            queue.put(("working", "BD", sg_res_type, bd_res_type))


            #如果百度召回立知，搜狗正常抓到结果且结果为其他，保留现场
            if bd_res_type == 'Lizhi' and not sg_res_err and not sg_res_type:
                my_screenshot.get_sogou_screenshot(query, "")
                my_screenshot.get_baidu_screenshot(query, "")

            #如果搜狗召回立知，百度正常抓到结果，且结果为非立知结果，保留现场
            if sg_res_type == 'Lizhi' and bd_res_type == 'Baike':
                my_screenshot.get_sogou_screenshot(query, "")
                my_screenshot.get_baidu_screenshot(query, "")

            if sg_res_type == 'Lizhi' and bd_res_type == 'Official':
                my_screenshot.get_sogou_screenshot(query, "")
                my_screenshot.get_baidu_screenshot(query, "")

            if sg_res_type == 'Lizhi' and not bd_res_err and not bd_res_type:
                my_screenshot.get_sogou_screenshot(query, "")
                my_screenshot.get_baidu_screenshot(query, "")

        except Exception as err:
            print("[fetch_and_analysis]:%s" % err)
            continue

    queue.put(("quit", None, None, None))


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
    #搜狗首条召回情况
    static_res['Sogou'] = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0}
    #百度首条召回情况
    static_res['Baidu'] = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0}

    #搜狗首条为立知结果的词，在百度的召回情况
    static_sg_lizhi = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0}
    #百度首条为立知结果的词，在搜狗的召回情况
    static_bd_lizhi = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0}

    try:
        #生成与核数对应的进程数，多进程执行fetch_and_analysis，将词表按进程数切分，每个进程处理对应的词表
        for i in range(cores):
            p = multiprocessing.Process(target=fetch_and_analysis, args=(split_wordlist(wordlist, cores, i), queue))
            p.start()
            p_list.append(p)

        while True:
            #queue的内容为线程状态、engine、搜狗结果类别、百度结果类别
            (status, engine, sg_ret, bd_ret) = queue.get()
            print(status, engine, sg_ret, bd_ret)

            if 'SG' == engine:
                if "Lizhi" == sg_ret:
                    static_res['Sogou']['Lizhi'] += 1

                    #统计在搜狗出立知结果时，在百度的召回情况
                    if 'Lizhi' == bd_ret:
                        static_sg_lizhi['Lizhi'] += 1
                    elif 'VR' == bd_ret:
                        static_sg_lizhi['VR'] += 1
                    elif 'Baike' == bd_ret:
                        static_sg_lizhi['Baike'] += 1
                    elif 'Official' == bd_ret:
                        static_sg_lizhi['Official'] += 1
                    else:
                        static_sg_lizhi['Other'] += 1

                elif "VR" == sg_ret:
                    static_res['Sogou']['VR'] += 1
                elif "Baike" == sg_ret:
                    static_res['Sogou']['Baike'] += 1
                elif "Official" == sg_ret:
                    static_res['Sogou']['Official'] += 1
                else:
                    static_res['Sogou']['Other'] += 1

            elif 'BD' == engine:
                if "Lizhi" == bd_ret:
                    static_res['Baidu']['Lizhi'] += 1

                    #统计在百度出立知结果时，在搜狗的召回情况
                    if 'Lizhi' == sg_ret:
                        static_bd_lizhi['Lizhi'] += 1
                    elif 'VR' == sg_ret:
                        static_bd_lizhi['VR'] += 1
                    elif 'Baike' == sg_ret:
                        static_bd_lizhi['Baike'] += 1
                    elif 'Official' == sg_ret:
                        static_bd_lizhi['Official'] += 1
                    else:
                        static_bd_lizhi['Other'] += 1

                elif "VR" == bd_ret:
                    static_res['Baidu']['VR'] += 1
                elif "Baike" == bd_ret:
                    static_res['Baidu']['Baike'] += 1
                elif "Official" == bd_ret:
                    static_res['Baidu']['Official'] += 1
                else:
                    static_res['Baidu']['Other'] += 1

            if status == "quit":
                quit_count += 1

            if quit_count == cores:
                break

        for p in p_list:
            p.join()

        return static_res, static_sg_lizhi, static_bd_lizhi

    except Exception as err:
        print("[parallel_process]:%s" % err)

def gen_result_dir(dirstr):
    try:
        if "/" in dirstr:
            os.makedirs(dirstr)
        else:
            os.mkdir(dirstr)

    except FileExistsError:
        print('[gen_result_dir] Dir exists: %s. remove dir, mkdir again' % (dirstr))
        shutil.rmtree(dirstr)

        if "/" in dirstr:
            os.makedirs(dirstr)
        else:
            os.mkdir(dirstr)

if __name__ == '__main__':

    #多进程抓取和数据分析
    start = time.time()

    today = datetime.date.today().strftime("%Y-%m-%d")
    scene_dir = ['bd_lizhi_sg_other', 'sg_lizhi_baidu_lizhi', 'sg_lizhi_baidu_baike', 'sg_lizhi_baidu_official', 'sg_lizhi_baidu_other']

    #生成搜狗词源的现场目录
    for dir in scene_dir:
        gen_result_dir(today + "/sogou/" + dir)

    #生成百度词源的现场目录
    for dir in scene_dir:
        gen_result_dir(today + "/baidu/" + dir)

    #词源为搜狗词，返回三个字典：1、在搜狗/百度的召回情况 2、搜狗首条为立知的词，在百度的召回情况 3、百度首条为立知的词，在搜狗的召回情况
    sogou_word_static_res, sogou_word_sg_lizhi, sogou_word_bd_lizhi = parallel_process(sogou_wordlist)
    print("sogou word:%s\t%s\t%s" % (sogou_word_static_res, sogou_word_sg_lizhi, sogou_word_bd_lizhi))

    #词源为百度词，返回三个字典：1、在搜狗/百度的召回情况 2、搜狗首条为立知的词，在百度的召回情况 3、百度首条为立知的词，在搜狗的召回情况
    baidu_word_static_res, baidu_word_sg_lizhi, baidu_word_bd_lizhi = parallel_process(baidu_wordlist)
    print("baidu word:%s\t%s\t%s" % (baidu_word_static_res, baidu_word_sg_lizhi, baidu_word_bd_lizhi))

    end = time.time()

    #汇总邮件内容
    total_table_head = ['数据抓取', '首条为立知', '首条为VR', '首条为百科', '首条为官网', '首条为其他']
    partial_table_head = ['首条为立知', '首条为VR', '首条为百科', '首条为官网', '首条为其他']
    static_item = ['Lizhi', 'VR', 'Baike', 'Official', 'Other']

    sogou_word_content = "" #搜狗词源的邮件结果内容
    baidu_word_content = "" #百度词源的邮件结果内容

    #抓取耗时
    runtime_html = Template.html_p_time(start, end)
    #搜狗词总量
    sogou_word_content += Template.html_p("搜狗日志取词总量：" + str(len(sogou_wordlist)))
    #搜狗词在搜狗/百度的召回情况
    sogou_word_content += Template.double_dict_to_html_table(sogou_word_static_res, total_table_head, static_item)
    #搜狗首条为立知的词，在百度的召回情况
    sogou_word_content += Template.html_p("搜狗首条为立知的词，在百度的召回情况:")
    sogou_word_content += Template.single_dict_to_html_table(sogou_word_sg_lizhi, partial_table_head, static_item)
    #百度首条为立知的词，在搜狗的召回情况
    sogou_word_content += Template.html_p("百度首条为立知的词，在搜狗的召回情况:")
    sogou_word_content += Template.single_dict_to_html_table(sogou_word_bd_lizhi, partial_table_head, static_item)

    #百度词总量
    baidu_word_content += Template.html_p("百度搜索取词总量：" + str(len(baidu_wordlist)))
    #百度词在搜狗/百度的召回情况
    baidu_word_content += Template.double_dict_to_html_table(baidu_word_static_res, total_table_head, static_item)
    #搜狗首条为立知的词，在百度的召回情况
    baidu_word_content += Template.html_p("搜狗首条为立知的词，在百度的召回情况:")
    baidu_word_content += Template.single_dict_to_html_table(baidu_word_sg_lizhi, partial_table_head, static_item)
    #百度首条为立知的词，在搜狗的召回情况
    baidu_word_content += Template.html_p("百度首条为立知的词，在搜狗的召回情况:")
    baidu_word_content += Template.single_dict_to_html_table(baidu_word_bd_lizhi, partial_table_head, static_item)

    report_tmp_path = "lizhi_monitor.html"
    report_content = "".join([Template.html_general_css(), Template.html_h3_title("立知效果-召回对比"), runtime_html,
                              sogou_word_content, baidu_word_content])
    DataFile.write_full_file(report_tmp_path, report_content)

    #发送邮件
    maillist = "yinjingjing@sogou-inc.com"
    Mail.sendMail("立知效果专项监控", report_tmp_path, maillist)

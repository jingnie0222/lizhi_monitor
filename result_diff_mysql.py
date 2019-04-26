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
import DBHelper
import pysnooper


fetch_service = "http://snapshot.sogou/agent/wget.php?"

#sogou_wordlist = ['马来西亚官方语言', '平头哥是什么动物', '绿茶婊是什么意思', '电阻的作用', '相对原子质量', 'zuzu化妆品怎么样','冯远征和梁丹妮']

sogou_wordlist = DataFile.read_file_into_list("./sogou")
baidu_wordlist = DataFile.read_file_into_list("./baidu")

#root_result_dir = "/search/odin/yinjingjing/lizhi_result/"  #linux
root_result_dir = ""  #windows
today = datetime.date.today().strftime("%Y-%m-%d")
scene_dir = ['bd_lizhi_sg_other', 'sg_lizhi_bd_baike', 'sg_lizhi_bd_official', 'sg_lizhi_bd_other']

task_table_neme = "lizhi_task"
result_table_name = "lizhi_resultdetail"


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
    #url = fetch_service + "engine=wap_sogou" + "&query=" + quote(query)
    url = "http://wap.sogou.com.inner/web/searchList.jsp?keyword=" + quote(query)
    #print(url,query)
    try:
        res = requests.get(url)
        res.encoding = 'utf-8'
        return res.text
    except Exception as err:
        print('[sg_fetch_res]: %s' % err)


def bd_fetch_page(query):
    url = fetch_service + "engine=wap_baidu" + "&query=" + quote(query)
    #print(url,query)
    try:
        res = requests.get(url)
        res.encoding = 'utf-8'
        return res.text
    except Exception as err:
        print('[bd_fetch_res]: %s' % err)


def fetch_and_analysis(word_list, query_from, queue):
    #搜狗召回立知，百度为Other，抽样保存现场时计数使用
    index = 0

    #同一个query在搜狗侧和百度侧分别抓取并对结果分类， query_from表示用的是搜狗词还是百度词，用于保存现场到对应目录
    for query in word_list:
        sg_scene_link = ""
        bd_scene_link = ""
        try:
            #print(query)
            #fetch from sogou
            sogou_page = sg_fetch_page(query)
            sg_ret = parse_sogou.parse_sogou(sogou_page)
            #print("sg_ret=%s" % sg_ret)

            # fetch from baidu
            baidu_page = bd_fetch_page(query)
            bd_ret = parse_baidu.parse_baidu(baidu_page)
            #print("bd_ret=%s" % bd_ret)

            sg_res_type = sg_ret['res_type']
            #sg_res_err = sg_ret['error']
            bd_res_type = bd_ret['res_type']
            #bd_res_err = bd_ret['error']

            '''
            #queue的内容为线程状态、engine、查询词、搜狗结果类别、百度结果类别
            queue.put(("working", "SG", query, sg_res_type, bd_res_type))
            queue.put(("working", "BD", query, sg_res_type, bd_res_type))
            '''

            ###其他现场的抓图先注掉，先抓两方都是立知的
            #如果百度召回立知，搜狗正常抓到结果且结果为其他，保留现场
            if bd_res_type == 'Lizhi' and sg_res_type == 'Other':
                my_screenshot.get_sogou_screenshot(query, "/".join([root_result_dir, today, query_from, "bd_lizhi_sg_other"]))
                my_screenshot.get_baidu_screenshot(query, "/".join([root_result_dir, today, query_from, "bd_lizhi_sg_other"]))
                sg_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'bd_lizhi_sg_other', quote(query)]) + "_sogou.png"
                bd_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'bd_lizhi_sg_other', quote(query)]) + "_baidu.png"

            #如果搜狗召回立知，百度正常抓到结果，且结果为非立知结果，保留现场
            if sg_res_type == 'Lizhi' and bd_res_type == 'Baike':
                my_screenshot.get_sogou_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_baike"]))
                my_screenshot.get_baidu_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_baike"]))
                sg_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'sg_lizhi_bd_baike', quote(query)]) + "_sogou.png"
                bd_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'sg_lizhi_bd_baike', quote(query)]) + "_baidu.png"

            if sg_res_type == 'Lizhi' and bd_res_type == 'Official':
                my_screenshot.get_sogou_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_official"]))
                my_screenshot.get_baidu_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_official"]))
                sg_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'sg_lizhi_bd_official', quote(query)]) + "_sogou.png"
                bd_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'sg_lizhi_bd_official', quote(query)]) + "_baidu.png"

            if sg_res_type == 'Lizhi' and bd_res_type == 'Other':
                #抽样保存现场
                if index % 15 == 0:
                    my_screenshot.get_sogou_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_other"]))
                    my_screenshot.get_baidu_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_other"]))
                    sg_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'sg_lizhi_bd_other', quote(query)]) + "_sogou.png"
                    bd_scene_link = "/".join(['http://10.144.96.115/lizhi_result', today, query_from, 'sg_lizhi_bd_other', quote(query)]) + "_baidu.png"
                index += 1

            #给静军提供两方都是立知结果的数据
            #if sg_res_type == 'Lizhi' and bd_res_type == 'Lizhi':
                #my_screenshot.get_sogou_first_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_lizhi"]))
                #my_screenshot.get_baidu_first_screenshot(query, "/".join([root_result_dir, today, query_from, "sg_lizhi_bd_lizhi"]))

            #queue的内容为线程状态、查询词、query_from、搜狗结果类别、百度结果类别、搜狗现场、百度现场、是否解决
            queue.put(("working", query, query_from, sg_res_type, bd_res_type, sg_scene_link, bd_scene_link, ""))


        except Exception as err:
            print("[fetch_and_analysis]:%s" % err)
            continue

    queue.put(("quit", None, None, None, None, None, None, None))


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

#@pysnooper.snoop()
def parallel_process(wordlist, query_from, mysql_db):

    cores = multiprocessing.cpu_count()
    print(cores)
    queue = multiprocessing.Queue()
    p_list = []
    quit_count = 0

    '''
    static_res = dict()
    #搜狗首条召回情况
    static_res['Sogou'] = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0, 'Error': 0}
    #百度首条召回情况
    static_res['Baidu'] = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0, 'Error': 0}

    #搜狗首条为立知结果的词，在百度的召回情况
    static_sg_lizhi = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0, 'Error': 0}
    #百度首条为立知结果的词，在搜狗的召回情况
    static_bd_lizhi = {'Lizhi': 0, 'VR': 0, 'Baike': 0, 'Official': 0, 'Other': 0, 'Error': 0}
    '''
    try:
        #生成与核数对应的进程数，多进程执行fetch_and_analysis，将词表按进程数切分，每个进程处理对应的词表
        for i in range(cores):
            p = multiprocessing.Process(target=fetch_and_analysis, args=(split_wordlist(wordlist, cores, i), query_from, queue))
            p.start()
            p_list.append(p)

        key_str = r'query,query_from,sg_res_type,bd_res_type,sg_scene,bd_scene,is_resolve'

        while True:

            #queue的内容为线程状态、查询词、query_from、搜狗结果类别、百度结果类别、搜狗现场、百度现场、是否解决
            (status, query, query_from, sg_ret, bd_ret, sg_link, bd_link, is_resolve) = queue.get()
            #print(status, query, query_from, sg_ret, bd_ret, sg_link, bd_link, is_resolve)

            if status == 'working':
                sql = r'INSERT INTO %s (%s) VALUES %s;' % (result_table_name, key_str, (query, query_from, sg_ret, bd_ret, sg_link, bd_link, is_resolve))
                print("sql=%s" % sql)
                #mysql_db._execute(sql)

            '''
            #queue的内容为线程状态、engine、查询词、搜狗结果类别、百度结果类别
            (status, engine, query, sg_ret, bd_ret) = queue.get()
            print(status, engine, query, sg_ret, bd_ret)
            
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
                    elif 'Other' == bd_ret:
                        static_sg_lizhi['Other'] += 1
                    elif "Error" == bd_ret:
                        static_sg_lizhi['Error'] += 1
    
                elif "VR" == sg_ret:
                    static_res['Sogou']['VR'] += 1
                elif "Baike" == sg_ret:
                    static_res['Sogou']['Baike'] += 1
                elif "Official" == sg_ret:
                    static_res['Sogou']['Official'] += 1
                elif 'Other' == sg_ret:
                    static_res['Sogou']['Other'] += 1
                elif "Error" == sg_ret:
                    static_res['Sogou']['Error'] += 1
    
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
                    elif 'Other' == sg_ret:
                        static_bd_lizhi['Other'] += 1
                    elif 'Error' == sg_ret:
                        static_bd_lizhi['Error'] += 1
    
                elif "VR" == bd_ret:
                    static_res['Baidu']['VR'] += 1
                elif "Baike" == bd_ret:
                    static_res['Baidu']['Baike'] += 1
                elif "Official" == bd_ret:
                    static_res['Baidu']['Official'] += 1
                elif "Other" == bd_ret:
                    static_res['Baidu']['Other'] += 1
                elif "Error" == bd_ret:
                    static_res['Baidu']['Error'] += 1
            '''

            if status == "quit":
                quit_count += 1

            if quit_count == cores:
                break

        for p in p_list:
            p.join()

        #return static_res, static_sg_lizhi, static_bd_lizhi

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

    #监控介绍
    monitor_info = '''
    1、该监控主要是对比搜狗搜索和百度搜索首条结果的召回情况，判断首条结果的类别，包括：立知、VR、百科、官网和其他结果；<br />
    2、词源：分别从搜狗和百度侧取10000词；<br />
    3、搜狗的立知结果包括：首条有立知icon的结果，首条没有立知icon但是属于立知医疗的结果；<br />
    4、百度的立知结果包括：精选摘要、优质问答、图谱结果；<br />
    5、由于无法区分百度的VR结果和普通结果，故将其统一归类为“其他结果”；<br />
    6、页面抓取采用的是数据抓取组提供的代理服务，有时会存在抓不到结果的情况，将此归类为“ERROR”；<br />
    7、对开发同学关注的几种情况，保存现场，包括：百度首条立知-搜狗首条其他、搜狗首条立知-百度首条百科/官网/其他，<br />
       搜狗首条立知-百度首条其他，抽样保存现场，其他全量保存现场；<br />
    8、由于抓取结果无css样式，保存现场通过实际查询+截图实现。由于搜索结果可能会不稳定，导致统计数据和截图现场存在偏差；
    '''

    #多进程抓取和数据分析
    start = time.time()

    #生成搜狗词源的现场目录
    for dir in scene_dir:
        gen_result_dir(root_result_dir + today + "/sogou/" + dir)

    #生成百度词源的现场目录
    for dir in scene_dir:
        gen_result_dir(root_result_dir + today + "/baidu/" + dir)

    #生成db对象
    db = DBHelper.init_db("mysql.conf", "lizhi")

    parallel_process(sogou_wordlist, "sogou", db)
    parallel_process(baidu_wordlist, "baidu", db)

    '''
    #词源为搜狗词，返回三个字典：1、在搜狗/百度的召回情况 2、搜狗首条为立知的词，在百度的召回情况 3、百度首条为立知的词，在搜狗的召回情况
    sogou_word_static_res, sogou_word_sg_lizhi, sogou_word_bd_lizhi = parallel_process(sogou_wordlist, "sogou")
    print("sogou word:%s\t%s\t%s" % (sogou_word_static_res, sogou_word_sg_lizhi, sogou_word_bd_lizhi))

    #词源为百度词，返回三个字典：1、在搜狗/百度的召回情况 2、搜狗首条为立知的词，在百度的召回情况 3、百度首条为立知的词，在搜狗的召回情况
    baidu_word_static_res, baidu_word_sg_lizhi, baidu_word_bd_lizhi = parallel_process(baidu_wordlist, "baidu")
    print("baidu word:%s\t%s\t%s" % (baidu_word_static_res, baidu_word_sg_lizhi, baidu_word_bd_lizhi))
    '''

    end = time.time()

    '''
    #汇总邮件内容
    total_table_head = ['数据抓取', '首条为立知', '首条为VR', '首条为百科', '首条为官网', '首条为其他', 'ERROR']
    partial_table_head = ['首条为立知', '首条为VR', '首条为百科', '首条为官网', '首条为其他', 'ERROR']
    static_item = ['Lizhi', 'VR', 'Baike', 'Official', 'Other', 'Error']

    sogou_word_content = "" #搜狗词源的邮件结果内容
    baidu_word_content = "" #百度词源的邮件结果内容

    #抓取耗时
    runtime_html = Template.html_p_time(start, end)
    #搜狗词总量
    sogou_word_content += Template.html_p("搜狗日志取词总量：" + str(len(sogou_wordlist)))
    #搜狗词在搜狗/百度的召回情况
    sogou_word_content += Template.double_dict_to_html_table(sogou_word_static_res, len(sogou_wordlist), total_table_head, static_item)
    #搜狗首条为立知的词，在百度的召回情况
    sogou_word_content += Template.html_p("搜狗首条为立知的词，在百度的召回情况:")
    sogou_word_content += Template.single_dict_to_html_table(sogou_word_sg_lizhi, partial_table_head, static_item)
    #相关现场地址
    sogou_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'sogou', 'sg_lizhi_bd_baike']), "搜狗首条立知-百度首条百科")
    sogou_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'sogou', 'sg_lizhi_bd_official']), "搜狗首条立知-百度首条官网")
    sogou_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'sogou', 'sg_lizhi_bd_other']), "搜狗首条立知-百度首条其他")
    #百度首条为立知的词，在搜狗的召回情况
    sogou_word_content += Template.html_p("百度首条为立知的词，在搜狗的召回情况:")
    sogou_word_content += Template.single_dict_to_html_table(sogou_word_bd_lizhi, partial_table_head, static_item)
    #相关现场地址
    sogou_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'sogou', 'bd_lizhi_sg_other']), "百度首条立知-搜狗首条其他")


    #百度词总量
    baidu_word_content += Template.html_p("百度搜索取词总量：" + str(len(baidu_wordlist)))
    #百度词在搜狗/百度的召回情况
    baidu_word_content += Template.double_dict_to_html_table(baidu_word_static_res, len(baidu_wordlist), total_table_head, static_item)
    #搜狗首条为立知的词，在百度的召回情况
    baidu_word_content += Template.html_p("搜狗首条为立知的词，在百度的召回情况:")
    baidu_word_content += Template.single_dict_to_html_table(baidu_word_sg_lizhi, partial_table_head, static_item)
    #相关现场地址
    baidu_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'baidu', 'sg_lizhi_bd_baike']), "搜狗首条立知-百度首条百科")
    baidu_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'baidu', 'sg_lizhi_bd_official']), "搜狗首条立知-百度首条官网")
    baidu_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'baidu', 'sg_lizhi_bd_other']), "搜狗首条立知-百度首条其他")
    #百度首条为立知的词，在搜狗的召回情况
    baidu_word_content += Template.html_p("百度首条为立知的词，在搜狗的召回情况:")
    baidu_word_content += Template.single_dict_to_html_table(baidu_word_bd_lizhi, partial_table_head, static_item)
    #相关现场地址
    baidu_word_content += Template.html_a_link("/".join(['http://10.144.96.115/lizhi_result', today, 'baidu', 'bd_lizhi_sg_other']), "百度首条立知-搜狗首条其他")

    report_tmp_path = "lizhi_monitor.html"
    report_content = "".join([Template.html_general_css(), Template.html_h3_title("立知效果-召回对比"), Template.html_p_spe(monitor_info), runtime_html,
                              sogou_word_content, baidu_word_content])
    DataFile.write_full_file(report_tmp_path, report_content)

    #发送邮件
    maillist = "yinjingjing@sogou-inc.com"
    Mail.sendMail("立知效果专项监控", report_tmp_path, maillist)
    '''
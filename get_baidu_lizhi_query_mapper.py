#!/usr/bin/env python

import re
import os
import sys

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

def extract_baidu_result(dinfo):
  pat = re.compile('<.*?>')
  res = []
  html = dinfo['snapshot']
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
      lizhi_key = filter(lambda x: block.find(x) != -1, key_lst)[0]
      label = 'lizhi'
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
        label = 'lizhi'
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

def do_work():
  for line in sys.stdin:
    try:
      tmp = line.split('\t', 1)
      if len(tmp) != 2:
        continue
      html_path, line = tmp
      dinfo = {}
      dinfo['snapshot'] = line.strip()
    except:
      continue
    if dinfo:
      #res = extract_baidu_result(dinfo)
      try:
        res = extract_baidu_result(dinfo)
      except:
        continue
      has_lizhi = False
      if res:
        for i, (query, label, url, title, content) in enumerate(res):
          if url and title and content and label and label == 'lizhi':
            print '\t'.join((query, label, url, title.rsplit('_', 1)[0], content.replace('\xe2\x80\x9c</span>', '')))
            has_lizhi = True
            break
      if not has_lizhi:
        os.remove(html_path)

if __name__ == '__main__':
  do_work()

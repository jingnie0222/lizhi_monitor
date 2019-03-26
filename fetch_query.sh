#!/bin/bash

QUERY_CNT=10000

sh getquery.sh $QUERY_CNT 3 "" "" 7 "baidu" wap
python3 gbk_to_utf8.py query.txt baidu

sh getquery.sh $QUERY_CNT 3 "" "" 7 "sogou" wap
#mv query.txt sogou
python3 gbk_to_utf8.py query.txt baidu

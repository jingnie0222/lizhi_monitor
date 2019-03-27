#!/bin/bash

QUERY_CNT=10000
rm query.txt -rf

sh getquery.sh $QUERY_CNT 3 "" "" 7 "baidu" wap
iconv -f gbk -t utf8 query.txt -c -o sogou
rm query.txt -rf

sh getquery.sh $QUERY_CNT 3 "" "" 7 "sogou" wap
iconv -f gbk -t utf8 query.txt -c -o baidu
rm query.txt -rf

sh getquery.sh $QUERY_CNT 3 "" "" 7 "google" pc
iconv -f gbk -t utf8 query.txt -c -o google
rm query.txt -rf
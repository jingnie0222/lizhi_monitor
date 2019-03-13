#!/bin/bash

QUERY_CNT=10000

sh getquery.sh $QUERY_CNT 3 "" "" 7 "baidu" wap
mv query.txt baidu

sh getquery.sh $QUERY_CNT 3 "" "" 7 "sogou" wap
mv query.txt sogou

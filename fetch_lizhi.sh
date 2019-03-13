#!/bin/bash

DATE=`date -d "" +"%Y%m%d"`
#DATE=20180102
CUR_DIR=`cd $(dirname $0);pwd;`

QUERY_CNT=5000
QUERY_SRC_DIR=../src/get_query/
QUERY_DATA_DIR=../data/query/

# Get query sample
cd $CUR_DIR/$QUERY_DATA_DIR
ln -s $CUR_DIR/$QUERY_SRC_DIR/getquery.sh getquery.sh
ln -s $CUR_DIR/$QUERY_SRC_DIR/sample.sh sample.sh

sh getquery.sh $QUERY_CNT 3 "" "" 7 "baidu" wap
mv query.txt baidu
sh getquery.sh $QUERY_CNT 3 "" "" 7 "sogou" wap
mv query.txt sogou

rm getquery.sh
rm sample.sh

# Get Result
cd $CUR_DIR
# Get Baidu Result
nohup sh fetch_baidu_lizhi.sh $DATE > /tmp/log_fetch_baidu.txt 2>&1 &
# Get Sogou Result
nohup sh fetch_sogou_lizhi.sh $DATE > /tmp/log_fetch_sogou.txt 2>&1 &
# Get SogouNoVr Result
nohup sh fetch_sogounovr_lizhi.sh $DATE > /tmp/log_fetch_sogounovr.txt 2>&1 &

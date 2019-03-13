#!/usr/bin/env bash

if [ $# -ne 5 ]; then
	echo "para's number is wrong !!!"
	exit 1
fi

if [ "$1" != "" ]; then
	START=$1
else
	echo "START is empty !!!!"
	exit 1
fi

if [ "$2" != "" ]; then
	END=$2
else
	echo "END is empty !!!!"
	exit 1
fi


if [ "$3" != "" ]; then
	LOG_SOURCE=$3
else
	echo "LOG_SOURCE is empty !!!!"
	exit 1
fi

if [ "$4" != "" ]; then
	LOG_TYPE=$4
else
	echo "LOG_TYPE is empty !!!!"
	exit 1
fi

if [ "$5" != "" ]; then
	QUERY_NUM=$5
else
	echo "QUERY_NUM is empty !!!!"
	exit 1
fi

if [ $LOG_SOURCE = "sogou" -a $LOG_TYPE = "wap" ]
then
	INPUT=/user/ms-search/pengjunrui/instant_query/wap_sogou_instant_query
elif [ $LOG_SOURCE = "sogou" -a $LOG_TYPE = "pc" ]
then
	INPUT=/user/ms-search/pengjunrui/instant_query/pc_sogou_instant_query
elif [ $LOG_SOURCE = "baidu" -a $LOG_TYPE = "pc" ]
then
	INPUT=/user/ms-search/pengjunrui/instant_query/pc_baidu_instant_query
elif [ $LOG_SOURCE = "baidu" -a $LOG_TYPE = "wap" ]
then
	INPUT=/user/ms-search/pengjunrui/instant_query/wap_baidu_instant_query
elif [ $LOG_SOURCE = "google" -a $LOG_TYPE = "pc" ]
then
	INPUT=/user/ms-search/pengjunrui/instant_query/pc_google_instant_query
else
	echo "LOG_SOURCE's or LOG_TYPE's value is wrong !!!"
	exit 2
fi



echo "now sample from "$START"_"$END"_"$LOG_SOURCE"_"$LOG_TYPE"_"$QUERY_NUM

day_cnt=0 #用来保存抽词的总天数
weekend_cnt=0 #用来保存是周末的天数	
curr_day="$START"
while true #从hdfs拖文件下来
do
	YYmm=${curr_day:0:6}
	day_week=`date -d $curr_day +%u`
	
	if [ $day_week -ge 6 ]; then
		weekend_cnt=`expr $weekend_cnt + 1`
	fi

	hadoop fs -test -e $INPUT/$YYmm/$curr_day
	
	if [ $? -ne 0 ] #判断hdfs是否存在此目录
	then
		echo "$INPUT/$YYmm/$curr_day does't exist !!!!"
		exit 1
	fi
	hdfs dfs -getmerge $INPUT/$YYmm/$curr_day/* ${LOG_SOURCE}_${LOG_TYPE}_${curr_day}_tmp
	cut -f 1 ${LOG_SOURCE}_${LOG_TYPE}_${curr_day}_tmp > ${LOG_SOURCE}_${LOG_TYPE}_${curr_day}
	rm -f ${LOG_SOURCE}_${LOG_TYPE}_${curr_day}_tmp
	day_cnt=`expr $day_cnt + 1`
	[ "$curr_day" \< "$END" ] || break
	curr_day=$( date +%Y%m%d --date "$curr_day +1 day" )
done



if [ $LOG_TYPE = "wap" -a $weekend_cnt -ge 1 ]; then
	workday_num=$(echo $QUERY_NUM $day_cnt $weekend_cnt 1.1 | awk '{printf "%d\n",$1/($2+($4-1.0)*$3)}')

	weekend_num=$(echo $workday_num 1.1 | awk '{printf "%d\n",$1*$2}')
	
	words_sum=$(echo $workday_num $weekend_num $day_cnt $weekend_cnt | awk '{printf "%d\n", ($3-$4)*$1+$4*$2}')
	
	if [ $words_sum -lt $QUERY_NUM ]; then
		weekend_num=`expr $weekend_num + 1`	
	fi
	words_sum=$(echo $workday_num $weekend_num $day_cnt $weekend_cnt | awk '{printf "%d\n", ($3-$4)*$1+$4*$2}')
	
	if [ $words_sum -lt $QUERY_NUM ]; then
		workday_num=`expr $workday_num + 1`	
	fi
else

	workday_num=$(echo $QUERY_NUM $day_cnt | awk '{printf "%d\n",$1/$2}')
	words_sum=$(echo $workday_num $day_cnt | awk '{printf "%d\n", $1*$2}')
	
	if [ $words_sum -lt $QUERY_NUM ]; then
		workday_num=`expr $workday_num + 1`	
	fi
fi

echo "workday_num: "$workday_num
echo "weekend_num: "$weekend_num


rm -f query.txt
touch query.txt

curr_day="$START"

while true
do
	day_week=`date -d $curr_day +%u`
	query_num=`wc -l ${LOG_SOURCE}_${LOG_TYPE}_${curr_day} | awk -F" " '{print $1}' `
	
	if [ $day_week -ge 6 -a $LOG_TYPE = "wap" ]; then
		if [ $query_num -lt $weekend_num ]; then
			echo "${LOG_SOURCE}_${LOG_TYPE}_${curr_day} file don't have enough queries !!!"
			exit 1
		fi
		shuf ${LOG_SOURCE}_${LOG_TYPE}_${curr_day} -n $weekend_num >> query.txt
	else
		if [ $query_num -lt $workday_num ]; then
			echo "${LOG_SOURCE}_${LOG_TYPE}_${curr_day} file don't have enough queries !!!"
			exit 1
		fi
		shuf ${LOG_SOURCE}_${LOG_TYPE}_${curr_day} -n $workday_num >> query.txt
	fi
	rm -f ${LOG_SOURCE}_${LOG_TYPE}_${curr_day}

	[ "$curr_day" \< "$END" ] || break
	curr_day=$(date +%Y%m%d --date "$curr_day +1 day")
done



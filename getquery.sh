#!/usr/bin/env bash

#代表想抽取的词的数量。为用户必须设定的选项
QUERY_NUM=$1

TIME_TYPE=$2 #代表抽词时，所采取的模式，可赋值为0,1,2,3,4

#当TIME_TYPE为0时，需要用户设置LOG_TYPE、NUM_DAY、QUERY_NUM。此时当LOG_TYPE为wap时，将从sogou、baidu时间区间为[current yyMMdd-NUM_DAY, current yyMMdd-1]的日志中各自抽取QUERY_NUM*0.5个词，在对sogou wap或者
#baidu wap进行抽词时，周末抽取的词数，将是工作日的1.1倍。当LOG_TYPE为pc时，将从sogou、baidu、google时间区间为[current yyMMdd-NUM_DAY, current yyMMdd-1]的日志中各自抽取QUERY_NUM*0.4,
#QUERY_NUM*0.4,QUERY_NUM*0.2个词。

#当TIME_TYPE为1时，需要用户设置LOG_TYPE、START、END和QUERY_NUM。此时当LOG_TYPE为wap时，将从sogou、baidu时间区间为[START, END]的日志中各自抽取QUERY_NUM*0.5个词，在对sogou wap或者baidu wap进行抽词时，
#周末抽取的词数，将是工作日的1.1倍。当LOG_TYPE为pc时，将从sogou、baidu、google时间区间为[START, END]的日志中各自抽取QUERY_NUM*0.4,QUERY_NUM*0.4,QUERY_NUM*0.2个词。

#当TIME_TYPE为2时，需要用户设置START、END、LOG_SOURCE、LOG_TYPE、QUERY_NUM，代表抽词时间区间为闭区间[START, END]，日志来源为LOG_SOURCE，日志类型为LOG_TYPE。

#当TIME_TYPE为3时，需要用户设置NUM_DAY、LOG_SOURCE、LOG_TYPE、QUERY_NUM。代表抽词时间区间为闭区间[current yyMMdd-NUM_DAY, current yyMMdd-1]。日志来源为LOG_SOURCE，日志类型为LOG_TYPE。
#current yyyyMMdd代表今天的日期。

#当TIME_TYPE为4时，需要用户设置NUM_DAY、LOG_SOURCE、LOG_TYPE、QUERY_NUM。代表抽词时间区间为闭区间[current yyMMdd-NUM_DAY, current yyMMdd-NUM_DAY]。日志来源为LOG_SOURCE，日志类型为LOG_TYPE。
#current yyyyMMdd代表今天的日期。


#当TIME_TYPE为1或者2时，用户需要设置START和END，格式均为yyyyMMdd，代表抽词时间区间为闭区间[START, END]。
START=$3
END=$4

#当TIME_TYPE为0、3、4时，用户需要设置NUM_DAY。NUM_DAY至少为1, 否则程序会报错。
NUM_DAY=$5

#代表日志的来源，可赋值为sogou或者baidu或者google
LOG_SOURCE=$6

#代表日志的类型，可赋值为wap或者pc，但当LOG_SOURCE为google时，只可为pc
LOG_TYPE=$7

#----------------此线以上需要用户设置------------------------

if [ $TIME_TYPE != "0" -a $TIME_TYPE != "1" -a $TIME_TYPE != "2" -a $TIME_TYPE != "3" -a $TIME_TYPE != "4" ]; then
	echo "TIME_TYPE's value is wrong !!!"
	exit 2
fi

if [ $TIME_TYPE = "0" -o $TIME_TYPE = "3" -o $TIME_TYPE = "4" ]; then
	if [ $NUM_DAY -lt 1 ]; then
		echo "NUM_DAY's should at least be 1 !!!"
		exit 2
	fi
fi


today=$(date +%Y%m%d)

if [ $TIME_TYPE = "1" -o $TIME_TYPE = "2" ]; then
	if [ ${#START} -ne 8 -o ${#END} -ne 8 ] #判断START和END的格式
	then
		echo "START's or END's format is wrong !!!"
		exit 2
	fi


	if [ "$END" \> "$today" -o "$END" = "$today" ] #END不应该>=today
	then
		echo "END should < today !!!"
		exit 2
	fi

	if [ "$START" \> "$END" ] #START应该<=END
	then
		echo "START should <= END !!!"
		exit 2
	fi
fi

#----------------以上对一些参数的赋值进行了check------------------------

if [ $TIME_TYPE = "0" -o $TIME_TYPE = "1" ]
then
	if [ $TIME_TYPE = "0" ]; then
		end=$( date +%Y%m%d --date "$today -1 day" )
		start=$( date +%Y%m%d --date "$today -$NUM_DAY day" )
	else
		end=$END
		start=$START
	fi

	echo "start date is: "$start
	echo "end date is: "$end

	if [ $LOG_TYPE = "wap" ]; then
		baidu_wap_num=$(echo $QUERY_NUM 0.5 | awk '{printf "%d\n",$1*$2}')
		echo "QUERY_NUM sample is: "$QUERY_NUM
		echo "baidu wap sample num is: "$baidu_wap_num
		if [ `expr $baidu_wap_num \* 2` -lt $QUERY_NUM ]; then
			baidu_wap_num=`expr $baidu_wap_num + 1`
		fi
		sogou_wap_num=$baidu_wap_num

		echo "sogou wap sample num is: "$sogou_wap_num
		sh sample.sh $start $end "baidu" "wap" $baidu_wap_num
		if [ $? -ne 0 ]; then
			echo "fail!!! when sample from baidu wap"
			exit 1
		fi

		cat query.txt > baidu_query.txt
		sh sample.sh $start $end "sogou" "wap" $sogou_wap_num
		if [ $? -ne 0 ]; then
			echo "fail!!! when sample from sogou wap"
			exit 1
		fi
		cat query.txt > sogou_query.txt
		cat baidu_query.txt sogou_query.txt > query.txt
		rm -f baidu_query.txt sogou_query.txt
	else
		baidu_pc_num=$(echo $QUERY_NUM 0.4 | awk '{printf "%d\n",$1*$2}')
		sogou_pc_num=$(echo $QUERY_NUM 0.4 | awk '{printf "%d\n",$1*$2}')
		google_pc_num=$(echo $QUERY_NUM 0.2 | awk '{printf "%d\n",$1*$2}')
		
		tmp_pc_num=`expr $baidu_pc_num + $sogou_pc_num`
		sum=`expr $tmp_pc_num + $google_pc_num`
		
		if [ $sum -lt $QUERY_NUM ]; then
			baidu_pc_num=`expr $baidu_pc_num + 1`
			sogou_pc_num=`expr $sogou_pc_num + 1`
			google_pc_num=`expr $google_pc_num + 1`
		fi

		sh sample.sh $start $end "baidu" "pc" $baidu_pc_num
		if [ $? -ne 0 ]; then
			echo "fail!!! when sample from baidu pc"
			exit 1
		fi
		cat query.txt > baidu_query.txt
		sh sample.sh $start $end "sogou" "pc" $sogou_pc_num
		if [ $? -ne 0 ]; then
			echo "fail!!! when sample from sogou pc"
			exit 1
		fi
		cat query.txt > sogou_query.txt
		sh sample.sh $start $end "google" "pc" $google_pc_num
		if [ $? -ne 0 ]; then
			echo "fail!!! when sample from google pc"
			exit 1
		fi
		cat query.txt > google_query.txt

		cat baidu_query.txt sogou_query.txt google_query.txt > query.txt
		rm -f baidu_query.txt sogou_query.txt google_query.txt
	fi
elif [ $TIME_TYPE = "2" -o $TIME_TYPE = "3" -o $TIME_TYPE = "4" ]
then
	if [ $TIME_TYPE = "2" ]; then
		start=$START
		end=$END
	elif [ $TIME_TYPE = "3" ]; then
		start=$( date +%Y%m%d --date "$today -$NUM_DAY day" )
		end=$( date +%Y%m%d --date "$today -1 day" )
	else
		start=$( date +%Y%m%d --date "$today -$NUM_DAY day" )
		end=$( date +%Y%m%d --date "$today -$NUM_DAY day" )
	fi

	sh sample.sh $start $end $LOG_SOURCE $LOG_TYPE $QUERY_NUM
	if [ $? -ne 0 ]; then
		echo "fail!!! when sample from ${LOG_SOURCE} ${LOG_TYPE}"
		exit 1
	fi
fi


echo "query.txt is done !!!"

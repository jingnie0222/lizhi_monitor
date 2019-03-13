#!/usr/bin/env bash

#�������ȡ�Ĵʵ�������Ϊ�û������趨��ѡ��
QUERY_NUM=$1

TIME_TYPE=$2 #������ʱ������ȡ��ģʽ���ɸ�ֵΪ0,1,2,3,4

#��TIME_TYPEΪ0ʱ����Ҫ�û�����LOG_TYPE��NUM_DAY��QUERY_NUM����ʱ��LOG_TYPEΪwapʱ������sogou��baiduʱ������Ϊ[current yyMMdd-NUM_DAY, current yyMMdd-1]����־�и��Գ�ȡQUERY_NUM*0.5���ʣ��ڶ�sogou wap����
#baidu wap���г��ʱ����ĩ��ȡ�Ĵ��������ǹ����յ�1.1������LOG_TYPEΪpcʱ������sogou��baidu��googleʱ������Ϊ[current yyMMdd-NUM_DAY, current yyMMdd-1]����־�и��Գ�ȡQUERY_NUM*0.4,
#QUERY_NUM*0.4,QUERY_NUM*0.2���ʡ�

#��TIME_TYPEΪ1ʱ����Ҫ�û�����LOG_TYPE��START��END��QUERY_NUM����ʱ��LOG_TYPEΪwapʱ������sogou��baiduʱ������Ϊ[START, END]����־�и��Գ�ȡQUERY_NUM*0.5���ʣ��ڶ�sogou wap����baidu wap���г��ʱ��
#��ĩ��ȡ�Ĵ��������ǹ����յ�1.1������LOG_TYPEΪpcʱ������sogou��baidu��googleʱ������Ϊ[START, END]����־�и��Գ�ȡQUERY_NUM*0.4,QUERY_NUM*0.4,QUERY_NUM*0.2���ʡ�

#��TIME_TYPEΪ2ʱ����Ҫ�û�����START��END��LOG_SOURCE��LOG_TYPE��QUERY_NUM��������ʱ������Ϊ������[START, END]����־��ԴΪLOG_SOURCE����־����ΪLOG_TYPE��

#��TIME_TYPEΪ3ʱ����Ҫ�û�����NUM_DAY��LOG_SOURCE��LOG_TYPE��QUERY_NUM��������ʱ������Ϊ������[current yyMMdd-NUM_DAY, current yyMMdd-1]����־��ԴΪLOG_SOURCE����־����ΪLOG_TYPE��
#current yyyyMMdd�����������ڡ�

#��TIME_TYPEΪ4ʱ����Ҫ�û�����NUM_DAY��LOG_SOURCE��LOG_TYPE��QUERY_NUM��������ʱ������Ϊ������[current yyMMdd-NUM_DAY, current yyMMdd-NUM_DAY]����־��ԴΪLOG_SOURCE����־����ΪLOG_TYPE��
#current yyyyMMdd�����������ڡ�


#��TIME_TYPEΪ1����2ʱ���û���Ҫ����START��END����ʽ��ΪyyyyMMdd��������ʱ������Ϊ������[START, END]��
START=$3
END=$4

#��TIME_TYPEΪ0��3��4ʱ���û���Ҫ����NUM_DAY��NUM_DAY����Ϊ1, �������ᱨ��
NUM_DAY=$5

#������־����Դ���ɸ�ֵΪsogou����baidu����google
LOG_SOURCE=$6

#������־�����ͣ��ɸ�ֵΪwap����pc������LOG_SOURCEΪgoogleʱ��ֻ��Ϊpc
LOG_TYPE=$7

#----------------����������Ҫ�û�����------------------------

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
	if [ ${#START} -ne 8 -o ${#END} -ne 8 ] #�ж�START��END�ĸ�ʽ
	then
		echo "START's or END's format is wrong !!!"
		exit 2
	fi


	if [ "$END" \> "$today" -o "$END" = "$today" ] #END��Ӧ��>=today
	then
		echo "END should < today !!!"
		exit 2
	fi

	if [ "$START" \> "$END" ] #STARTӦ��<=END
	then
		echo "START should <= END !!!"
		exit 2
	fi
fi

#----------------���϶�һЩ�����ĸ�ֵ������check------------------------

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

#!/bin/env python
#coding:utf8
#########################################################################
#
#File name: check_http_status.py
#Description: 利用python的pycurl模块,获取url的返回状态和返回时间
#Author:pangli
#mail:artie_lee@163.com
#
#改进支持检查网页内容是否包含指定的字符串
#Author:cranezhou
#########################################################################
import pycurl
# import fcntl
import sys
import os
import StringIO
import time
from optparse import OptionParser

TIME = int(time.time())
# data_path = os.path.split(os.path.realpath(__file__))[0] + "/http_data/"
# #判断数据文件夹是否存在
# if not os.path.isdir(data_path):
#     os.makedirs(data_path)

#返回代码:200-207成功状态,300-307重定向状态,此处也划分到成功里
code_rule = [200, 201, 202, 203, 204, 205, 206, 207, 300, 301, 302, 303, 304, 305, 306, 307]
usage = "python %(script_name)s -u <url|ipaddress> -w <connectTime,totalTime> -c <connectTime,totalTime> -t <http|https> -s <String>"

parser = OptionParser(usage=usage % {"script_name" : sys.argv[0]})
parser.add_option("-u", "--url", dest="url", help="url or ipaddress")
parser.add_option("-t", "--type", dest="type", help="transport protocols type,http|https")
parser.add_option("-w", "--warning", dest="w_value", help="alarm value(warning)")
parser.add_option("-c", "--critical", dest="c_value", help="alarm value(critical)")
parser.add_option("-s", "--string", dest="string", help="String to expect in the content")

option,args = parser.parse_args()
if option.url == -1 or option.w_value == -1 or option.c_value == -1 or option.type == -1:
    parser.print_help()
    sys.exit(3)

def http_url_req(url):
    try:
        buf = StringIO.StringIO()
        status = dict()
        #去掉用户输入的url头
        format_url = url.replace("http://", "")
        req = pycurl.Curl()
        #perform返回写入缓存忽略掉
        req.setopt(req.WRITEFUNCTION, buf.write)
        #设置请求的URL
        req.setopt(req.URL,"http://" + format_url)
        #设置连接超时
        req.setopt(req.TIMEOUT,5)
        #执行请求
        req.perform()
        status["return_code"] = req.getinfo(pycurl.HTTP_CODE)
        status["con_time"] = float("%0.3f" % req.getinfo(pycurl.CONNECT_TIME))
        status["tol_time"] = float("%0.3f" % req.getinfo(pycurl.TOTAL_TIME))
        status["body_content"] = buf.getvalue()
        req.close()
        return status
    except pycurl.error,e:
        print "The http status  : CRITICAL | connect failed "
        sys.exit(2)
    except Exception, e:
        print str(e)
        sys.exit(3)

def https_url_req(url):
    try:
        buf = StringIO.StringIO()
        status = dict()
        #去掉用户输入的url头
        format_url = url.replace("https://", "")
        req = pycurl.Curl()
        #perform返回写入缓存忽略掉
        req.setopt(req.WRITEFUNCTION, buf.write)
        #忽略证书检查
        req.setopt(req.SSL_VERIFYPEER, 0)
        #忽略主机验证
        req.setopt(req.SSL_VERIFYHOST, 0)
        #设置请求的URL
        req.setopt(req.URL,"https://" + format_url)
        #设置超时连接
        req.setopt(req.TIMEOUT,5)
        #执行请求
        req.perform()
        status["return_code"] = req.getinfo(pycurl.HTTP_CODE)
        status["con_time"] = float("%0.3f" % req.getinfo(pycurl.CONNECT_TIME))
        status["tol_time"] = float("%0.3f" % req.getinfo(pycurl.TOTAL_TIME))
        status["body_content"] = buf.getvalue()
        req.close()
        return status
    except pycurl.error:
        print "The https status  : CRITICAL | connect failed "
        sys.exit(2)
    except Exception, e:
        print str(e)
        sys.exit(3)

#判断报警状态
def alarm(**params):
    w = dict()
    c = dict()
    print_result  = "The http status  : %(status)s | URL=%(ip)s http_return_code=%(return_code)s connect_time=%(c_time)s total_time=%(t_time)s"
    code = params["return_code"]
    con_time = round(params["con_time"],3)
    tol_time = round(params["tol_time"],3)
    URL = params["url"]
    w["cTime"],w["tTime"] = [float(each) for each in (option.w_value).split(",")]
    c["cTime"],c["tTime"] = [float(each) for each in (option.c_value).split(",")]
    body_content = params["body_content"]
    #报警判断
    if cmp(con_time,c["cTime"]) >= 0 or cmp(tol_time,c["tTime"]) >= 0 or code not in code_rule:
        print print_result % {"status":"CRITICAL","ip":URL, "return_code":code,"c_time":con_time,"t_time":tol_time}
        sys.exit(2)
    
    elif cmp(con_time,w["cTime"]) >= 0 or cmp(tol_time,w["tTime"]) >= 0 or code not in code_rule or body_string not in body_content:
        print print_result % {"status":"WARNING","ip":URL, "return_code":code,"c_time":con_time,"t_time":tol_time} 
        sys.exit(1)

    else:
        print print_result % {"status":"OK","ip":URL,"return_code":code,"c_time":con_time,"t_time":tol_time}
        sys.exit(0)




if __name__ == '__main__':
    url = option.url
    body_string =  option.string
    
    if option.type == "http":
        return_data = http_url_req(url)
        alarm(return_code = return_data["return_code"],
            url=option.url,
            con_time = return_data["con_time"],
            tol_time = return_data["tol_time"],
            body_content = return_data["body_content"])
    elif option.type == "https":
        return_data = https_url_req(url)
        alarm(return_code = return_data["return_code"],
            url=option.url,
            con_time = return_data["con_time"],
            tol_time = return_data["tol_time"],
            body_content = return_data["body_content"])
    else:
        print "ERROR: transport protocols type error"
        parser.print_help()
        sys.exit(3)

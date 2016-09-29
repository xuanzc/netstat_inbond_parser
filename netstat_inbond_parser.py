# -*- coding:UTF-8 -*-
__author__ = 'zechun'
__created__ = '2016/9/16'
__copy_right__ = 'www.shsnc.com'

import re
import commands
import codecs
import os
import sys

reload(sys)
sys.setdefaultencoding('utf8')


def put_dict(dicts, key):
    """
    检查字典dicts中,是否存在相应的key,如果有其value+1;没有则加入字典中,其value=1
    :param dicts:传入的字典
    :param key:传入的key
    :return:null
    """
    cnt = dicts.get(key)
    if cnt:
        cnt = int(cnt)
        dicts[key] = cnt + 1
    elif key:
        dicts.setdefault(key, 1)


def build_result_dict(result_dict, server_info, ip_addr, ip_range):
    """
    根据传入的端口port,ip,ip范围,构造如下结构的字典,结果保存在result_dict中
    # result_dict = {'server_info':
    #     {'ip_range':
    #         {
    #             'ip1': count1,
    #             'ip2': count2
    #         }
    #     }
    # }
    """
    ip_range_dict = result_dict.get(server_info)
    if not ip_range_dict:
        result_dict[server_info] = {ip_range: {ip_addr: 1}}
    else:
        ip_dict = ip_range_dict.get(ip_range)
        if not ip_dict:
            ip_range_dict[ip_range] = {ip_addr: 1}
        else:
            put_dict(ip_dict, ip_addr)


def read_file(file_name='', include_str='', exclude_str='ACC,STREAM,stream'):
    """
    如果文件为空则则把当前机器的netstat -an结果
    :param file_name:
    :return:contents
    """
    contents = ''
    tag = False

    if file_name == '':
        status, contents = commands.getstatusoutput('netstat -an')
    else:

        f = open(file_name, 'r')
        line = f.readline()
        while line:
            for i in include_str.split(','):
                if line.find(i) != -1:
                    tag = True
                    for j in exclude_str.split(','):
                        if line.find(j) != -1:
                            tag = False
                    if tag == True:
                        contents = contents + str(line)
            line = f.readline()
        f.close()
    return contents


def put_listent_dict(listen_dict, contents):
    """
    将netstat -an中含LISTEN关键字的行找出来,并把监听的端口和网络协议加入字典listen_dict中
    :return:null
    """
    es = r"(\w+)" \
         r"(.+)" \
         r"(\s)" \
         r"(.+)" \
         r"(\.|\:)" \
         r"(\d+)" \
         r"(\s+)" \
         r"(.+)" \
         r"(\.|\:)" \
         r"(.+)" \
         r"(\s+)"
    for i in contents.split('\n'):
        mo = re.search(es, i)
        if mo:
            protocol = mo.group(1).replace('0      0', '').replace(' ', '')
            listen_port = mo.group(6)
            server_ip = mo.group(4)
            listen_dict.setdefault(server_ip + ',' + protocol + ',' + listen_port, listen_port)


def exist_in_listen_dict(listen_dict, server_info, server_port):
    """
    根据传入的server_info及server_port检查是否存在相应的监听
    :param listen_dict:
    :param server_info:
    :param server_port:
    :return:
    """
    server_common_ip = '*|0.0.0.0|127.0.0.1|::'
    TAG = False
    if listen_dict.get(server_info):
        TAG = True
    else:
        for i in listen_dict:
            if i.find(server_info) != -1:
                TAG = True
            for j in server_common_ip.split('|'):
                if i.find(j) != -1 and listen_dict.get(i) == server_port:
                    TAG = True
    return TAG


def get_listent_dict(listen_dict):
    contents = ""
    contents = u'监听协议及端口列表:'
    contents += u'\n服务器IP,协议,监听端口'
    for i in sorted(listen_dict):
        contents += '\n%s' % (i)
    return contents


def put_result_dict(result_dict, listen_dict, contents=read_file()):
    """分析contents中的内容,把结果保存到result_dict字典中"""
    express = r"(\w+)" \
              r"(.+)" \
              r"(\D)" \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])\." \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])\." \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])\." \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])" \
              r"(\.|\:)" \
              r"(\d+)" \
              r"(.+)" \
              r"(\D)" \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])\." \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])\." \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])\." \
              r"([01]?\d\d?|2[0-4]\d|25[0-5])" \
              r"(\.|\:)" \
              r"(\d+)" \
              r"(\s+)" \
              r"(\w+)"
    for line in contents.split('\n'):
        mo = re.search(express, line)
        if mo:
            server_ip = mo.group(4) + '.' + mo.group(5) + '.' + mo.group(6) + '.' + mo.group(7)
            protocol = mo.group(1).replace('0      0', '').replace(' ', '')
            port = mo.group(9)
            protocol_and_port = protocol + ',' + port
            ip_range = mo.group(12) + '.' + mo.group(13) + '.' + mo.group(14)
            ip_addr = ip_range + '.' + mo.group(15)
            server_info = server_ip + ',' + protocol_and_port
            if exist_in_listen_dict(listen_dict, server_info, port):
                build_result_dict(result_dict, server_info, ip_addr, ip_range)


def get_result_dict(result_dict,
                    ip_count=3):
    contents = u'\n入站IP列表(相同IP段不同IP数量<=%s):' % ip_count
    contents += u'\n服务器IP,协议,端口,客户端IP'
    for i in sorted(result_dict):
        # if i in port_list.split(','):
        # print(i + ':')
        # print(result_dict.get(i))
        for j in result_dict.get(i):
            d = result_dict.get(i).get(j)
            if len(d) <= ip_count:
                # print ('   IP段 : %s [%d]:' % (j, len(d)))
                for k in d:
                    # print(i + ',' + k)
                    contents = contents + '\n' + (i + ',' + k)
                    # print '    IP : %s [%d]' % (k, d.get(k))
    return contents


def get_result_dict_range(result_dict,
                          ip_count=3):
    contents = u'\n入站IP段列表(相同IP段不同IP数量>%s):' % ip_count
    contents += u'\n服务器IP,协议,端口,客户端IP段,IP段的不同IP数统计'
    for i in sorted(result_dict):
        for j in sorted(result_dict.get(i)):
            d = result_dict.get(i).get(j)
            if len(d) > ip_count:
                contents = contents + '\n' + ('%s,%s.0/24,%d' % (i, j, len(d)))
    return contents


def write_csv(file_name, contents):
    with open(file_name + '.csv', 'w') as f:
        t = u'' + contents
        f.write(codecs.BOM_UTF8)
        f.write('%s\n' % t.encode('utf-8'))


def process(file_name, ip_count=3):
    """
    根据
    :param file_name:
    :return:
    """
    # 结果字典表,用于存放筛选结果
    result_dict = {}

    # 监听端口字典
    listen_dict = {}

    # 不同ip出现次数<=ip_count在ip列表中出现,>ip_count则将网段结果加入白名单
    # ip_count = 3

    contents1 = read_file(file_name=file_name, include_str='LISTEN', exclude_str='ACC,STREAM,stream')
    put_listent_dict(listen_dict, contents1)

    contents = get_listent_dict(listen_dict)

    contents2 = read_file(file_name=file_name, include_str='.', exclude_str='ACC,STREAM,DGRAM,stream,*,LISTEN')
    put_result_dict(result_dict, listen_dict, contents2)
    print(result_dict)

    contents = contents + '\n' + (get_result_dict(result_dict, ip_count))
    contents = contents + '\n' + (get_result_dict_range(result_dict, ip_count))

    write_csv(file_name, contents)


def bat(dir_path, ip_count=3):
    for filename in os.listdir(r'' + dir_path):
        if filename.find('.csv') == -1 and filename.find('netstat') != -1:
            process(dir_path + '/' + filename, ip_count)


def main():
    ip_count = 3
    dir_path = ""
    argv_len = len(sys.argv)
    if argv_len <= 1:
        print (u'请输入正确的参数,像这样:')
        print (r'python %s "d:\" 3 ' % sys.argv[0])
        exit(0)
    if argv_len >= 2:
        dir_path = sys.argv[1]
    if argv_len >= 3:
        ip_count = sys.argv[2]

    bat(dir_path, ip_count)
    # process(r'D:\code\PycharmProjects\mypy\csg\netstat_test\test\test_netstat.txt')
    # bat(r'netstat_test/windows_linux(2016-9-13)')
    # bat(r'netstat_test/安全加固筛查0913')
    # bat(r'/Users/zechun/PycharmProjects/mypy/csg/netstat_test/fhqxx_0912')


main()

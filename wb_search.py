#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-07-05 11:32:49
# @Author  : worileqing (worileqing@163.com)
# @Link    : worileqing.top
# @Version : 1.0.0

import requests,re,datetime,json
from bs4 import BeautifulSoup
from wb_login2 import login, handle_slock

'''
从微博高级搜索获取的接口，目前微博高级搜索可定义的参数为：
关键词
类型
    全部
    热门
    原创
    关注人
    认证用户
    媒体
包含
    全部
    含图片
    含视频
    含音乐
    含短链
时间
    (起止时间，到小时级别)
地点
    (省市，到地级市)
时间和地点的参数为网页上面所展示的，但是具体请求的时候可不可以更为精确还没有验证
同时微博搜索url可以添加"&nodup=1",其作用是关闭微博对于搜索结果相同的过滤，查看全部的搜索结果
'''

f_url = "http://s.weibo.com/weibo/{}&typeall=1&suball=1&timescope=custom:{}:{}&page={}"
#高级搜索接口，这里只用到了关键词和起止时间

def wb_search(username,password):
    session = login(username,password)
    now_time = datetime.datetime.now()
    time_range = datetime.timedelta(hours=2)#搜索时间起止范围，这里设置的为当前时间的+-2小时
    s_time = str(now_time - time_range)[:13].replace(" ", "-")
    e_time = str(now_time + time_range)[:13].replace(" ", "-")
    page_set = 50#设置爬取的结果页，目前微博登录后只展示前50页的内容（不登录1页。。。）
    keyword = "测试"#搜索关键词
    page = 1
    while page < page_set:
        s_url = f_url.format(keyword, s_time, e_time, page)
        r_html = session.get(s_url).text
        pattern = re.compile('STK.pageletM.view\\((.*)\\)')
        scripts = re.findall(pattern, r_html)
        content = ''
        for script in scripts:
            content += json.loads(script).get('html')
        '''
        此时的content差不多就是我们看到的网页的文字内容了
        '''
        if "我真滴不是机器" in content:
            handle_slock(self.session)
        max_page = int(max(re.findall("第(\d+?)页", content)))
        # import pdb
        # pdb.set_trace()
        if max_page< page_set:
            page_set = max_page
        page += 1
        soup = BeautifulSoup(content, 'lxml')
        wb_datas = soup.findAll(attrs={"class": "WB_cardwrap S_bg2 clearfix"})
        for wb_data in wb_datas:
            wb_content = wb_data.find(attrs={'class': "comment_txt"}).text.strip()
            print("每条微博的内容："+wb_content)

if __name__ == '__main__':
    username = input("输入微博账号:")
    password = input("输入密码:")
    wb_search(username,password)

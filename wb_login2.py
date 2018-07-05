#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-06-01 10:43:31
# @Author  : worileqing (worileqing@163.com)
# @Link    : worileqing.top
# @Version : 1.0.0

import time
import base64
import rsa
import math
import random
import binascii
import requests
import re,json
from urllib.parse import quote_plus
import logging

# 构造 Request headers
agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
headers = {
    'User-Agent': agent
}

session = requests.session()

# 访问 初始页面带上 cookie
index_url = "http://weibo.com/login.php"
yundama_username = ''
yundama_password = ''



def get_pincode_url(pcid):
    size = 0
    url = "http://login.sina.com.cn/cgi/pin.php"
    pincode_url = '{}?r={}&s={}&p={}'.format(url, math.floor(random.random() * 100000000), size, pcid)
    return pincode_url


def get_img(url,path):
    resp = requests.get(url, headers=headers, stream=True)
    with open(path, 'wb') as f:
        for chunk in resp.iter_content(1000):
            f.write(chunk)


def get_su(username):
    """
    对 email 地址和手机号码 先 javascript 中 encodeURIComponent
    对应 Python 3 中的是 urllib.parse.quote_plus
    然后在 base64 加密后decode
    """
    username_quote = quote_plus(username)
    username_base64 = base64.b64encode(username_quote.encode("utf-8"))
    return username_base64.decode("utf-8")


# 预登陆获得 servertime, nonce, pubkey, rsakv
def get_server_data(su):
    pre_url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su="
    pre_url = pre_url + su + "&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.19)&_="
    prelogin_url = pre_url + str(int(time.time() * 1000))
    pre_data_res = session.get(prelogin_url, headers=headers)

    sever_data = eval(pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", ''))

    return sever_data


# 这一段用户加密密码，需要参考加密文件
def get_password(password, servertime, nonce, pubkey):
    rsaPublickey = int(pubkey, 16)
    key = rsa.PublicKey(rsaPublickey, 65537)  # 创建公钥,
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)  # 拼接明文js加密文件中得到
    message = message.encode("utf-8")
    passwd = rsa.encrypt(message, key)  # 加密
    passwd = binascii.b2a_hex(passwd)  # 将加密信息转换为16进制。
    return passwd


def login(username, password):
    # su 是加密后的用户名
    su = get_su(username)
    sever_data = get_server_data(su)
    servertime = sever_data["servertime"]
    nonce = sever_data['nonce']
    rsakv = sever_data["rsakv"]
    pubkey = sever_data["pubkey"]
    password_secret = get_password(password, servertime, nonce, pubkey)

    postdata = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'useticket': '1',
        'pagerefer': "http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl",
        'vsnf': '1',
        'su': su,
        'service': 'miniblog',
        'servertime': servertime,
        'nonce': nonce,
        'pwencode': 'rsa2',
        'rsakv': rsakv,
        'sp': password_secret,
        'sr': '1366*768',
        'encoding': 'UTF-8',
        'prelt': '115',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META'
        }

    need_pin = sever_data['showpin']
    if need_pin == 1:
        # 你也可以改为手动填写验证码
        # if not yundama_username:
        #     raise Exception('由于本次登录需要验证码，请配置顶部位置云打码的用户名{}和及相关密码'.format(yundama_username))
        pcid = sever_data['pcid']
        postdata['pcid'] = pcid
        img_url = get_pincode_url(pcid)
        verify_code_path = './pincode.png'
        get_img(img_url,verify_code_path)
        verify_code = input('验证码')
        # verify_code = get_code(verify_code_path)
        postdata['door'] = verify_code

    login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
    login_page = session.post(login_url, data=postdata, headers=headers)
    login_loop = (login_page.content.decode("GBK"))


    if 'retcode=101' in login_loop:
        logging.error('invalid password for {}, please ensure your account and password'.format(name))
        # LoginInfoOper.freeze_account(name, 2)
        return ''

    if 'retcode=2070' in login_loop:
        logging.error('invalid verification code')
        return 'pinerror'

    if 'retcode=4049' in login_loop:
        logging.warning('account {} need verification for login'.format(name))
        return 'login_need_pincode'

    if '正在登录' in login_loop or 'Signing in' in login_loop:




        pa = r'location\.replace\([\'"](.*?)[\'"]\)'
        loop_url = re.findall(pa, login_loop)[0]
        login_index = session.get(loop_url, headers=headers)
        uuid = login_index.text
        uuid_pa = r'"uniqueid":"(.*?)"'
        uuid_res = re.findall(uuid_pa, uuid, re.S)[0]
        web_weibo_url = "http://weibo.com/%s/profile?topnav=1&wvr=6&is_all=1" % uuid_res
        weibo_page = session.get(web_weibo_url, headers=headers)
        weibo_pa = r'<title>(.*?)</title>'
        user_name = re.findall(weibo_pa, weibo_page.content.decode("utf-8", 'ignore'), re.S)[0]
        logging.info('登陆成功，你的用户名为：'+user_name)
        # cookies = requests.utils.dict_from_cookiejar(session.cookies)
        return session


def handle_slock(session):
    url = "https://s.weibo.com/"
    code = str(int((time.time()*10000)))
    get_rcode = "https://s.weibo.com/ajax/pincode/pin?type=sass{}".format(code)
    response = session.request("GET", get_rcode)
    with open("code.png", "wb") as f:
        f.write(response.content)
    # code = get_code("code.png")
    code = input("打开code.png,输入验证码")

    url = "https://s.weibo.com/ajax/pincode/verified"

    querystring = {"__rnd": "{}".format(int(time.time()*1000))}

    payload = "secode={}&type=sass&pageid=weibo&_t=0".format(code)
    headers = {
        'host': "s.weibo.com",
        'connection': "keep-alive",
        'origin': "https://s.weibo.com",
        'x-requested-with': "XMLHttpRequest",
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/66.0.3359.181 Chrome/66.0.3359.181 Safari/537.36",
        'content-type': "application/x-www-form-urlencoded",
        'accept': "*/*",
        'dnt': "1",
        'referer': "http://s.weibo.com",
        'accept-encoding': "gzip, deflate, br",
        'accept-language': "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        'cache-control': "no-cache",
    }
    response = session.request(
        "POST", url, data=payload, headers=headers, params=querystring)
    if "100000" in response.text:
        return True
    else:
        return False

if __name__ == "__main__":
    username = input('微博用户名：')
    password = input('微博密码：')
    login(username, password)

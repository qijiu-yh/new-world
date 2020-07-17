# -*- coding: utf-8 -*-
#!../env/Scripts/python
import configparser
import logging
import urllib
import os
import sys, getopt
from selenium import webdriver
from urllib import quote
from concurrent.futures import ThreadPoolExecutor
import Queue
import re
import chardet

# que = Queue.LifoQueue()
que = Queue.Queue()
logging.basicConfig(filename='./log/'+"log"+'.log', format='[%(asctime)s-%(filename)s-%(levelname)s:%(message)s]', level=logging.ERROR, filemode='a', datefmt='%Y-%m-%d %I:%M:%S %p')
options = {}
pool = None
config_file = ""


def get_config():
    """获取配置信息"""
    #  实例化configParser对象
    config = configparser.ConfigParser()
    config.read('spider.conf', encoding='GBK')
    # -get(section,option)得到section中option的值，返回为string类型
    options["spider"] = {}
    options["spider"]["url_list_file"] = config.get('spider', 'url_list_file')
    options["spider"]["output_directory"] = config.get('spider', 'output_directory')
    options["spider"]["max_depth"] = config.getint('spider', 'max_depth')
    options["spider"]["crawl_interval"] = config.getint('spider', 'crawl_interval')
    options["spider"]["crawl_timeout"] = config.getint('spider', 'crawl_timeout')
    options["spider"]["target_url"] = config.get('spider', 'target_url')
    options["spider"]["thread_count"] = config.getint('spider', 'thread_count')

    print options
    return options


def get_url():
    url_path = options["spider"]["url_list_file"]
    with open(url_path) as fp:
        url = fp.readline()
        que.put((url, 1))
    # url, num = queue.get()
    while True:
        if not que.empty():
            url, num = que.get()
            # pool.submit(crawl_web_page, url, num)
            crawl_web_page(url, num)


def crawl_web_page(url1, num):
    urls = []
    try:
        print "url:", url1, " num: ",num
        if num > options.get("spider", 0).get("max_depth", 0):
            return
        re_str = options.get("spider", "").get("target_url", "")
        # pattern = re.compile(r'http[s]?://(.*?)\?')
        pattern = re.compile(re_str)
        path = pattern.search(url1)
        # if not path:
        #     return

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome("chromedriver.exe", chrome_options=chrome_options)
        driver.implicitly_wait(10)  # seconds
        driver.set_page_load_timeout(10)
        try:
            driver.get(url1)  # 普通情况下，设置的 超时加载时间远远小于实际网页加载完成需要的时间，所以肯定会报错
        except:
            print 111
            driver.execute_script('window.stop()')  # 执行Javascript来停止页面加载 window.stop()
            return

        driver.get(url1)
        save_html(url1)
        a_urls = driver.find_elements_by_xpath("//a")  # 匹配出所有a元素里的链接

        for item in a_urls:
            url = item.get_attribute("href")
            print url
            if url == 'None':  # 很多的a元素没有链接，所有是None
                continue
            try:
                response = urllib2.urlopen(url, timeout=60)  # 可以通过urllib测试url地址是否能打开
            except Exception as e:
                logging.error('Error url info: %s', e, exc_info=1)   # 把测试不通过的url显示出来
            else:
                urls.append(url)
                que.put((url, num+1))
        driver.close()
    except Exception as e:
        logging.error('Error : %s', e, exc_info=1)  # 把测试不通过的url显示出来
    return urls


def save_html(url):
    #    注意windows文件命名的禁用符，比如 /
    print "url: ",url
    file_content = urllib.urlopen(url).read()
    chardit1 = chardet.detect(file_content)
    if chardit1['encoding'] == "utf-8" or chardit1['encoding'] == "UTF-8":
        print "UTF-8"
    elif chardit1['encoding'] == "gbk" or chardit1['encoding'] == "GBK":
        file_content = file_content.decode('gbk')
        print "GBK"
    file_name = quote(url, "")
    # file_name = file_name.replace('/', '\/')
    filedir = os.path.expanduser(options.get("spider", 0).get("output_directory", 0))
    filepath = os.path.join(filedir, file_name)
    filepath = filepath + ".html"
    with open(filepath, "wb+") as f:
        #   写文件用bytes而不是str，所以要转码
        f.write(file_content)


def get_argv(argv):
   try:
      opts, args = getopt.getopt(argv, "hvc:", ["conf="])
   except getopt.GetoptError:
      print 'test.py -c <spider.conf>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'test.py -c <spider.conf>'
         sys.exit()
      elif opt == '-v':
         print 'spider version 1.0'
         sys.exit()
      elif opt in ("-c"):
          global config_file
          config_file = arg


if __name__ == '__main__':
    get_argv(sys.argv[1:])
    get_config()
    pool = ThreadPoolExecutor(options["spider"]["thread_count"])
    get_url()





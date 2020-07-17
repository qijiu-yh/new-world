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


class spider_url:
    def __init__(self):
        que = Queue.LifoQueue()
        logging.basicConfig(filename='./log/' + "log" + '.log',
                            format='[%(asctime)s-%(filename)s-%(levelname)s:%(message)s]', level=logging.ERROR,
                            filemode='a', datefmt='%Y-%m-%d %I:%M:%S %p')
        options = {}
        pool = None
        config_file = ""

    @staticmethod
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

    @staticmethod
    def get_url():
        with open('urls.txt') as fp:
            url = fp.readline()
            que.put((url, 1))
        # url, num = queue.get()
        while True:
            if not que.empty():
                url, num = que.get()
                # pool.submit(crawl_web_page, url, num)
                crawl_web_page(url, num)
            else:
                break

    @staticmethod
    def crawl_web_page(url1, num):
        print "url:", url1, " num: ",num
        if num > options.get("spider", 0).get("max_depth", 0):
            print "break"
            return
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome("chromedriver.exe", chrome_options=chrome_options)
        driver.implicitly_wait(10)  # seconds

        driver.get(url1)
        save_html(url1)
        a_urls = driver.find_elements_by_xpath("//a")  # 匹配出所有a元素里的链接
        urls = []
        for item in a_urls:
            url = item.get_attribute("href")
            if url == 'None':  # 很多的a元素没有链接，所有是None
                continue
            try:
                response = urllib.urlopen(url)  # 可以通过urllib测试url地址是否能打开
            except:
                logging.error('Error url:   ' + url)   # 把测试不通过的url显示出来
            else:
                urls.append(url)
                que.put((url, num+1))
        driver.close()
        return urls

    @staticmethod
    def save_html(url):
        #    注意windows文件命名的禁用符，比如 /
        print "url: ",url
        file_content = urllib.urlopen(url).read()
        file_name = quote(url, "")
        # file_name = file_name.replace('/', '\/')
        filedir = os.path.expanduser(options.get("spider", 0).get("output_directory", 0))
        filepath = os.path.join(filedir, file_name)
        filepath = filepath + ".html"
        with open(filepath, "wb+") as f:
            #   写文件用bytes而不是str，所以要转码
            f.write(file_content)

    @staticmethod
    def get_argv(argv):
       try:
          opts, args = getopt.getopt(argv, "hc:", ["conf="])
       except getopt.GetoptError:
          print 'test.py -c <spider.conf>'
          sys.exit(2)
       for opt, arg in opts:
          if opt == '-h':
             print 'test.py -c <spider.conf>'
             sys.exit()
          elif opt in ("-c"):
              global config_file
              config_file = arg
              print "def config_file", config_file


if __name__ == '__main__':
    get_argv(sys.argv[1:])
    print "config_file", config_file

    # get_config()
    # pool = ThreadPoolExecutor(options["spider"]["thread_count"])
    # get_url()





# -*- coding: utf-8 -*-
#!../env/Scripts/python
import configparser
import logging
import urllib.request
import os
import sys, getopt
from selenium import webdriver
from urllib import parse
from concurrent.futures import ThreadPoolExecutor
import queue
import re
import chardet

que = queue.Queue()
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

    print (options)
    return options


def get_url():
    url_path = options["spider"]["url_list_file"]
    with open(url_path) as fp:
        # url = fp.readline()
        while True:
            url = fp.readline()
            if url:
                que.put((url, 1))
            else:
                break

    # url, num = queue.get()
    while True:
        if not que.empty():
            url, num = que.get()
            pool.submit(crawl_web_page, url, num)
            # crawl_web_page(url, num)
        # else:
        #     break


def crawl_web_page(url1, num):
    urls = []
    try:
        save_html(url1)

        if num + 1 > options.get("spider", 0).get("max_depth", 0):
            return

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome("chromedriver.exe", options=chrome_options)
        driver.implicitly_wait(10)  # seconds
        driver.set_page_load_timeout(10)
        try:
            driver.get(url1)
        except:
            print(1111)
            driver.execute_script('window.stop()')
            return

        a_urls = driver.find_elements_by_xpath("//a")  # 匹配出所有a元素里的链接

        re_str = options.get("spider", "").get("target_url", "")
        # pattern = re.compile(r'http[s]?://(.*?)\?')
        pattern = re.compile(re_str)

        for item in a_urls:
            url = item.get_attribute("href")
            if url == 'None':  # 很多的a元素没有链接，所有是None
                continue
            try:
                response = urllib.request.urlopen(url, timeout=10)  # 可以通过urllib测试url地址是否能打开
            except Exception as e:
                logging.error('Error url info: %s', e, exc_info=1)   # 把测试不通过的url显示出来
            else:
                path = pattern.search(url1)
                # if not path:
                #     continue
                urls.append(url)
                print("url add:", url, " num: ", num + 1)
                que.put((url, num+1))
        driver.close()
    except Exception as e:
        logging.error('Error : %s', e, exc_info=1)  # 把测试不通过的url显示出来

    return urls


def save_html(url):
    #    注意windows文件命名的禁用符，比如 /
    print ("url save : ",url)
    file_content = urllib.request.urlopen(url).read()
    chardit1 = chardet.detect(file_content)
    if chardit1['encoding'] == "utf-8" or chardit1['encoding'] == "UTF-8":
        print ("UTF-8")
    elif chardit1['encoding'] == "gbk" or chardit1['encoding'] == "GBK":
        file_content = file_content.decode('gbk')
        print ("GBK")
    file_name = parse.quote(url, "")
    # file_name = file_name.replace('/', '\/')
    filedir = os.path.expanduser(options.get("spider", 0).get("output_directory", 0))
    # filepath = os.path.join(filedir, file_name)
    filepath = filedir+ "/" + file_name
    filepath = filepath + ".html"
    with open(filepath, "wb+") as f:
        #   写文件用bytes而不是str，所以要转码
        f.write(file_content)


def get_argv(argv):
   try:
      opts, args = getopt.getopt(argv, "hvc:", ["conf="])
   except getopt.GetoptError:
      print ('test.py -c <spider.conf>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print ('test.py -c <spider.conf>')
         sys.exit()
      elif opt == '-v':
         print ('spider version 1.0')
         sys.exit()
      elif opt in ("-c"):
          global config_file
          config_file = arg


if __name__ == '__main__':
    get_argv(sys.argv[1:])
    get_config()
    pool = ThreadPoolExecutor(options["spider"]["thread_count"])
    get_url()





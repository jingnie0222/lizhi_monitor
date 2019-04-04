#!/usr/bin/python3
# -*-codig=utf8-*-

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import quote



def get_sogou_screenshot(query, pic_dir):
    try:
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        url = "http://wap.sogou.com.inner/web/searchList.jsp?keyword=" + quote(query)
        driver.get(url)
        driver.save_screenshot("./" + pic_dir + "/" + query + "_sogou.png")
        driver.close()
    except Exception as err:
        driver.close()
        print("[get_sogou_screenshot]:%s" % err)


def get_baidu_screenshot(query, pic_dir):
    try:
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        url = "https://wap.baidu.com/s?word=" + quote(query)
        driver.get(url)
        driver.save_screenshot("./" + pic_dir + "/" + query + "_baidu.png")
        driver.close()
    except Exception as err:
        driver.close()
        print("[get_baidu_screenshot]:%s" % err)


if __name__ == "__main__":
    get_sogou_screenshot("喜马拉雅", "")
    get_baidu_screenshot("喜马拉雅", "")
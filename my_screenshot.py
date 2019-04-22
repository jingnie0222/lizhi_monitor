#!/usr/bin/python3
# -*-codig=utf8-*-

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import quote
from PIL import Image
import os


def get_sogou_screenshot(query, pic_dir):
    try:
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        url = "http://wap.sogou.com.inner/web/searchList.jsp?keyword=" + quote(query)
        driver.get(url)
        driver.save_screenshot(pic_dir + "/" + query + "_sogou.png")
        driver.close()
        driver.quit()
    except Exception as err:
        driver.close()
        driver.quit()
        print("[get_sogou_screenshot]:%s" % err)


def get_baidu_screenshot(query, pic_dir):
    try:
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        url = "https://wap.baidu.com/s?word=" + quote(query)
        driver.get(url)
        driver.save_screenshot(pic_dir + "/" + query + "_baidu.png")
        driver.close()
        driver.quit()
    except Exception as err:
        driver.close()
        driver.quit()
        print("[get_baidu_screenshot]:%s" % err)


def get_sogou_first_screenshot(query, pic_dir):
    try:
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        url= "http://wap.sogou.com.inner/web/searchList.jsp?keyword=" + quote(query)
        driver.get(url)

        #截取整张图片
        driver.save_screenshot(pic_dir + "/" + query + "_sogou_total.png")

        #根据css定位要截取的图片，计算其大小和位置，然后在整张图片中进行截取
        target = driver.find_element_by_css_selector("div[data-v=\"101\"]")
        if target:
            left = target.location['x']
            top = target.location['y']
            right = target.location['x'] + target.size['width']
            bottom = target.location['y'] + target.size['height']

            im = Image.open('temp.png')
            im = im.crop((left, top, right, bottom))
            im.save(pic_dir + "/" + query + "_sogou.png")
        #截取完成后，删除整张截图
        if os.path.exists(pic_dir + "/" + query + "_sogou_total.png"):
            os.remove(pic_dir + "/" + query + "_sogou_total.png")

        driver.close()
        driver.quit()

    except Exception as err:
        driver.close()
        driver.quit()
        print("[get_sogou_first_screenshot] word:%s\t err:%s" % (query, err))


def get_baidu_first_screenshot(query, pic_dir):
    try:
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        #dcap['phantomjs.page.settings.userAgent'] = ('Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1')
        #url = "https://wap.baidu.com/s?word=" + quote(query)
        url= "http://snapshot.sogou/agent/wget.php?engine=wap_baidu&query=" + quote(query)
        driver.get(url)
        driver.save_screenshot(pic_dir + "/" + query + "_baidu_total.png")

        target = driver.find_element_by_css_selector("div[order=\"1\"]")
        if target:
            left = target.location['x']
            top = target.location['y']
            #截图百度截图右侧最后一个字符截不全的问题，增加15个像素点
            right = target.location['x'] + target.size['width'] + 20
            bottom = target.location['y'] + target.size['height']

            im = Image.open(pic_dir + "/" + query + "_baidu_total.png")
            im = im.crop((left, top, right, bottom))
            im.save(pic_dir + "/" + query + "_baidu.png")

        if os.path.exists(pic_dir + "/" + query + "_baidu_total.png"):
            os.remove(pic_dir + "/" + query + "_baidu_total.png")


        driver.close()
        driver.quit()

    except Exception as err:
        driver.close()
        driver.quit()
        print("[get_baidu_first_screenshot] word:%s\t err:%s" % (query, err))


if __name__ == "__main__":
    #get_sogou_screenshot("喜马拉雅", "")
    #get_baidu_screenshot("喜马拉雅", "")
    get_baidu_first_screenshot("华为wps连接怎么设置", "")
    #get_sogou_first_screenshot("张作霖的子女", "")


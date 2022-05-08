# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 09:23:51 2020

@author: Lyonel
"""

from selenium import webdriver
import time
import pandas as pd
import re
import requests
from utils.config import CHROME_DRIVER

def getDriver():
    # chrome_driver = r"C:\Users\liuyi\Anaconda3\Lib\site-packages\selenium\webdriver\chrome\chromedriver.exe"
    chrome_driver = CHROME_DRIVER
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-infobars')
    driver = webdriver.Chrome(options=options, executable_path=chrome_driver)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": {"User-Agent": "browserClientA"}})
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
    })
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
        "platform": "Windows"})
    return driver

def get_info_page(page):
    url = f'http://www.ocoal.com/article/Index/index/id-4/page-{page}'
    driver = getDriver()
    driver.get(url)
    # new_url = driver.find_element_by_css_selector('li a').get_attribute('href')
    text_l = pd.Series(
        [i.text for i in driver.find_elements_by_xpath("//div[@class='infolist-main bidlist']//ul//li//a")])
    new_url = pd.Series([i.get_attribute('href') for i in
                         driver.find_elements_by_xpath("//div[@class='infolist-main bidlist']//ul//li//a")])
    # new_url = pd.Series([i.text for i in driver.find_elements_by_xpath("//li//a//em")])
    # new_url = [i for i in new_url if 'mp.weixin' in i]
    date_l = text_l.apply(lambda x: x.split('\n')[1])
    driver.quit()
    df = pd.concat([date_l, text_l, new_url],axis=1)
    return df

def get_data_from_wxpage(wx_url, date):
    df_raw = pd.read_html(wx_url, encoding='utf-8')
    df_raw_ = [df_raw[i][df_raw[i]=='全国统调电厂'].dropna(how='all',axis=0) for i in range(len(df_raw))]
    df_num = [i for i in range(len(df_raw_)) if len(df_raw_[i])>0][0]
    df = df_raw[df_num]
    df.columns = df.iloc[7, :]
    df_ = df.set_index('电厂类型').loc[['全国统调电厂', '全国重点电厂', '南方八省电厂', '样本区域电厂'], '日耗']
    df_ = df_.apply(lambda x: [float(i) for i in re.findall("(.*?)万吨", x)][0])
    df_.name = date
    return df_

def jump_to_wxlink(url):
    driver = getDriver()
    driver.get(url)
    try:
        nurl = driver.find_element_by_id('js_access_msg').get_attribute('href')
    except:
        nurl = None
    driver.quit()
    return nurl

def get_wxlink(url):
    driver = getDriver()
    driver.get(url)
    nurll = driver.find_elements_by_xpath('//div[@class="s_nr"]//a')[0].get_attribute('href')
    driver.quit()
    return nurll

def get_all_page(pagenum):
    l = []
    for page in range(1, pagenum+1):
        print(f"page-{page}")
        outdf = get_info_page(page=page)
        l.append(outdf)
    df = pd.concat(l)
    return df

def get_data(info_df, data_df):
    if data_df == None:
        data_df = pd.DataFrame(columns=['全国统调电厂', '全国重点电厂', '南方八省电厂', '样本区域电厂'])
    l = []
    for i,x in info_df.iterrows():
        if x.date in data_df.index:
            print(f"{x.date}_get")
        else:
            print(f"{x.date}_loading")
            if "www.ocoal.com" in x.url:
                fake_wx_url = get_wxlink(x.url)
                wx_url = jump_to_wxlink(fake_wx_url)
                if wx_url == None:
                    data = pd.Series(index=['全国统调电厂', '全国重点电厂', '南方八省电厂', '样本区域电厂'], data=None)
                    data.name = x.date
                else:
                    data = get_data_from_wxpage(wx_url, x.date)
            else:
                try:
                    data = get_data_from_wxpage(x.url, x.date)
                except:
                    wx_url = jump_to_wxlink(x.url)
                    if wx_url == None:
                        data = pd.Series(index=['全国统调电厂', '全国重点电厂', '南方八省电厂', '样本区域电厂'], data=None)
                        data.name = x.date
                    else:
                        data = get_data_from_wxpage(wx_url, x.date)
                        
            l.append(data)
    outdf = pd.concat(l, axis=1).T
    data_df = pd.concat([data_df, outdf])
    data_df.to_excel("E:\\煤炭爬虫\\日数据.xlsx")
# info_df = get_all_page(40)
# info_df = pd.read_excel("E:\\煤炭爬虫\\info.xlsx", index_col=0)
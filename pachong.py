# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 09:23:51 2020

@author: Lyonel
"""

from selenium import webdriver
import time
import pandas as pd
import re


def getDriver():
    chrome_driver = r"C:\Users\liuyi\Anaconda3\Lib\site-packages\selenium\webdriver\chrome\chromedriver.exe"
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


def get_data_gysy(source='WJW', thre=17):
    if source=='WJW':
        url = 'http://www.nhc.gov.cn/xcs/yqtb/list_gzbd.shtml'
        driver = getDriver()
        driver.get(url)
        time.sleep(5)
        # new_url = driver.find_element_by_css_selector('li a').get_attribute('href')
        new_url = [i.get_attribute('href') for i in driver.find_elements_by_xpath("//li//a")]
        newsl = []
        datel = []
        for nu in new_url[:thre]:
            driver.get(nu)
            time.sleep(3)
            news_ = driver.find_element_by_id('xw_box').text
            date = re.findall(f"(.*?)月(.*?)日", news_)[0]
            date = f"2022-{date[0]}-{date[1]}"
            newsl.append(news_)
            datel.append(date)
        driver.quit()
        news = pd.DataFrame({'date':datel, 'news':newsl}, index=range(len(datel)))
        news.date = pd.to_datetime(news.date)
    else:
        url = source
        driver = getDriver()
        driver.get(url)

        news = driver.find_element_by_class_name('rich_media_inner').text
        driver.quit()
    return news


# x = txt_data.正文.iloc[24]
# x = txt_data.正文.iloc[5]

def txt_split(x, location):
    dfl = []
    reget = x.split('截至')
    reqz = reget[0].split('本土')[1]
    rewzz = reget[1].split('无症状感染者')[1]
    resh_qz = re.findall(f"上海(.*?)；", reqz)
    resh_wzz = re.findall(f"上海(.*?)；", rewzz)

    for l in location:
        if len(resh_qz) > 0:
            if '在' not in resh_qz[0]:
                reout1 = re.findall(f"{l}(.*?)例", resh_qz[0])
            else:
                reout1 = re.findall(f"(.*?)例，在{l}", resh_qz[0])
            if len(reout1) == 0:
                reout1 = [0]
        else:
            reout1 = [0]

        if len(resh_wzz) > 0:
            if '在' not in resh_wzz[0]:
                reout2 = re.findall(f"{l}(.*?)例", resh_wzz[0])
            else:
                reout2 = re.findall(f"(.*?)例，在{l}", resh_wzz[0])
            if len(reout2) == 0:
                reout2 = [0]
        else:
            reout2 = [0]

        date = re.findall(f"(.*?)月(.*?)日", reget[0])[0]
        date = f"2022-{date[0]}-{date[1]}"

        reout_df = pd.DataFrame(
            {'日期': pd.to_datetime(date), '行政区': l, '新增确诊': int(reout1[0]), '新增无症状感染': int(reout2[0])}, index=[0])
        dfl.append(reout_df)
    outdf = pd.concat(dfl).reset_index(drop=True)
    return outdf

def txt_split_china(x, location):
    x_ = x.split('\r')
    if len(x_) == 1:
        x_ = x.split('\n')
    xzqzr = [i for i in x_ if '新增确诊病例' in i][0]
    xzwzzr = [i for i in x_ if '新增无症状感染者' in i][0]
    # btbl = re.findall(f"病例(.*?)，居住于{l}", x1)
    # reout1 = [re.findall(r"\d+\.?\d*", i) for i in reout1]
    lo_qz = re.findall(f"本土病例(.*?)。", xzqzr)[0].split('无症状感染者转为确诊病例')
    dfl = []
    for l in location:
        try:
            city_qz = int(re.findall(f"{l}(.*?)例", lo_qz[0])[0])
        except:
            city_qz = 0
        try:
            city_zg = int(re.findall(f"{l}(.*?)例", lo_qz[1])[0])
        except:
            city_zg = 0
        try:
            city_wzz = int(re.findall(f"{l}(.*?)例", xzwzzr)[0])
        except:
            city_wzz = 0
        reout_df = pd.DataFrame(
            {'地区': l, '新增确诊': city_qz, '无症状转归':city_zg,'新增无症状感染': city_wzz}, index=[0])
        dfl.append(reout_df)
    outdf = pd.concat(dfl).reset_index(drop=True)
    return outdf

def txt_split_wx(x, location):
    dfl = []
    x0 = x.split('本土病例情况')[0].split('新增境外输入性新冠肺炎确诊病例')[0]
    x0_ = x.split('本土病例情况')[1]
    x1 = x0_.split('本土无症状感染者情况')[0]
    x1 = x1.split('在风险人群筛查中发现新冠病毒核酸检测结果异常，即被隔离管控。经疾控中心复核结果为阳性。经市级专家会诊，综合流行病学史、临床症状、实验室检测和影像学检查结果等，诊断为确诊病例。')[0]
    x2 = x0_.split('本土无症状感染者情况')[1].split('境外输入病例情况')[0]
    date = re.findall(f"2022年(.*?)月(.*?)日", x0)[0]
    date = f"2022-{date[0]}-{date[1]}"

    def _cal(i):
        if len(i) == 2:
            f = (int(i[1]) - int(i[0]) + 1)
        else:
            f = 1
        return f

    for l in location:
        reout1 = re.findall(f"病例(.*?)，居住于{l}", x1)
        reout1 = [re.findall(r"\d+\.?\d*", i) for i in reout1]
        reout1 = sum([_cal(i) for i in reout1])

        reout2 = re.findall(f"无症状感染者(.*?)，居住于{l}", x2)
        reout2 = [re.findall(r"\d+\.?\d*", i) for i in reout2]
        reout2 = sum([_cal(i) for i in reout2])

        reout_df = pd.DataFrame(
            {'日期': pd.to_datetime(date), '行政区': l, '新增确诊': int(reout1), '新增无症状感染': int(reout2)}, index=[0])
        dfl.append(reout_df)
    outdf = pd.concat(dfl).reset_index(drop=True)

    try:
        if '无新增本土新冠肺炎确诊病例' not in x0:
            qzall = [int(i) for i in re.findall(f"新增本土新冠肺炎确诊病例(\d+\.?\d*)例", x0) + re.findall(f"新增(\d+\.?\d*)例本土新冠肺炎确诊病例", x0) + re.findall(f"新增本土新冠肺炎确诊病例(\d+\.?\d*)", x0)][0]
            wzzall = [int(i) for i in re.findall(f"和无症状感染者(\d+\.?\d*)例", x0)+re.findall(f"新增(\d+\.?\d*)例本土无症状感染者", x0)][0]
            try:
                zgall = [int(i) for i in re.findall(f"含既往无症状感染者转为确诊病例(\d+\.?\d*)例", x0)+re.findall(f"其中(\d+\.?\d*)例确诊病例为此前无症状感染者转归", x0)+re.findall(f"其中(\d+\.?\d*)例确诊病例为既往无症状感染者转归", x0)][0]
            except:
                zgall = 0
        else:
            qzall = 0
            wzzall = \
            [int(i) for i in re.findall(f"和无症状感染者(\d+\.?\d*)例", x0) + re.findall(f"新增(\d+\.?\d*)例本土无症状感染者", x0)][0]
            zgall = 0

        if ('其余在隔离管控中发现' not in x0) and ('其余隔离管控中发现' not in x0):
            if ('均在隔离管控中发现' not in x0) and ('其余在相关风险人群排查中发现' not in x0):
                regk = re.findall(f"其中(.*?)在隔离管控中发现", x0)
                regknqz = sum([int(i) for i in re.findall(f"(\d+\.?\d*)例确诊病例和", regk[0])])
                regknwzz = [int(i) for i in re.findall(f"和(\d+\.?\d*)例无症状感染者", regk[0])][0]

                regkwqz = qzall - zgall - regknqz
                regkwwzz = wzzall - regknwzz
            elif '其余在相关风险人群排查中发现' in x0:
                regk = re.findall(f"例，(.*?)例确诊病例和(.*?)例无症状感染者在隔离管控中发现", x0)[0]
                regknqz = int(regk[0])
                regknwzz = int(regk[1])

                regkwqz = qzall - zgall - regknqz
                regkwwzz = wzzall - regknwzz
            else:
                print(x)
                regknqz = input('请输入管控内确诊')
                regknwzz = input('请输入管控内无症状')
                # regknqz = qzall
                # regknwzz = wzzall

                regkwqz = input('请输入管控外确诊')
                regkwwzz = input('请输入管控外无症状')
        else:
            regk = re.findall(f"(.*?)在相关风险人群排查中发现", x0)
            if len(regk)>0:
                regkwqz = sum([re.findall(f"(\d+\.?\d*)例确诊病例", regk[0])+re.findall(f"(\d+\.?\d*)例病例因症就诊发现", regk[0])])
                regkwwzz = [int(i) for i in re.findall(f"(\d+\.?\d*)例无症状感染者", regk[0])][0]
            else:
                regkwqz = sum([int(i) for i in
                               re.findall(f"(\d+\.?\d*)例确诊病例为此前无症状感染者转归", x0) + re.findall(f"(\d+\.?\d*)例确诊病例",
                                                                                                x0) + re.findall(
                                   f"(\d+\.?\d*)例病例因症就诊发现", x0) + re.findall(
                                   f"(\d+\.?\d*)例在例行筛查中发现", x0)])
                try:
                    regkwwzz = [int(i) for i in re.findall(f"(\d+\.?\d*)例无症状感染者", x0)][0]
                except:
                    regkwwzz = 0

            regknqz = qzall - regkwqz
            regknwzz = wzzall - regkwwzz
        outdf2 = pd.DataFrame(
                {'日期': pd.to_datetime(date), '管控内新增确诊':regknqz, '管控内新增无症状':regknwzz, '管控外新增确诊':regkwqz, '管控外新增无症状':regkwwzz, '文本':x0}, index=[0])
    except:
        print(x)
        regknqz = input('gknqz')
        regknwzz = input('gknwzz')
        regkwqz = input('gkwqz')
        regkwwzz = input('gkwwzz')
        outdf2 = pd.DataFrame({'日期': pd.to_datetime(date), '管控内新增确诊':regknqz, '管控内新增无症状':regknwzz, '管控外新增确诊':regkwqz, '管控外新增无症状':regkwwzz, '文本':x0}, index=[0])
    return outdf, outdf2

def txt_split_wx_new(x):
    x0 = x.split('本土病例情况')[0].split('新增境外输入性新冠肺炎确诊病例')[0]
    x0_ = x.split('本土病例情况')[1]
    x1 = x0_.split('本土无症状感染者情况')[0]
    date = re.findall(f"2022年(.*?)月(.*?)日", x0)[0]
    date = f"2022-{date[0]}-{date[1]}"

    try:
        xzzy = [int(i) for i in re.findall(f"新增治愈出院(\d+\.?\d*)例", x1)][0]
        jcyxgc = [int(i) for i in re.findall(f"解除医学观察无症状感染者(\d+\.?\d*)例", x) + re.findall(f"解除医学观察本土无症状感染者(\d+\.?\d*)例", x)][0]
        try:
            jwjc = [int(i) for i in re.findall(f"例，境外输入性无症状感染者(\d+\.?\d*)例", x)][0]
        except:
            jwjc = 0
        mrcy = xzzy + jcyxgc - jwjc
        outdf3 = pd.DataFrame(
                {'日期': date, '每日出院':mrcy}, index=[0])
    except:
        print(x)
        d2 = input('每日出院')
        outdf3 = pd.DataFrame(
            {'日期': date, '每日出院': d2}, index=[0])
    return outdf3

def txt_split_gq(x, location):
    dfl = []
    x0 = x.split('本土病例情况')[0].split('新增境外输入性新冠肺炎确诊病例')[0]
    x0_ = x.split('本土病例情况')[1]
    x1 = x0_.split('本土无症状感染者情况')[0]
    x2 = x0_.split('本土无症状感染者情况')[1].split('境外输入病例情况')[0]
    date = re.findall(f"2022年(.*?)月(.*?)日", x0)[0]
    date = f"2022-{date[0]}-{date[1]}"

    if '在风险人群筛查中发现新冠病毒核酸检测结果异常，即被隔离管控。经疾控中心复核结果为阳性。经市级专家会诊，综合流行病学史、临床症状、实验室检测和影像学检查结果等，诊断为确诊病例。' in x1:
        x1_ = x1.split('在风险人群筛查中发现新冠病毒核酸检测结果异常，即被隔离管控。经疾控中心复核结果为阳性。经市级专家会诊，综合流行病学史、临床症状、实验室检测和影像学检查结果等，诊断为确诊病例。')
        x1 = x1_[0].split('均为本市闭环隔离管控人员，其间新冠病毒核酸检测结果异常，经疾控中心复核结果为阳性。经市级专家会诊，综合流行病学史、临床症状、实验室检测和影像学检查结果等，诊断为确诊病例。')[1]
    else:
        x1 = ''

    if '在风险人群筛查中发现新冠病毒核酸检测结果异常，即被隔离管控。经疾控中心复核结果为阳性，诊断为无症状感染者。' in x2:
        x2 = x2.split('均为本市闭环隔离管控人员，其间新冠病毒核酸检测结果异常，经疾控中心复核结果为阳性，诊断为无症状感染者。')[1]
    else:
        x2 = ''

    def _cal(i):
        if len(i) == 2:
            f = (int(i[1]) - int(i[0]) + 1)
        else:
            f = 1
        return f

    for l in location:
        reout1 = re.findall(f"病例(.*?)，居住于{l}", x1)
        reout1 = [re.findall(r"\d+\.?\d*", i) for i in reout1]
        reout1 = sum([_cal(i) for i in reout1])

        reout2 = re.findall(f"无症状感染者(.*?)，居住于{l}", x2)
        reout2 = [re.findall(r"\d+\.?\d*", i) for i in reout2]
        reout2 = sum([_cal(i) for i in reout2])

        reout_df = pd.DataFrame(
            {'日期': pd.to_datetime(date), '行政区': l, '新增控外阳性': int(reout1)+int(reout2)}, index=[0])
        dfl.append(reout_df)
    outdf = pd.concat(dfl).reset_index(drop=True)
    return outdf

def get_gkline(source="WJW"):
    txt_data = pd.read_excel(r'E:\国家卫健委-疫情防控动态.xlsx')
    location = ['浦东新区', '闵行区', '徐汇区', '嘉定区', '松江区', '黄浦区', '宝山区', '静安区', '普陀区', '崇明区', '奉贤区', '杨浦区', '虹口区', '长宁区',
                '青浦区', '金山区']
    try:
        df_old = pd.read_excel('E:\\管控情况表.xlsx', index_col=0).sort_values(by='日期')
    except:
        df_old = pd.DataFrame(index=[pd.to_datetime('2022-02-28')], columns=location, data=0)
    if source == False:
        outl = []
        for i, r in txt_data.iloc[:14,:].iterrows():
            s = r.上海发布地址
            x = get_data_gysy(s)
            outdf, outdf2 = txt_split_wx(x, location)
            outl.append(outdf2)
        dfout = pd.concat(outl).reset_index(drop=True)
    else:
        x = get_data_gysy(source=source)
        outdf, outdf2 = txt_split_wx(x, location)
        dfout = pd.concat([df_old, outdf2]).drop_duplicates()
    dfout.loc[:, ['管控内新增确诊', '管控内新增无症状', '管控外新增确诊', '管控外新增无症状']] = dfout.loc[:, ['管控内新增确诊', '管控内新增无症状', '管控外新增确诊', '管控外新增无症状']].astype(int)
    dfout.to_excel('E:\\管控情况表.xlsx')

    dfout_ = dfout.set_index('日期').cumsum()
    dfout_.to_excel('E:\\管控折线.xlsx')

def get_ax(source="WJW"):
    df_old = pd.read_excel('E:\\治愈表.xlsx', index_col=0)

    txt_data = pd.read_excel(r'E:\国家卫健委-疫情防控动态.xlsx')
    if source == 'WJW':
        outl = []
        for i, r in txt_data.iloc[:10,:].iterrows():
            x = get_data_gysy(source=r.上海发布地址)
            outdf3 = txt_split_wx_new(x)
            outl.append(outdf3)
        dfo = pd.concat(outl).reset_index(drop=True)
    else:
        x = get_data_gysy(source=source)
        dfo = txt_split_wx_new(x)
    dfout = pd.concat([df_old, dfo]).drop_duplicates().reset_index(drop=True)

    dfout.to_excel('E:\\治愈表.xlsx')

def get_kwxz(source="WJW"):
    location = ['浦东新区', '闵行区', '徐汇区', '嘉定区', '松江区', '黄浦区', '宝山区', '静安区', '普陀区', '崇明区', '奉贤区', '杨浦区', '虹口区', '长宁区',
                '青浦区', '金山区']
    txt_data = pd.read_excel(r'E:\国家卫健委-疫情防控动态.xlsx')
    try:
        df_old = pd.read_excel(r'E:\\控外新增.xlsx', index_col=0)
    except:
        outl = []
        for i, r in txt_data.iloc[:10, :].iterrows():
            s = r.上海发布地址
            x = get_data_gysy(s)
            outdf = txt_split_gq(x, location)
            outl.append(outdf)
        dfout = pd.concat(outl).reset_index(drop=True)
        df_old = dfout.set_index(['日期', '行政区']).新增控外阳性.unstack().T
        df_old.to_excel('E:\\控外新增.xlsx')

    x = get_data_gysy(source=source)
    dfo = txt_split_gq(x, location)
    dfo = dfo.set_index(['日期', '行政区']).新增控外阳性.unstack().T
    dfout = pd.concat([df_old, dfo], axis=1).T.drop_duplicates().T

    dfout.to_excel('E:\\控外新增.xlsx')

def get_china():
    txt_data = pd.read_excel('E:\\全国疫情文本表.xlsx', index_col=0)
    news = get_data_gysy(source='WJW', thre=1)
    txt_data = pd.concat([txt_data, news]).drop_duplicates().sort_values(by='date')
    txt_data.to_excel(r"E:\\全国疫情文本表.xlsx")
    location = pd.read_excel('E:\\province.xlsx',index_col=0).province.to_list()
    outl = []
    for i, r in txt_data.iterrows():
        outdf3 = txt_split_china(r.news, location)
        outdf3['日期'] = r.date
        outl.append(outdf3)
    dfo = pd.concat(outl).reset_index(drop=True)
    dfo['真实新增确诊'] = dfo['新增确诊'] - dfo['无症状转归'] + dfo['新增无症状感染']

    dfo_ = dfo.set_index(['日期', '地区']).真实新增确诊.unstack().sum(axis=1)
    dfo_.columns = ['全国日增阳性']

    dfo__ = dfo.set_index(['日期', '地区']).真实新增确诊.unstack().drop(columns='上海').loc['2022-04-20':,:]
    temp = dfo__.sum()
    dfo__ = dfo__.loc[:, temp[temp!=0].index]

    writer = pd.ExcelWriter("E:\\全国疫情.xlsx")
    dfo_.to_excel(writer, sheet_name='全国日增')
    dfo__.to_excel(writer, sheet_name='各省市日增')
    writer.save()

def renew(source='WJW'):
    txt_data = pd.read_excel(r'E:\国家卫健委-疫情防控动态.xlsx')
    location = ['浦东新区', '闵行区', '徐汇区', '嘉定区', '松江区', '黄浦区', '宝山区', '静安区', '普陀区', '崇明区', '奉贤区', '杨浦区', '虹口区', '长宁区',
                '青浦区', '金山区']
    try:
        df_old = pd.read_excel('E:\\疫情增量表.xlsx', index_col=0)
    except:
        df_old = pd.DataFrame(index=[pd.to_datetime('2022-02-28')], columns=location)

    if source=='local':
        outl = []
        for i, r in txt_data.iloc[:22,:].iterrows():
            x = get_data_gysy(r.上海发布地址)
            outdf, outdf2 = txt_split_wx(x, location)
            outl.append(outdf)
        dfout = pd.concat(outl).reset_index(drop=True)
        dfout.to_excel('E:\\疫情增量表.xlsx')
    elif source=='WJW':
        news = get_data_gysy(source)
        dfout = txt_split(news, location)
        dfout = pd.concat([df_old, dfout]).drop_duplicates()
        dfout.to_excel('E:\\疫情增量表.xlsx')
    else:
        news = get_data_gysy(source)
        dfout, dfout2 = txt_split_wx(news, location)
        dfout = pd.concat([df_old, dfout]).drop_duplicates()
        dfout.to_excel('E:\\疫情增量表.xlsx')

    df = pd.concat([df_old, dfout]).drop_duplicates()
    dfqz = df.groupby(['日期', '行政区']).新增确诊.sum().unstack()
    dfqzc = dfqz.cumsum()
    dfwzz = df.groupby(['日期', '行政区']).新增无症状感染.sum().unstack()
    dfwzzc = dfwzz.cumsum()

    dfall = (dfqzc + dfwzzc).sort_index(ascending=False)
    dfall.T.to_excel('E:\\疫情总量表.xlsx')

    dfzx = (dfqz + dfwzz)
    dfzx['总计'] = dfzx.sum(axis=1)
    dfzx.iloc[-14:, :].T.to_excel('E:\\疫情折线.xlsx')
    print(dfqz.sum(axis=1).iloc[-1], dfwzz.sum(axis=1).iloc[-1])


if __name__ == '__main__':
    s = 'https://mp.weixin.qq.com/s/6Zk1yLrGojy_5bU4oS9ZTA'
    renew(source=s)
    get_gkline(source=s)
    get_ax(source=s)
    get_kwxz(source=s)
    get_china()
'''
df = pd.read_excel("已导出.xlsx", index_col = 0)
error_id = pd.read_csv("error.csv", index_col = 0)
df_l = []
error_id_ = []
pass_id_ = []
for i in error_id:
    try:
        temp_df = get_data(i)

    except Exception:
        error_id_.append(i)
        continue
    df_l.append(temp_df)
    pass_id_.append(i)
    time.sleep(0.2)

df = pd.concat(df_l, axis = 0)
'''
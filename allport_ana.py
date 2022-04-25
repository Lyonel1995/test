import pandas as pd
import numpy as np
from utils.data_api import DATA_API
from utils.config import DIR_ROOT
from datetime import datetime
import os


def load_data(shift_time=6):
    '''

    :param shift_time: 建仓期, 默认为6个月
    :return: port_all: 持仓信息, ann: 公告日期, fundinfo: 基金信息, fund_scale: 基金规模, stock2net: 基金股票持仓占比, price: 股票价格, fund_r_m: 基金收益率（月）, fund_r_q: 基金收益率（季）
    '''
    # fundinfo 时间修改
    fundinfo = pd.read_csv(os.path.join(DIR_ROOT, "fund_data\\fundInfo.csv"), encoding='gbk').dropna(
        subset=['setupDate', "ivstTypeInDt"]).copy()
    # fundinfo.setupDate = fundinfo.setupDate.apply(lambda x: datetime.strptime(str(x)[:-2], "%Y%m%d"))
    fundinfo.setupDate = fundinfo.setupDate.apply(lambda x: datetime.strptime(str(int(x)), "%Y%m%d"))
    # fundinfo.ivstTypeInDt = fundinfo.ivstTypeInDt.apply(lambda x: datetime.strptime(str(x)[:-2], "%Y%m%d"))
    fundinfo.ivstTypeInDt = fundinfo.ivstTypeInDt.apply(lambda x: datetime.strptime(str(int(x)), "%Y%m%d"))
    fundinfo.ivstTypeExDt = fundinfo.ivstTypeExDt.fillna(datetime.strftime(datetime.now(), "%Y%m%d"))
    fundinfo.ivstTypeExDt = fundinfo.ivstTypeExDt.apply(lambda x: datetime.strptime(str(int(x)), "%Y%m%d"))
    fundinfo.wrtOffDate = fundinfo.wrtOffDate.fillna(datetime.strftime(datetime.now(), "%Y%m%d"))
    fundinfo.wrtOffDate = fundinfo.wrtOffDate.apply(lambda x: datetime.strptime(str(int(x)), "%Y%m%d"))
    # fundinfo.wrtOffDate = fundinfo.wrtOffDate.apply(lambda x: datetime.strptime(str(x)[:-2], "%Y%m%d") if str(
    #     fundinfo.wrtOffDate[0]) != 'nan' else datetime.now())
    # fundinfo = fundinfo[fundinfo.fundName.apply(lambda x: "ETF" not in x)]
    # fundinfo['setupDate_sn'] = fundinfo.ivstTypeInDt + pd.DateOffset(months=shift_time) # 用setupDate_sn表示顺推后的并入二级分类日期
    fundinfo['setupDate_sn'] = fundinfo.setupDate + pd.DateOffset(months=shift_time)  # 用setupDate_sn表示顺推后的成立日期
    fundinfo = fundinfo[fundinfo.isinitial == 1]
    fundinfo = fundinfo[fundinfo.fundType == '开放式']
    fundinfo = fundinfo[fundinfo.is_graded == "否"]
    return fundinfo

def clean_data(fundinfo, t):
    fund_detail = fundinfo.copy()
    fund_detail = fund_detail.set_index('fundCode')

    fund_detail = fund_detail[fund_detail.scndIvstType.isin(['普通股票型基金', '偏股混合型基金', '灵活配置型基金', '平衡混合型基金'])]
    # fund_detail = fund_detail[fund_detail.scndIvstType==scndtype]

    fund_detail = fund_detail[(fund_detail.setupDate_sn <= t) & (fund_detail.ivstTypeExDt > t)]
    # fund_detail= fund_detail[~fund_detail.index.duplicated(keep = 'first')]

    fund_detail = fund_detail.reset_index()
    return fund_detail

fundinfo = load_data(shift_time=0)
date1 = '2021-12-31'
date0 = '2021-06-30'
fundport = pd.read_pickle(os.path.join(DIR_ROOT, f"stock_data\\citic&hs_port.pkl"))
fundscale = pd.read_pickle(os.path.join(DIR_ROOT, "fund_data\\fund_scale.pkl")).resample(
    "q").last().stack().reset_index()
fundscale.columns = ["edDt", "fundCode", "scale"]
fundport = pd.merge(fundport, fundscale, on=['fundCode', 'edDt'], how="left")
fundport["stockvalue"] = (fundport.stockvaluetonav / 100) * fundport.scale

port_H1 = fundport[(fundport.edDt==date1) & (fundport.fundCode.isin(clean_data(fundinfo, date1).fundCode.drop_duplicates().to_list()))]
port_H0 = fundport[(fundport.edDt==date0) & (fundport.fundCode.isin(clean_data(fundinfo, date0).fundCode.drop_duplicates().to_list()))]

def get_pivot(port_H1):
    indussum = port_H1.groupby('industry').stockvalue.sum()
    indussum = indussum/indussum.sum()
    return indussum

s1 = get_pivot(port_H1)
s0 = get_pivot(port_H0)
s = pd.concat([s0,s1],axis=1)
s.columns = [date0, date1]
s = s[s.index.map(lambda x: 'HS' not in x)]

s['diff'] = s.iloc[:,-1]-s.iloc[:,0]
s.to_excel(r'E:\BaiduNetdiskWorkspace\实习\全持仓\diff.xlsx')

def get_pivot_stk(port_H1):
    ssum = port_H1.groupby('StockCode').stockvalue.sum()
    snum = port_H1.groupby('StockCode').apply(lambda x: len(x))
    return ssum, snum

stk1,sn1 = get_pivot_stk(port_H1)
stk0,sn0 = get_pivot_stk(port_H0)

stk_all = pd.concat([stk0, stk1, sn1],axis=1)
stk_all.columns = ['t0', 't1', 'num']
stk_all.loc[:,['t0','t1']] = stk_all.loc[:,['t0','t1']].fillna(0)/100000000
stk_all['diff'] = stk_all.t1-stk_all.t0
stk_all.num = stk_all.num.fillna(0)
stk_all.to_excel(r'E:\BaiduNetdiskWorkspace\实习\全持仓\stockkdiff.xlsx')
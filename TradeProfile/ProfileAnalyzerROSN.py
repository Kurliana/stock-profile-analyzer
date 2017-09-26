'''
Created on 06 May 2017

@author: Kurliana
'''
import time
import numpy
import requests
import shutil
import logging.config
import math
import os
import datetime
from multiprocessing import Process, Manager
from collections import Counter
#import pythoncom

logging.config.fileConfig('log_nvtk.conf')
log=logging.getLogger('main')
from ProfileAnalyzer import ProfileAnalyser

class ProfileAnalyserROSN(ProfileAnalyser):

    def get_ranges_by_dayweek(self,curr_date):
        day_of_week =  self.get_day_week(curr_date)
        day_ranges={0:[100000, 105000, 110000, 175000, -1, 0, 0.04, 3, 'take_innsta_0.005', 14, 0],
                    1:[100000, 120000, 122000, 180000, -1, 0, 0.02, 4, 'take_innsta_0.015', 27, 0],
                    2:[100000, 105000, 110000, 161000, -1, 0, 0.03, 3, 'take_innsta_0.01', 9, 14],
                    3:[100000, 102000, 103000, 173000, -1, 0, 0.03, 4, 'take_innsta_0.0075', 9, 14],
                    4:[100000, 105000, 110000, 175000, -1, 0, 0.02, 3, 'take_innsta_0.005', 9, 0],
                    5:[183000, 183000, 183000, 183000,1],
                    6:[183000, 183000, 183000, 183000,1]}

        return [day_ranges[day_of_week]]

    def get_ranges_by_dayweek_new(self,curr_date):
        day_of_week = self.get_day_week(curr_date)
        day_ranges={0:[[100000, 112000, 114000, 162000, 1, 0, 0.01, 3, 'take_innsta_0.04', 27, 0],[]],
                    1:[[100000, 101000, 102000, 171000, 1, 0, 0.04, 4, 'take_innsta_0.03', 14, 20],[]],
                    2:[[100000, 101000, 121000, 175000, -1, 0, 0.03, 3, 'take_innsta_0.02', 14, 20],[]],
                    3:[[183000, 183000, 183000, 183000,1],[]],
                    4:[[183000, 183000, 183000, 183000,1],[]],
                    5:[self.end_time, self.end_time, self.end_time, self.end_time,1],
                    6:[self.end_time, self.end_time, self.end_time, self.end_time,1]}
        
        return [day_ranges[day_of_week]]
    
if __name__ == "__main__":
    # based on my_app_0817_full_tatn_atr
    start_timer=time.time()
    temp_file_name="daily_ROSN.txt"
    result_files=["C:\\Just2Trade Client\\Rosneft.txt","C:\\Just2Trade Client\\reserv_Rosneft.txt"]
    if os.path.exists(temp_file_name):
        os.remove(temp_file_name)
    cur_date=time.localtime()
    cur_year=cur_date[0]
    cur_month=cur_date[1]
    cur_day=cur_date[2]
    results_days=[]
    results_profit=[]
    results_procent=[]
    results_days_rev=[]
    results_profit_rev=[]
    results_procent_rev=[]
    results_days_dir=[]
    results_profit_dir=[]
    results_procent_dir=[]
    get_file_string="http://export.finam.ru/export9.out"
    stock_params={"market":"1",
                  "em":"17273",
                  "code":"ROSN",
                  "apply":"0",
                  "df":"1",
                  "mf":"5",
                  "yf":"2017",
                  "from":"01.06.2017",
                  "dt":"%s" % cur_day,
                  "mt":"%s" % (cur_month-1),
                  "yt":"%s" % cur_year,
                  "to":"%s.%s.%s" % (cur_day,cur_month,cur_year),
                  "p":"4", # period means 10 minutes
                  "e":".txt", # export format
                  "f":"%s" % temp_file_name.split(".")[0],
                  "cn":"ROSN",
                  "dtf":"1",
                  "tmf":"1",
                  "sep":"1",
                  "sep2":"1",
                  "datf":"1",
                  "at":"0",
                  "fsp":"1",
                  "MSOR":"1",                 
                  }
    r = requests.post(get_file_string, stock_params,stream=True,allow_redirects=True)
    with open(temp_file_name, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
        
    pa = ProfileAnalyserROSN(temp_file_name)
    log.info("All saved dayes %s " % len(pa.days))
    start_date=pa.days[0]
    best_ranges = pa.robot(start_date, 5, day_end = int("%d%.2d%.2d" % (cur_year,cur_month,cur_day)),delta=0.005,loss=0.015)
    for best_range_ind in range(len(best_ranges)):
        best_range=best_ranges[best_range_ind]
        result_file=result_files[best_range_ind]
        if not best_range:
            with open(result_file, 'wb') as f:
                f.write("\n")
                #f.write("00\n")
                #f.write("00\n")
                #f.write("00\n")
                #f.write("00\n")
                #f.write("00\n")
        else:    
            begin_time,check_time,start_time,end_time,trade,delta,loss,take,method, ema1, ema2 = best_range[0], best_range[1], best_range[2], best_range[3], best_range[4], best_range[5], best_range[6], best_range[7], best_range[8], best_range[9], best_range[10]              
            #current_date=datetime.date.today().strftime("%Y%m%d")
            #begin_time,check_time,start_time,end_time,trade = pa.get_ranges_by_dayweek(int(current_date))[0]
            #log.info("Current date %s" % current_date)
            #period_day_tickers = pa.filter_tickers(pa.tickers, 100000,184000,pa.days[-6],pa.days[-1])
            #day_profit, day_count, day_procent, day_list_profit = pa.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, 0.0005, 0.015, 1, 0.02, True)
            with open(result_file, 'wb') as f:
                f.write(str(check_time)[:2]+"\n")
                f.write(str(check_time)[2:4]+"\n")
                f.write(str(start_time)[:2]+"\n")
                f.write(str(start_time)[2:4]+"\n")
                f.write(str(end_time)[:2]+"\n")
                f.write(str(end_time)[2:4]+"\n")
                f.write(str(trade)+"\n")
                f.write(str(delta)+"\n")
                f.write(str(loss)+"\n")
                f.write(str(take)+"\n")
                f.write("".join(str(method).split("_")[:-1])+"\n")
                f.write("".join(str(method).split("_")[-1])+"\n")
                f.write(str(ema1)+"\n")
                f.write(str(ema2)+"\n")

    log.info( time.time()-start_timer)
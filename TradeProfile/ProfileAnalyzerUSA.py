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
from indicators import TradeIndicators
#import pythoncom


log=logging.getLogger('main')

class ProfileAnalyser():
    
    def __init__(self, tick_file = "", day_of_week=-1):
        self.thread_index=0
        self.comission=0.01
        self.go=20
        self.tickers=[]
        self.days=[]
        self.results_days=[]
        self.results_profit=[]
        self.results_procent=[]
        self.allowed_times={0:[],1:[],2:[],3:[],4:[],5:[],6:[]}
        self.success_ranges=[]
        current_day=0
        with open(tick_file,"r+") as f:
            single_ticker = f.readline()
            while single_ticker:
                candle = single_ticker.split(",")
                candle[1]=int(candle[1])
                candle[2]=int(candle[2])
                candle[3]=int(candle[3])
                candle[4]=float(candle[4])
                candle[5]=float(candle[5])
                candle[6]=float(candle[6])
                candle[7]=float(candle[7])
                candle[8]=int(candle[8])
                candle.append({})
                if day_of_week < 0 or day_of_week ==  self.get_day_week(candle[2]):
                    self.tickers.append(candle)
                    if not current_day == candle[2]:
                        current_day = candle[2]
                        self.days.append(current_day)
                single_ticker = f.readline()
        self.time_range=range(94000,160000,1000)
        for one_time_counter in range(len(self.time_range)-1,-1,-1):
            if self.time_range[one_time_counter] % 10000 > 5000:
                del self.time_range[one_time_counter]
        self.days.sort()
        ti = TradeIndicators(self.tickers)
        self.tickers=ti.count_indicators(["ATR"])
        del ti

    def filter_tickers(self, tikers, begin_time=94000, end_time=120000, date_start=-1,date_end=-1,day_of_week=-1):
        filtered_tickers=[]
        for single_ticker in tikers:
            single_ticker_time=single_ticker[3]
            if single_ticker_time >= begin_time and single_ticker_time <= end_time:
                if date_start < 0 or date_start <= single_ticker[2]:
                    if date_end < 0 or date_end >= single_ticker[2]:
                        if day_of_week < 0 or day_of_week == self.get_day_week(single_ticker[2]):
                            filtered_tickers.append(single_ticker)
                            
                        
        return filtered_tickers
    
    def group_tickers(self, tickers, group_time=3000):
        pass
    
    def combine_tickers(self, ticker1, ticker2):
        total_ticker=[]
        total_ticker+=ticker1
        total_ticker[3]=max(ticker1[3],ticker2[3])
        total_ticker[5]=max(ticker1[5],ticker2[5])
        total_ticker[6]=min(ticker1[6],ticker2[6])
        total_ticker[7]=ticker2[7]
        return total_ticker
    
    def combine_multi_tickers_slide(self, tickers_list, start_time = -1, end_time = 200000, stop = 0.015,take=0.005,direction = 1, schema = "Noschema"):
        total_ticker=[]
        #high_low=[]
        min_value=200000000
        min_time=0
        max_value=0
        max_time=0
        close_value=0
        stop_value=0
        take_value=0
        take_price=0
        start_value=0
        start_values={}
        obv=0

        #print tickers_list,start_time,end_time
        for ticker in tickers_list:
            if ticker[3] > start_time and ticker[3] <= end_time:
                if not total_ticker:
                    #log.info(ticker)
                    if (take == 0) or (direction > 0 and ticker[6] > ticker[9]["ATRTS"+str(take)]) or (direction < 0 and ticker[5] < ticker[9]["ATRTS"+str(take)]):
                        #log.info("Start time %s value %s" % (ticker[3],ticker[4]))
                        total_ticker+=ticker
                if total_ticker:
                    if take_price == 0:
                        start_value=ticker[4]
                        if direction > 0:
                            #log.info("Direction upstream")
                            take_price=ticker[4]*(1-stop)
                        if direction < 0:
                            #log.info("Direction downstram")
                            take_price=ticker[4]*(1+stop)
                    if ticker[4] > ticker[7]:
                        obv+=ticker[8]
                    else:
                        obv-=ticker[8]
                    if ticker[5] > max_value:
                        max_value = ticker[5]
                        max_time = ticker[3]
                    if ticker[6] < min_value:
                        min_value = ticker[6]
                        min_time = ticker[3]
                    #high_low.append(ticker[5])
                    #high_low.append(ticker[6])
    
                    close_value=ticker[7]
                    if schema.find("stop_limit")>=0:
                        take_limit = float(schema[11:])
                    if schema.find("take_atrts")>=0:
                        take_limit = float(schema[11:])
                    if schema.find("take_equity")>=0:
                        take_limit = float(schema[12:])
                    if schema.find("take_shorty")>=0:
                        take_limit = float(schema[12:])
                    if schema.find("take_revers")>=0:
                        take_limit = float(schema[12:])
                    if schema.find("take_sinrev")>=0:
                        take_limit = float(schema[12:])
                    if schema.find("take_innsta")>=0:
                        take_limit = float(schema[12:])
                    if schema.find("wrong_equity")>=0:
                        take_limit = float(schema[13:])

                    if direction > 0:
                        if schema == "simple" and ticker[5] > total_ticker[4]*(1+take) and take_value == 0 and stop_value == 0:
                            #log.info("Take profit simple %s up, take price %s, max price %s, profit %s" % (take, total_ticker[4]*(1+take),ticker[5],take))
                            take_value = take
                        if schema.find("stop_limit")>=0 and max_value > total_ticker[4]*(1+take_limit) and max_value*(1-take) > ticker[6] and take_value == 0 and stop_value == 0:
                            take_value = ((max_value*(1-take))/total_ticker[4])-1
                            #log.info("Take profit stop_limit %s up, take price %s, min price %s, profit %s" % (take_limit,max_value*(1-take),ticker[6],take_value))
                        if schema.find("take_equity")>=0 and take_value == 0 and stop_value == 0:
                            if ticker[6] < take_price:
                                take_value = (take_price/total_ticker[4])-1
                                #log.info("Take profit take_equity %s up, take price %s, min price %s, profit %s" % (take_limit,take_price,ticker[6],take_value))
                            tmp_take_price = ticker[5]*(1-take-(stop + take_limit)*max(0,1-(ticker[5]-total_ticker[4])/((stop + take_limit)*total_ticker[4])))
                            if tmp_take_price > take_price:
                                take_price = tmp_take_price
                                #log.info("Take profit take_equity %s up, take price %s, max price %s, min price %s, profit %s" % (total_ticker[4],take_price,ticker[5],ticker[6],take_value))
                        if schema.find("take_shorty")>=0 and take_value == 0 and stop_value == 0:
                            if total_ticker and take > 0 and ticker[6] < ticker[9]["ATRTS"+str(take)]:
                                take_value = (ticker[7]/start_value)-1
                            if total_ticker and ticker[6] < take_price:
                                #log.info("stop value")
                                take_value = (take_price/total_ticker[4])-1
                                #log.info("Take profit take_equity %s up, take price %s, min price %s, profit %s" % (take_limit,take_price,ticker[6],take_value))
                            tmp_take_price = ticker[5]*(1-(stop + take_limit)*max(0,1-(ticker[5]-total_ticker[4])/((take_limit)*total_ticker[4])))
                            if tmp_take_price > take_price:# and tmp_take_price < ticker[7]:
                                take_price = tmp_take_price
                                
                        if schema.find("take_atrts")>=0 and take_value == 0 and stop_value == 0:
                            if total_ticker and take > 0 and ticker[6] < ticker[9]["ATRTS"+str(take)]:
                                take_value = (ticker[7]/start_value)-1
                            #if total_ticker and ticker[6] < take_price:
                                #log.info("max value %s %s" % (take_price,ticker[3]))
                            #    take_value = (take_price/start_value)-1
                                #log.info("Take profit take_equity %s up, take price %s, min price %s, profit %s" % (take_limit,take_price,ticker[6],take_value))
                            #tmp_take_price = ticker[6]-ticker[9]["ATR"]*take
                            #if tmp_take_price > take_price:# and tmp_take_price < ticker[7]:
                                #log.info("ATRTS %s" % take_price)
                            #    take_price = tmp_take_price
                                
                        if schema.find("take_revers")>=0 and stop_value == 0:
                            if ticker[6] < take_price:
                                #log.info("Revers %s" % take_price)
                                take_value += (take_price/start_value)-1-self.comission/self.go
                                start_value=take_price
                                direction=-1
                                take_price=start_value*(1+stop)
                            else:
                                #log.info("Take profit take_equity %s up, take price %s, min price %s, profit %s" % (take_limit,take_price,ticker[6],take_value))
                                tmp_take_price = ticker[5]*(1-take-(stop + take_limit)*max(0,1-(ticker[5]-start_value)/((take_limit)*start_value)))
                                if tmp_take_price > take_price:
                                    take_price = tmp_take_price
                                if take_price > ticker[7]:
                                    take_price=ticker[7]*(1-take)
                        if schema.find("take_sinrev")>=0 and take_value == 0 and stop_value == 0:
                            if ticker[6] < take_price:
                                #log.info("Revers %s" % take_price)
                                take_value += (take_price/start_value)-1-self.comission/self.go
                                start_value=take_price
                                direction=-1
                                take_price=start_value*(1+stop)
                            else:
                                #log.info("Take profit take_equity %s up, take price %s, min price %s, profit %s" % (take_limit,take_price,ticker[6],take_value))
                                tmp_take_price = ticker[5]*(1-take-(stop + take_limit)*max(0,1-(ticker[5]-start_value)/((take_limit)*start_value)))
                                if tmp_take_price > take_price:
                                    take_price = tmp_take_price
                                if take_price > ticker[7]:
                                    take_price=ticker[7]*(1-take)
                        if schema.find("take_innsta")>=0 and take_value == 0 and stop_value == 0:
                            if total_ticker and take > 0 and ticker[6] < ticker[9]["ATRTS"+str(take)]:
                                take_value = (ticker[7]/start_value)-1
                                #log.info(ticker)
                                #log.info("Stop by atr at %s with start %s end %s" % (ticker[3],start_value,ticker[7]))
                            if ticker[6] < take_price and take_value == 0:
                                take_value = (take_price/total_ticker[4])-1
                                #log.info(ticker)
                                #log.info("Stop by limit at %s with start %s end %s" % (ticker[3],total_ticker[4],take_price))
                                #log.info("Take profit take_equity %s up, take price %s, min price %s, profit %s" % (take_limit,take_price,ticker[6],take_value))
                            tmp_take_price = ticker[5]*(1-(stop + take_limit)*max(0,1-(ticker[5]-total_ticker[4])/((take_limit)*total_ticker[4])))
                            if tmp_take_price > take_price:
                                take_price = tmp_take_price
                            if take_price > ticker[7]:
                                take_value=(ticker[7]/total_ticker[4])-1
                                #take_price=ticker[7]*(1-take)
                                #log.info("Take profit take_shorty %s up, take price %s, max price %s, min price %s, profit %s" % (total_ticker[4],take_price,ticker[5],ticker[6],take_value))
                        if ticker[6] < total_ticker[4]*(1-stop) and take_value == 0 and stop_value == 0:
                            stop_value = -stop
                        if schema.find("wrong_equity")>=0 and take_value == 0 and stop_value == 0:
                            if ticker[6] < take_price:
                                take_value = (take_price/total_ticker[4])-1
                                #log.info("Take profit take_equity %s up, take price %s, min price %s, profit %s" % (take_limit,take_price,ticker[6],take_value))
                            tmp_take_price = ticker[5]*(1-take-max(0,1-(ticker[5]-total_ticker[4])/((take_limit)*total_ticker[4])))
                            if tmp_take_price > take_price:
                                take_price = tmp_take_price
                            #log.info("Take profit take_equity %s up, take price %s, max price %s, min price %s, profit %s" % (total_ticker[4],take_price,ticker[5],ticker[6],take_value))
                    elif direction < 0:
                        if schema == "simple" and ticker[6] < total_ticker[4]*(1-take) and take_value == 0 and stop_value == 0:
                            #log.info("Take profit simple %s down, take price %s, min price %s, profit %s" % (take, total_ticker[4]*(1-take),ticker[6],take))
                            take_value = take
                        if schema.find("stop_limit")>=0 and min_value < total_ticker[4]*(1-take_limit) and min_value*(1+take) < ticker[5] and take_value == 0 and stop_value == 0:
                            take_value = (total_ticker[4]/(min_value*(1+take)))-1
                            #log.info("Take profit stop_limit %s down, take price %s, max price %s, profit %s" % (take_limit,min_value*(1+take),ticker[5],take_value))
                        if schema.find("take_equity")>=0 and take_value == 0 and stop_value == 0:
                            if ticker[5] > take_price:
                                take_value = (total_ticker[4]/take_price)-1
                                #log.info("Take profit take_equity %s down, take price %s, max price %s, profit %s" % (take_limit,take_price,ticker[5],take_value))
                            tmp_take_price = ticker[6]*(1+take+(stop + take_limit)*max(0,1-(total_ticker[4]-ticker[6])/((stop + take_limit)*total_ticker[4])))
                            if tmp_take_price < take_price:
                                take_price = tmp_take_price
                            #log.info("Take profit take_equity %s down, take price %s, max price %s, min price %s, profit %s" % (total_ticker[4],take_price,ticker[5],ticker[6],take_value))
                        if schema.find("take_shorty")>=0 and take_value == 0 and stop_value == 0:
                            #if ticker[7] > ticker[4] and ticker[9]["ATR"]*take<ticker[5]-ticker[6]:
                                #log.info("Max value %s %s %s" % (max_value*(1-take),ticker[3],total_ticker[4]))
                            #    take_value = (total_ticker[4]/ticker[7])-1
                            if total_ticker and take > 0 and ticker[5] > ticker[9]["ATRTS"+str(take)]:
                                take_value = (ticker[7]/start_value)-1
                            if total_ticker and ticker[5] > take_price:
                                take_value = (total_ticker[4]/take_price)-1
                                #log.info("Take profit take_equity %s down, take price %s, max price %s, profit %s" % (take_limit,take_price,ticker[5],take_value))
                            tmp_take_price = ticker[6]*(1+(stop + take_limit)*max(0,1-(total_ticker[4]-ticker[6])/((take_limit)*total_ticker[4])))
                            if tmp_take_price < take_price:# and tmp_take_price > ticker[7]:
                                take_price = tmp_take_price
                            #if take_price < ticker[7]:
                            #    take_price=ticker[7]*(1+take)
                        if schema.find("take_atrts")>=0 and take_value == 0 and stop_value == 0:
                            if total_ticker and take > 0 and ticker[5] > ticker[9]["ATRTS"+str(take)]:
                                take_value = (ticker[7]/start_value)-1
                            #if total_ticker and ticker[5] > take_price:
                                #log.info("min value %s %s" % (take_price,ticker[3]))
                            #    take_value = (total_ticker[4]/take_price)-1
                                #log.info("Take profit take_equity %s down, take price %s, max price %s, profit %s" % (take_limit,take_price,ticker[5],take_value))
                            #tmp_take_price = ticker[5]+ticker[9]["ATR"]*take
                            #if tmp_take_price < take_price:# and tmp_take_price > ticker[7]:
                            #    take_price = tmp_take_price
                            #if take_price < ticker[7]:
                        if schema.find("take_revers")>=0 and stop_value == 0:
                            if ticker[5] > take_price:
                                #log.info("Revers %s" % take_price)
                                take_value += (start_value/take_price)-1-self.comission/self.go
                                start_value=take_price
                                direction=1
                                take_price=start_value*(1-stop)
                                #log.info("Take profit take_equity %s down, take price %s, max price %s, profit %s" % (take_limit,take_price,ticker[5],take_value))
                            else:
                                tmp_take_price = ticker[6]*(1+take+(stop + take_limit)*max(0,1-(start_value-ticker[6])/((take_limit)*start_value)))
                                if tmp_take_price < take_price:
                                    take_price = tmp_take_price
                                if take_price < ticker[7]:
                                    take_price=ticker[7]*(1+take)
                        if schema.find("take_sinrev")>=0 and take_value == 0 and stop_value == 0:
                            if ticker[5] > take_price:
                                #log.info("Revers %s" % take_price)
                                take_value += (start_value/take_price)-1-self.comission/self.go
                                start_value=take_price
                                direction=1
                                take_price=start_value*(1-stop)
                                #log.info("Take profit take_equity %s down, take price %s, max price %s, profit %s" % (take_limit,take_price,ticker[5],take_value))
                            else:
                                tmp_take_price = ticker[6]*(1+take+(stop + take_limit)*max(0,1-(start_value-ticker[6])/((take_limit)*start_value)))
                                if tmp_take_price < take_price:
                                    take_price = tmp_take_price
                                if take_price < ticker[7]:
                                    take_price=ticker[7]*(1+take)
                        if schema.find("take_innsta")>=0 and take_value == 0 and stop_value == 0:
                            if total_ticker and take > 0 and ticker[5] > ticker[9]["ATRTS"+str(take)]:
                                take_value = (ticker[7]/start_value)-1
                                #log.info(ticker)
                                #log.info("Stop by atr at %s with start %s end %s" % (ticker[3],start_value,ticker[7]))
                            if ticker[5] > take_price and take_value == 0:
                                #log.info(ticker)
                                #log.info("Stop by limit at %s with start %s end %s" % (ticker[3],total_ticker[4],take_price))
                                take_value = (total_ticker[4]/take_price)-1
                                #log.info("Take profit take_equity %s down, take price %s, max price %s, profit %s" % (take_limit,take_price,ticker[5],take_value))
                            tmp_take_price = ticker[6]*(1+(stop + take_limit)*max(0,1-(total_ticker[4]-ticker[6])/((take_limit)*total_ticker[4])))
                            if tmp_take_price < take_price:
                                take_price = tmp_take_price
                            if take_price < ticker[7]:
                                #take_price=ticker[7]*(1+take)
                                take_value=(total_ticker[4]/ticker[7])-1                      
    
                            #log.info("Take profit take_shorty %s down, take price %s, max price %s, min price %s, profit %s" % (total_ticker[4],take_price,ticker[5],ticker[6],take_value))
                        if schema.find("wrong_equity")>=0 and take_value == 0 and stop_value == 0:
                            if ticker[5] > take_price:
                                take_value = (total_ticker[4]/take_price)-1
                                #log.info("Take profit take_equity %s down, take price %s, max price %s, profit %s" % (take_limit,take_price,ticker[5],take_value))
                            tmp_take_price = ticker[6]*(1+take+max(0,1-(total_ticker[4]-ticker[6])/((take_limit)*total_ticker[4])))
                            if tmp_take_price < take_price:
                                take_price = tmp_take_price
                            #log.info("DEBUG %s %s %s %s %s %s" % (stop,take,take_limit,(total_ticker[4]-ticker[6]),((stop+take_limit)*total_ticker[4]),(total_ticker[4]-ticker[6])/((stop+take_limit)*total_ticker[4])))
                        if ticker[5] > total_ticker[4]*(1+stop) and take_value == 0 and stop_value == 0:
                            stop_value = -stop
        if not total_ticker:
            return [], 0, 0
        total_ticker[3]=max_time
        total_ticker[5]=max_value
        total_ticker[6]=min_value
        total_ticker[7]=close_value
        total_ticker[8]=min_time
        total_ticker.append({})
        
        if (schema.find("take_revers")>=0 or schema.find("take_sinrev")>=0)and not take_value == 0:
            if direction > 0:
                take_value += (close_value/start_value)-1
            elif direction < 0:
                take_value += (start_value/close_value)-1
        return total_ticker,stop_value,take_value
    
    def combine_multi_tickers(self, tickers_list, start_time = -1, end_time = 200000):
        total_ticker=[]
        #high_low=[]
        min_value=200000000
        min_time=0
        max_value=0
        max_time=0
        close_time=0
     
        #print tickers_list,start_time,end_time
        for ticker in tickers_list:
            if ticker[3] > start_time and ticker[3] <= end_time:
                if ticker[5] > max_value:
                    max_value = ticker[5]
                    max_time = ticker[3]
                if ticker[6] < min_value:
                    min_value = ticker[6]
                    min_time = ticker[3]
                #high_low.append(ticker[5])
                #high_low.append(ticker[6])
                if not total_ticker:
                    total_ticker+=ticker
                close_time=ticker[7]
        if not total_ticker:
            return []
        total_ticker[3]=max_time
        total_ticker[5]=max_value
        total_ticker[6]=min_value
        total_ticker[7]=close_time
        total_ticker[8]=min_time
        total_ticker.append({})
        
        return total_ticker
    
    def _get_list_weight_stat(self, result_list):
        result=[]
        x=[]
        for single_result in result_list:
            x.append(single_result[0])
            
        _x=numpy.array(x)    
        result.append(numpy.mean(_x))
        result.append((numpy.min(_x), numpy.max(_x)))
        result.append(numpy.std(_x))
        result.append(result[0]/result[-1])
        result.append((numpy.percentile(_x, 25), numpy.percentile(_x, 50), numpy.percentile(_x, 75)))
        log.info("List statistic: %s" % result)
        return result
    
    def _get_weekdays_period(self, curr_date, period, dayweek):
        found_days=0
        end_ind = None
        for rev_ind in range(self.days.index(curr_date)-1,-1,-1):
            tmp_dayweek = self.get_day_week(self.days[rev_ind])
            if dayweek == -1 or tmp_dayweek == dayweek:
                found_days+=1
                if not end_ind:
                    end_ind = rev_ind
            if found_days == period+1:
                return rev_ind, end_ind
        return None, None

    def get_list_weight_stat(self, result_list):
        pass
    
    def _find_candle_in_ranges(self, candle_ranges, begin_time = 94000, check_time=102000, start_time=102000, end_time=120000, base_ind_diff=0):
        for single_candle in candle_ranges:
            if single_candle[2+base_ind_diff] == begin_time and single_candle[3+base_ind_diff] == check_time and single_candle[4+base_ind_diff] == start_time and single_candle[5+base_ind_diff] == end_time:
                return single_candle
            
        return None
    
    def get_candle_ranges_old(self, selected_timelines, result_days = None,return_all=False):

        begin_times=[]
        check_times=[]
        start_times=[]
        end_times=[]
        trade_direct=[]
        
        for single_result in selected_timelines:
            begin_times.append(single_result[2])
            check_times.append(single_result[3])
            start_times.append(single_result[4])
            end_times.append(single_result[5])
            trade_direct.append(single_result[11])
            
        #log.info("Trade selection %s" % trade_direct)
        if not return_all:
            begin_dict=Counter(begin_times).most_common()
            check_dict=Counter(check_times).most_common()
            start_dict=Counter(start_times).most_common()
            end_dict=Counter(end_times).most_common()
            trade_dict=Counter(trade_direct).most_common()
            #print begin_dict
            
            #return [[begin_dict[0][0],check_dict[0][0],self.time_range[self.time_range.index(start_dict[0][0])+1],self.time_range[self.time_range.index(end_dict[0][0])+1],trade_dict[0][0]]]
            
            return [[begin_dict[0][0],check_dict[0][0],start_dict[0][0],end_dict[0][0],trade_dict[0][0]]]
        else:
            return_list=[]
            for singe_res_ind in range(len(begin_times)):
                return_list.append([begin_times[singe_res_ind],check_times[singe_res_ind],start_times[singe_res_ind],end_times[singe_res_ind],trade_direct[singe_res_ind]])
            return return_list
            
    def _get_result_day_by_time(self, result_days, begin_time, check_time, start_time, end_time, index_offset = 0):
        for single_result in result_days:
            if single_result[2+index_offset] == begin_time and single_result[3+index_offset] == check_time and single_result[4+index_offset] == start_time and single_result[5+index_offset] == end_time:
                return single_result
        return None
    
    def get_day_week(self, date_int):
        return datetime.datetime(int(str(date_int)[:4]), int(str(date_int)[4:6]), int(str(date_int)[6:8]), 23, 55, 55, 173504).weekday()
    
    def get_candle_ranges_new2(self, selected_timelines, result_days = None,return_all=False):
        max_weight = 0
        best_timeline=[[160000,160000,160000,160000,1]]
        
        for single_result in selected_timelines:
            sum_weights=[]
            begin_times_index=self.time_range.index(single_result[2])
            check_times_index=self.time_range.index(single_result[3])
            start_times_index=self.time_range.index(single_result[4])
            end_times_index=self.time_range.index(single_result[5])
            for begin_index in [begin_times_index,begin_times_index+1]:
                for check_index in [check_times_index-1,check_times_index,check_times_index+1]:
                    for start_index in [start_times_index-1,start_times_index,start_times_index+1]:
                        for end_index in [end_times_index-1,end_times_index,end_times_index+1]:
                            begin_time = self.time_range[begin_index]
                            check_time = self.time_range[check_index]
                            start_time = self.time_range[start_index]
                            end_time = self.time_range[end_index]
                            tmp_result = self._get_result_day_by_time(result_days, begin_time, check_time, start_time, end_time)
                            if tmp_result:
                                sum_weights.append(tmp_result[0])
                            else:
                                sum_weights.append(0)
            sum_array = numpy.array(sum_weights)
            sum_std = numpy.std(sum_array)
            if sum_std == 0:
                sum_std=0.0000001
            single_weight = numpy.mean(numpy.array(sum_weights))/sum_std
            if single_weight >= max_weight:
                max_weight = single_weight
                best_timeline=[[single_result[2],single_result[3],single_result[4],single_result[5],single_result[11]]]
                
        return best_timeline

    def get_candle_ranges(self, selected_timelines, result_days = None,return_all=False):
        max_weight = 0
        best_timeline=[[160000,160000,160000,160000,1]]
        
        for single_result in selected_timelines:
            sum_weights=0
            begin_times_index=self.time_range.index(single_result[2])
            check_times_index=self.time_range.index(single_result[3])
            start_times_index=self.time_range.index(single_result[4])
            end_times_index=self.time_range.index(single_result[5])
            for begin_index in [begin_times_index,begin_times_index+1]:
                for check_index in [check_times_index-1,check_times_index,check_times_index+1]:
                    for start_index in [start_times_index-1,start_times_index,start_times_index+1]:
                        for end_index in [end_times_index-1,end_times_index,end_times_index+1]:
                            begin_time = self.time_range[begin_index]
                            check_time = self.time_range[check_index]
                            start_time = self.time_range[start_index]
                            end_time = self.time_range[end_index]
                            tmp_result = self._get_result_day_by_time(result_days, begin_time, check_time, start_time, end_time)
                            if tmp_result:
                                sum_weights+=tmp_result[0]
            #single_weight = numpy.mean(numpy.array(sum_weights))/numpy.std(numpy.array(sum_weights))
            if sum_weights >= max_weight:
                max_weight = sum_weights
                best_timeline=[[single_result[2],single_result[3],single_result[4],single_result[5],single_result[11]]]
                
        return best_timeline

    def is_up_direction(self, ticker1, check_time=102000, direction_delta = 0):
        if not ticker1:
            return 0
        if (abs(ticker1[4] - ticker1[7]) > min(ticker1[4],ticker1[7])*direction_delta) and ticker1[4] < ticker1[7]: #and ticker1[9] > obv_delta: #upstream
            return 1
        elif (abs(ticker1[4] - ticker1[7]) > min(ticker1[4],ticker1[7])*direction_delta) and ticker1[4] > ticker1[7]: #and ticker1[9] < obv_delta:
            return -1
        else:
            return 0
        
    def check_direction_slide(self, ticker2, up_direction, start_time=102000, end_time=120000, delta=0, stop_loss=0.015, take_profit=200):
        if not ticker2:
            #print "Failed to found ticker2 in case: %s, %s, %s" % (tickers_by_day, start_time, end_time)
            return None

        if up_direction > 0: #upstream
            
            # update slide stoploss
            if ticker2[3] > ticker2[8]: # max price before min price
                take_profit= (ticker2[5]/ticker2[4]-1-take_profit)
            
            if ticker2[6] < ticker2[4]*(1-stop_loss) and ticker2[5] > ticker2[4]*(1+take_profit):
                if ticker2[3] > ticker2[8]:
                    return (ticker2[4]*(1+take_profit))/ticker2[4]
                else:
                    return (ticker2[4]*(1-stop_loss))/ticker2[4]
            elif ticker2[6] < ticker2[4]*(1-stop_loss):
                return (ticker2[4]*(1-stop_loss))/ticker2[4]
            elif ticker2[5] > ticker2[4]*(1+take_profit):
                return (ticker2[4]*(1+take_profit))/ticker2[4]
            else:
                return ticker2[7]/ticker2[4]
        else:
            # update slide stoploss
            if ticker2[3] < ticker2[8]: # max price before min price
                take_profit= (ticker2[4]/ticker2[6]-1-take_profit)
                
            if ticker2[6] < ticker2[4]*(1-take_profit) and ticker2[5] > ticker2[4]*(1+stop_loss):
                if ticker2[3] < ticker2[8]:
                    return ticker2[4]/(ticker2[4]*(1+stop_loss))
                else:
                    return ticker2[4]/(ticker2[4]*(1-take_profit))
            elif ticker2[6] < ticker2[4]*(1-take_profit):
                return ticker2[4]/(ticker2[4]*(1-take_profit))
            elif ticker2[5] > ticker2[4]*(1+stop_loss):
                return ticker2[4]/(ticker2[4]*(1+stop_loss))
            else:
                return ticker2[4]/ticker2[7]

    def check_direction(self, ticker2, up_direction, start_time=102000, end_time=120000, delta=0, stop_loss=0.015, take_profit=200):
        take_profit = 200
        if not ticker2:
            #print "Failed to found ticker2 in case: %s, %s, %s" % (tickers_by_day, start_time, end_time)
            return None

        if up_direction > 0: #upstream
            if ticker2[6] < ticker2[4]*(1-stop_loss) and ticker2[5] > ticker2[4]*(1+take_profit):
                if ticker2[3] > ticker2[8]:
                    return (ticker2[4]*(1+take_profit))/ticker2[4]
                else:
                    return (ticker2[4]*(1-stop_loss))/ticker2[4]
            elif ticker2[6] < ticker2[4]*(1-stop_loss):
                return (ticker2[4]*(1-stop_loss))/ticker2[4]
            elif ticker2[5] > ticker2[4]*(1+take_profit):
                return (ticker2[4]*(1+take_profit))/ticker2[4]
            else:
                return ticker2[7]/ticker2[4]
        else:
            if ticker2[6] < ticker2[4]*(1-take_profit) and ticker2[5] > ticker2[4]*(1+stop_loss):
                if ticker2[3] < ticker2[8]:
                    return ticker2[4]/(ticker2[4]*(1+stop_loss))
                else:
                    return ticker2[4]/(ticker2[4]*(1-take_profit))
            elif ticker2[6] < ticker2[4]*(1-take_profit):
                return ticker2[4]/(ticker2[4]*(1-take_profit))
            elif ticker2[5] > ticker2[4]*(1+stop_loss):
                return ticker2[4]/(ticker2[4]*(1+stop_loss))
            else:
                return ticker2[4]/ticker2[7]
                
    def analyze_by_day(self, tickers, check_time=102000, start_time=102000, end_time=120000, delta=0, direction_delta = 0.001, stop_loss = 0.015, reverse_trade=1, take_profit = 200, ignore_check_limit = True, take_profit_schema = "Noschema"):
        day_count=0
        check_diff_limit=0.02
        if len(tickers) == 0:
            log.info("No any tickers found")
            return 0,1,1,[],0
        day_tickers=[tickers[0]]
        total_profit=0
        count_profit=1
        procn_profit=1
        list_profit=[]
        zero_days=0
        for single_ticker in tickers:
            if single_ticker[2] == day_tickers[0][2]:
                day_tickers.append(single_ticker) 
            else:
                day_count+=1
                ticker1=self.combine_multi_tickers(day_tickers,-1,check_time)
                is_up = self.is_up_direction(ticker1,check_time,direction_delta)*reverse_trade
                if not is_up == 0:
                   #ticker2=self.combine_multi_tickers(day_tickers,start_time,end_time)
                    ticker2, combi_stop, combi_take = self.combine_multi_tickers_slide(day_tickers,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema)

                    if ticker2:
                        if combi_take == 0 and combi_stop == 0:
                            tmp_profit = self.check_direction(ticker2, is_up, start_time, end_time, delta, stop_loss, take_profit)-1
                        elif combi_stop == 0:
                            tmp_profit = combi_take
                        elif combi_take == 0:
                            tmp_profit = combi_stop
                        if tmp_profit:
                            if tmp_profit>0: 
                                total_profit+=1
                            else: 
                                total_profit-=1
                            if not tmp_profit == 0:
                                tmp_profit-=self.comission/self.go
                            count_profit=count_profit+tmp_profit*self.go
                            procn_profit=procn_profit*(1+tmp_profit*self.go)
                            list_profit.append(tmp_profit)
                        else:
                            list_profit.append(float(0))
                            zero_days+=1
                    else:
                        list_profit.append(float(0))
                        zero_days+=1
                else:
                    zero_days+=1
                    list_profit.append(float(0))   
                day_tickers=[single_ticker]
        day_count+=1
        ticker1=self.combine_multi_tickers(day_tickers,-1,check_time)
        is_up = self.is_up_direction(ticker1,check_time,direction_delta)*reverse_trade
        if not is_up == 0:
            ticker2, combi_stop, combi_take = self.combine_multi_tickers_slide(day_tickers,start_time,end_time,stop_loss,take_profit,is_up,take_profit_schema)
            if ticker2:
                if combi_take == 0 and combi_stop == 0:
                    tmp_profit = self.check_direction(ticker2, is_up, start_time, end_time, delta, stop_loss, take_profit)-1
                elif combi_stop == 0:
                    tmp_profit = combi_take
                elif combi_take == 0:
                    tmp_profit = combi_stop
                if tmp_profit:
                    if tmp_profit>0: 
                        total_profit+=1
                    else: 
                        total_profit-=1
                    if not tmp_profit == 0:
                        tmp_profit-=self.comission/self.go
                    count_profit=count_profit+tmp_profit*self.go
                    procn_profit=procn_profit*(1+tmp_profit*self.go)
                    list_profit.append(tmp_profit)
                else:
                    list_profit.append(float(0))
                    zero_days+=1
            else:
                list_profit.append(float(0))
                zero_days+=1
        else:
            list_profit.append(float(0))
            zero_days+=1    
        day_tickers=[single_ticker]
        return total_profit, count_profit, procn_profit, list_profit, zero_days
    
    def main_analyzer(self, begin_list, check_list, start_list, end_list, date_start, date_end, stop_loss, direction_delta,take_profit, profit_method, results_days_dict, results_profit_dict, results_procent_dict, thread=0):
        #pythoncom.CoInitialize()
        results_days=[]
        results_profit=[]
        results_procent=[]
        delta=0
        
        results_days_dict[thread]=[]   
        results_profit_dict[thread]=[]         
        results_procent_dict[thread]=[]  
        
        #print "thread %s started: %s" % (thread,check_list)
        #for stop_loss in [0.005,0.001,0.015,0.02,0.05]:
        #    for direction_delta in [0.0015,0.005,0.01,0.02]:
        for begin in begin_list:
            for end in end_list:
                if begin < end:
                    filtered_tickers = self.filter_tickers(self.tickers, begin, end, date_start, date_end)
                    for check in check_list:
                        #print "thread %s check: %s" % (thread,check)
                        if begin < check and check < end:
                            for start in start_list:
                                if begin < check and check < start and start < end:
                                    if self.time_range.index(check) - self.time_range.index(begin) > 2 and self.time_range.index(end) - self.time_range.index(start) > 2:
                                        days,profit,procent,list_profit,zero_days=self.analyze_by_day(filtered_tickers, check, start, end, delta, direction_delta, stop_loss,1,take_profit,True, profit_method)
                                        days_rev,profit_rev,procent_rev,list_profit_rev,zero_days=self.analyze_by_day(filtered_tickers, check, start, end, delta, direction_delta, stop_loss,-1,take_profit,True, profit_method)
                                    else:
                                        days=0
                                        profit=1
                                        procent=1
                                        days_rev=0
                                        profit_rev=1
                                        procent_rev=1
                                        list_profit=[]
                                        list_profit_rev=[]
                                    results_days.append([days,begin,check,start,end,profit,procent,list_profit,stop_loss,direction_delta,1])
                                    results_profit.append([profit,begin,check,start,end,days,procent,list_profit,stop_loss,direction_delta,1])
                                    results_procent.append([procent,begin,check,start,end,days,profit,list_profit,stop_loss,direction_delta,1])
                                    results_days.append([days_rev,begin,check,start,end,profit_rev,procent_rev,list_profit_rev,stop_loss,direction_delta,-1])
                                    results_profit.append([profit_rev,begin,check,start,end,days_rev,procent_rev,list_profit_rev,stop_loss,direction_delta,-1])
                                    results_procent.append([procent_rev,begin,check,start,end,days_rev,profit_rev,list_profit_rev,stop_loss,direction_delta,-1])
        results_days_dict[thread]+=results_days   
        results_profit_dict[thread]+=results_profit 
        results_procent_dict[thread]+=results_procent
        del results_days
        del results_profit
        del results_procent
        
    def start_analyzer_threaded(self,day_start=-1,day_end=-1, threads = 16,direction_delta=0.0015,stop_loss=0.015, save_results = False, take_profit = 200, profit_method = "Nomathod"):
        start_time_range=self.time_range#[3:]
        thread_counter=threads
        thread_list={}
        results_days=[]
        results_profit=[]
        results_procent=[]
        manager = Manager()
        results_days_dict = manager.dict()
        results_profit_dict = manager.dict()
        results_procent_dict = manager.dict()
        for thread_num in range(thread_counter):
            thread_list[self.thread_index+thread_num] = Process(target=self.main_analyzer, name="t%s" % (self.thread_index+thread_num), args=[[self.time_range[0]], start_time_range[thread_num*len(start_time_range)/thread_counter:(thread_num+1)*len(start_time_range)/thread_counter], self.time_range, self.time_range[:-3], day_start, day_end, stop_loss, direction_delta, take_profit, profit_method, results_days_dict, results_profit_dict, results_procent_dict, self.thread_index+thread_num])
        #thread_list[self.thread_index+thread_counter] = Process(target=self.main_analyzer, name="t%s" % (self.thread_index+thread_counter), args=[[self.time_range[0]], start_time_range[len(start_time_range)/thread_counter*thread_counter:], self.time_range, self.time_range[:-3], day_start, day_end, stop_loss, direction_delta, take_profit, profit_method, results_days_dict, results_profit_dict, results_procent_dict, self.thread_index+thread_counter])
        
        for thread_num in range(thread_counter):
            try:
                thread_list[self.thread_index+thread_num].start()
                log.info("Thread %s started" % thread_num)
            except Exception as e:
                log.error("Exception in threading %s" % e)
            
        is_alive_counter=thread_counter
        while is_alive_counter>0:
            time.sleep(1)
            is_alive_counter=0
            for thread_num in range(thread_counter):
                if thread_list[self.thread_index+thread_num].is_alive():
                    is_alive_counter+=1
            print "alive %s" % is_alive_counter
        
        for thread_name in results_days_dict.keys():
            results_days+=results_days_dict[thread_name]
            results_profit+=results_profit_dict[thread_name]
            results_procent+=results_procent_dict[thread_name]
            del results_days_dict[thread_name]
            del results_profit_dict[thread_name]
            del results_procent_dict[thread_name]
            
        del results_days_dict
        del results_profit_dict
        del results_procent_dict 
        
        for thread_num in range(thread_counter):
            try:
                thread_list[self.thread_index+thread_num].join()
                del thread_list[self.thread_index+thread_num]
            except Exception as e:
                log.error("Exception in threading exit %s" % e)
                
        del manager
        del thread_list        
            
        results_days.sort()
        #log.info(results_days[0:20])
        #log.info(results_days[-22:])
        results_profit.sort()
        #log.info(results_profit[0:20])
        #log.info(results_profit[-22:])
        results_procent.sort()
        #log.info(results_procent[0:20])
        #log.info(results_procent[-22:])
        if save_results:
            self.results_days=results_days
            self.results_profit=results_profit
            self.results_procent=results_procent
        self.thread_index+=threads+1
        return results_days,results_profit,results_procent
    
    def start_analyzer(self,day_start=-1,day_end=-1,direction_delta=0.0015,stop_loss=0.015,day_of_week = -1):
        start_ind=0
        end_ind=0
        results_days=[]
        results_profit=[]
        results_procent=[]
        if day_start > -1:
            start_ind=self.days.index(day_start)
        if day_end > -1:
            end_ind=self.days.index(day_end)
            dayweek = self.get_day_week(day_end)
        for single_day in self.results_days:
            days=0
            profit=1
            procent=1
            ind_list= []
            if not day_end == -1: #or not self.allowed_times[dayweek] or [single_day[1],single_day[2],single_day[3],single_day[4]] in self.allowed_times[dayweek]:
                if len(single_day[7]) > 0 and not single_day[0] == 0:  
                    for ind in range(start_ind,end_ind+1,1):
                        if day_of_week < 0 or self.get_day_week(self.days[ind]) == day_of_week:
                            tmp_profit = single_day[7][ind]
                            ind_list.append(tmp_profit)
                            if single_day[7][ind] > 0:
                                days+=1
                            elif single_day[7][ind] < 0:
                                days-=1
                                
                            profit+=tmp_profit*self.go
                            procent=procent*(1+tmp_profit*self.go)
                        
    
                    results_days.append([days]+single_day[1:5]+[profit,procent]+[ind_list]+single_day[8:11])     
                    #results_days.append([days,single_day[1],single_day[2],single_day[3],single_day[4],profit,procent,single_day[7][start_ind:end_ind+1],stop_loss,direction_delta,single_day[10]])
                    #results_profit.append([profit,single_day[1],single_day[2],single_day[3],single_day[4],days,procent,single_day[7][start_ind:end_ind+1],stop_loss,direction_delta,single_day[10]])
                    #results_procent.append([procent,single_day[1],single_day[2],single_day[3],single_day[4],days,profit,single_day[7][start_ind:end_ind+1],stop_loss,direction_delta,single_day[10]])
                else:
                    results_days.append(single_day)
                #results_profit.append([profit,single_day[1],single_day[2],single_day[3],single_day[4],days,procent,[],stop_loss,direction_delta,single_day[10]])
                    #results_procent.append([procent,single_day[1],single_day[2],single_day[3],single_day[4],days,profit,[],stop_loss,direction_delta,single_day[10]])
        results_days.sort()
        #log.info(results_days[0:20])
        #log.info(results_days[-22:])
        #results_profit.sort()
        #log.info(results_profit[0:20])
        #log.info(results_profit[-22:])
        #results_procent.sort()
        #log.info(results_procent[0:20])
        #log.info(results_procent[-22:])
        
        return results_days
    
    def _timeline_appender(self, logic_key, result_candidate):
        timeline = []
        begin_cand_ind=self.time_range.index(result_candidate[1])
        check_cand_ind=self.time_range.index(result_candidate[2])
        start_cand_ind=self.time_range.index(result_candidate[3])
        ended_cand_ind=self.time_range.index(result_candidate[4])
        result_daily_array=numpy.array(result_candidate[7])
        result_daily_std = numpy.std(result_daily_array)
        try:
            if result_daily_std == 0:
                result_daily_std = 0.0000001
            if logic_key == "simple_profit":
                #if check_cand_ind - begin_cand_ind > 3 and ended_cand_ind - start_cand_ind > 2:
                timeline.append([result_candidate[6]]+result_candidate)
            if logic_key == "3_simple_profit":
                three_period_profit = 0
                if len(result_candidate[7]) > 3:
                    three_period_profit = (1+result_candidate[7][-1]*self.go)*(1+result_candidate[7][-2]*self.go)*(1+result_candidate[7][-3]*self.go)
                if three_period_profit > 1.1:
                    tmp_result_candidate = []
                    tmp_result_candidate+=result_candidate
                    #tmp_result_candidate[10]=-tmp_result_candidate[10]
                    timeline.append([three_period_profit]+tmp_result_candidate)
            if logic_key == "extra":
                if check_cand_ind - begin_cand_ind > 5 and check_cand_ind - begin_cand_ind < 17 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 5:
                    timeline.append([numpy.mean(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "extra2":
                if check_cand_ind - begin_cand_ind > 5 and check_cand_ind - begin_cand_ind < 17 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.mean(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "best_ranges":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([(float(result_candidate[0])*2)*(1/float(result_candidate[6]))]+result_candidate)
            if logic_key == "best_ranges2":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([(float(result_candidate[0]))*(float(result_candidate[6]))]+result_candidate)
            if logic_key == "percentile2":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.percentile(result_daily_array,80)]+result_candidate)
            if logic_key == "std_percentile":        
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([(result_candidate[0])*(result_candidate[5])*(result_daily_std)]+result_candidate)
            if logic_key == "median":                
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.median(result_daily_array)]+result_candidate)
            if logic_key == "anomality":                
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    stable_level = numpy.median(numpy.array(self._get_result_day_by_time(self.results_days, result_candidate[1], result_candidate[2], result_candidate[3], result_candidate[4],-1)[7]))
                    tmp_result_candidate = []
                    tmp_result_candidate+=result_candidate
                    #tmp_result_candidate[10]=-tmp_result_candidate[10]
                    timeline.append([stable_level-result_daily_array[-1]]+tmp_result_candidate)
            if logic_key == "percentile":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.percentile(result_daily_array,75)]+result_candidate)
            if logic_key == "std":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.mean(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "std_median":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([numpy.median(result_daily_array)/result_daily_std]+result_candidate)
            if logic_key == "extra_zero":
                if check_cand_ind - begin_cand_ind > 5 and check_cand_ind - begin_cand_ind < 17 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    timeline.append([math.sqrt(result_candidate[6])/result_candidate[6]]+result_candidate)
            if logic_key == "period_profit":
                if check_cand_ind - begin_cand_ind > 5 and start_cand_ind - check_cand_ind > 2 and ended_cand_ind - start_cand_ind > 2:
                    priod_len=len(result_candidate[7])
                    semi_period=int(math.sqrt(priod_len))
                    min_per_prof=200000000
                    for per_start in range(priod_len*2/semi_period-1):
                        semi_per_prof=1
                        for per_ind in range(semi_period):
                            semi_per_prof=semi_per_prof*(1+result_candidate[7][per_start*semi_period/2+per_ind]*self.go)
                        min_per_prof=min(min_per_prof,semi_per_prof)
                        tmp_result_candidate = []
                        tmp_result_candidate+=result_candidate
                        #tmp_result_candidate[10]=-tmp_result_candidate[10]
                    timeline.append([min_per_prof]+tmp_result_candidate) 
            if logic_key == "percentile_period_profit":
                period_profit = []
                for period_ind in range(len(result_candidate[7])/15):
                    tmp_per_profit=1
                    for inner_ind in range(period_ind*15,(period_ind+1)*15,1):
                        tmp_per_profit=tmp_per_profit*result_candidate[7][inner_ind]
                    period_profit.append(tmp_per_profit)
                    timeline.append([numpy.percentile(numpy.array(period_profit),75)]+result_candidate) 
        except Exception as e:
            log.info("Exception: %s" % e)
                
        return timeline        
    
    def real_trade_decisoner(self, results_days, results_profit, results_days_rev, results_profit_rev, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5):
        results_timeline_extra_days=[]
        results_timeline_extra_rev=[]
        results_timeline_extra2_days=[]
        results_timeline_extra2_rev=[]

        best_days=[]
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])

        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))

        for result_part in results_days:
            if result_part[0] >= days_limit:
                results_timeline_extra_days+=self._timeline_appender("extra",result_part)
                results_timeline_extra2_days+=self._timeline_appender("extra2",result_part)
                    
        best_days=[]
        for single_result in results_days_rev:
            if single_result[0]>0:
                best_days.append(single_result[0])
                
        if len(best_days) > 0:
            days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))
        else:
            days_limit=2000000
        print "Days limit %s" % days_limit
   
        for result_part in results_days_rev:
            if result_part[0] >= days_limit:
                results_timeline_extra_rev+=self._timeline_appender("extra",result_part)
                results_timeline_extra2_rev+=self._timeline_appender("extra2",result_part)

        results_timeline_extra_days.sort()
        results_timeline_extra_rev.sort()
        results_timeline_extra2_days.sort()
        results_timeline_extra2_rev.sort()
        log.info("get_best_ranges_profit_std_rev results_extra_day len %s" % len(results_timeline_extra_days))
        log.info("get_best_ranges_profit_std_rev results_extra_rev len %s" % len(results_timeline_extra_rev))
        log.info("get_best_ranges_profit_std_rev results_extra2_day len %s" % len(results_timeline_extra2_days))
        log.info("get_best_ranges_profit_std_rev results_extra2_rev len %s" % len(results_timeline_extra2_rev))

        trade_dir=0

        if len(results_timeline_extra_days) > 170:
            trade_dir=1
            log.info("Good day")
        #else:
        #    log.info("Bad day")
        #    trade_dir=0
        
        return trade_dir

    def get_best_ranges_new_gen_single_method(self, logic_key, results_days, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5, return_all = False, more = -940000, less=940000):
        results_timeline_days=[]

        #best_days=[]
        #for single_result in results_days:
        #    if single_result[0]>0:
        #        best_days.append(single_result[0])

        #if len(best_days) == 0:
        #    log.info("No best days found for %s" % logic_key)
        #    return [[160000, 160000, 160000, 160000,0]] 

        #days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))

        for result_part in results_days:
            #if result_part[0] >= -1000:
            results_timeline_days+=self._timeline_appender(logic_key,result_part)
                    
        results_timeline_days.sort()
        log.info("%s: results_day len %s" % (logic_key,len(results_timeline_days)))

        #if len(results_timeline_days) < max(abs(max_stat),period):
        #    log.info("No best range for %s" % logic_key)
        #    return [[160000, 160000, 160000, 160000,0]] 
        #if results_timeline_days[-20][0] > 2:
            #return None
            
        if max_stat < 0:
            result_timeline=results_timeline_days[max_stat:]
        else:
            result_timeline=results_timeline_days[:max_stat]
            
        if result_timeline[-1][0] <= more or result_timeline[-1][0] >= less:
            log.info("Weight %s with more %s and less %s for method %s" % (result_timeline[-1][0],more,less,logic_key))
            return [[160000, 160000, 160000, 160000,0]] 

        log.info("timeline %s: %s" % (logic_key,result_timeline))
        return self.get_candle_ranges_old(result_timeline,results_timeline_days,return_all)
    
    def get_best_ranges_new_gen(self, logic_key, results_days, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5, return_all = False, more = -94000000000, less=940000000000,limit_days = True):
        results_timeline_days=[]

        best_days=[]
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])

        if len(best_days) == 0:
            log.info("No best days found for %s" % logic_key)
            return [[160000, 160000, 160000, 160000,0]] 

        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))

        for result_part in results_days:
            if result_part[0] >= days_limit and limit_days:
                results_timeline_days+=self._timeline_appender(logic_key,result_part)
                    
        results_timeline_days.sort()
        #log.info("%s: results_day len %s" % (logic_key,len(results_timeline_days)))

        if len(results_timeline_days) < max(abs(max_stat),period):
            log.info("No best range for %s" % logic_key)
            return [[160000, 160000, 160000, 160000,0]] 
        #if results_timeline_days[-20][0] > 2:
            #return None
            
        if max_stat < 0:
            result_timeline=results_timeline_days[max_stat:]
        else:
            result_timeline=results_timeline_days[:max_stat]
            
        if result_timeline[-1][0] <= more or result_timeline[-1][0] >= less:
            log.info("Weight %s with more %s and less %s for method %s" % (result_timeline[-1][0],more,less,logic_key))
            return [[160000, 160000, 160000, 160000,0]] 

        #log.info("timeline %s: %s" % (logic_key,result_timeline))
        return self.get_candle_ranges_old(result_timeline,results_timeline_days,return_all)
        
    def get_best_ranges_double_period(self, logic_key, results_days, results_profit, period_days, period_profit, best_range = 2, weight_multiplyer=0.6, period = 10,max_stat = -5):
        results_timeline_days=[]
        results_timeline_period=[]

        best_days=[]
        for single_result in results_days:
            if single_result[0]>0:
                best_days.append(single_result[0])

        days_limit=int(numpy.median(numpy.array(best_days[-int(len(best_days)/best_range):])))

        for result_part in results_days:
            if result_part[0] >= days_limit:
                results_timeline_days+=self._timeline_appender(logic_key,result_part)
                    
        results_timeline_days.sort()
        log.info("%s: results_day len %s" % (logic_key,len(results_timeline_days)))

        if len(results_timeline_days) < max(abs(max_stat),period):
            log.info("No best range for %s" % logic_key)
            return [[160000, 160000, 160000, 160000,1]]
            #return None 
       
        if max_stat < 0:
            result_timeline=results_timeline_days[:-max_stat]
        else:
            result_timeline=results_timeline_days[-max_stat:]

        for single_result in result_timeline:
            find_candle = self._find_candle_in_ranges(period_days,single_result[2],single_result[3],single_result[4],single_result[5],-1)
            if find_candle:
                results_timeline_period+=self._timeline_appender(logic_key,find_candle)
                    
        results_timeline_period.sort()
        
        
        result_to_return = [[160000, 160000, 160000, 160000,1]]
        max_diff=-1
        for single_result in result_timeline:
            weight_coeff=single_result[0]/results_timeline_days[-1][0]
            find_candle = self._find_candle_in_ranges(results_timeline_period,single_result[2],single_result[3],single_result[4],single_result[5])
            if find_candle and max_diff < find_candle[0]:#/results_timeline_period[-1][0]:
                max_diff = find_candle[0]#/results_timeline_period[-1][0]
                result_to_return = [[find_candle[2],find_candle[3],find_candle[4],find_candle[5],find_candle[6]]]
        
        return result_to_return
    
    def set_allowed_times(self, result_profit,dayweek):
        for single_result in result_profit:
            self.allowed_times[dayweek].append([single_result[1],single_result[2],single_result[3],single_result[4]])
        log.info("For day %s allowed times %s"  % (dayweek,self.allowed_times[dayweek]))

    def get_ranges_by_dayweek(self,curr_date):
        day_of_week =  self.get_day_week(curr_date)
        day_ranges={0:[160000, 160000, 160000, 160000,1],
                    1:[94000, 114000, 120000, 135000, 1, 0, 0.01, 0.005, 'simple'],
                    2:[94000, 101000, 103000, 112000, -1, 0, 0.0075, 0.01, 'simple'],
                    3:[94000, 115000, 135000, 152000, -1, 0, 0.0075, 0.01, 'simple'],
                    4:[94000, 101000, 102000, 133000, -1, 0, 0.01, 0.005, 'simple'],
                    5:[160000, 160000, 160000, 160000,1],
                    6:[160000, 160000, 160000, 160000,1]}
        
        return [day_ranges[day_of_week]]

    def get_ranges_by_dayweek_new(self,curr_date):
        day_of_week = self.get_day_week(curr_date)
        day_ranges={0:[160000, 160000, 160000, 160000,1],
                    1:[94000, 114000, 120000, 135000, 1, 0, 0.01, 0.0075, 'take_equity_0.0025'],
                    2:[94000, 102000, 103000, 112000, -1, 0.0075, 0.0075, 0.001, 'take_equity_0.0025'],
                    3:[94000, 124000, 125000, 144000, 1, 0.005, 0.003, 0.001, 'take_equity_0.0075'],
                    4:[94000, 101000, 102000, 132000, -1, 0, 0.005, 0.003, 'take_equity_0.0025'],
                    5:[160000, 160000, 160000, 160000,1],
                    6:[160000, 160000, 160000, 160000,1]}
        
        return [day_ranges[day_of_week]]

    def get_day_profit_old(self, curr_date, period = 30,period2 = 30,simulate_trade=True,delta=0.005,loss=0.015):
        used_ranges=[]
        ranges_counter=0
        profit_delta=0.25
        procent_delta=1.25
        trade_dir=1
        day_profit_list=[]
        day_count_list=[]
        day_procent_list=[]
        day_list_profit_list=[]
        trade_direction_list=[]
        results_days=[]
        results_profit=[]
        results_procent=[]
        results_days_rev=[]
        results_profit_rev=[]
        results_procent_rev=[]
        results_days_dir=[]
        results_profit_dir=[]
        results_procent_dir=[]
        thread_period_dict={"0":2,"1":2,"2":2,"3":2,"5":3,"10":4,"15":5,"30":6,"60":7,"180":12}
        if "%s" % period in thread_period_dict.keys():
            thread_count = thread_period_dict["%s" % period]
        else:
            thread_count = 16
        curr_date_pos=self.days.index(curr_date)
        log.info("Get day profit %s" % curr_date)
        if curr_date_pos <= period or curr_date_pos <= period2*5:
            return [-1], [-1], [-1], []
        
        day_of_week = self.get_day_week(curr_date)
        if day_of_week > 4:
            log.info("Let's skip weekend day %s" % curr_date)
            return [-1], [-1], [-1], []
        
        if not self.results_days:
            self.start_analyzer_threaded(-1,-1,16,delta,loss,save_results = True,take_profit = 2, profit_method = "take_innsta_0.01")
        
        period_day_tickers = self.filter_tickers(self.tickers, 94000,160000,self.days[curr_date_pos-period-1],self.days[curr_date_pos-1])
        results_days_all = self.start_analyzer(self.days[curr_date_pos-period-1],self.days[curr_date_pos-1],delta,loss)

        success_day_counter=0
        reverse_day_counter=0
        for result in results_days_all:
            if result[10] == 1:
                results_days_dir.append(result)
                if result[6] > 1:
                    success_day_counter+=1
            else:
                if result[6] > 1:
                    reverse_day_counter+=1
                results_days_rev.append(result)
        log.info("Success periods %s" % success_day_counter)
        log.info("Reverse periods %s" % reverse_day_counter)
        self.success_ranges.append(success_day_counter)
        if len(self.success_ranges) > 1:
            if success_day_counter - self.success_ranges[-2] > 2000:
                log.info("Too big increase of success ranges %s" % (success_day_counter - self.success_ranges[-2]))
                #return [-1], [-1], [-1], []

        if self.get_ranges_by_dayweek(curr_date)[0][4] == 1:
            results_days=results_days_dir
        else:
            results_days=results_days_rev
  
        best_ranges1 = self.get_best_ranges_new_gen("median",results_days, 8,0.6,period,-5)
        best_ranges2 = self.get_best_ranges_new_gen("extra2",results_days, 8,0.6,period,-5)
        best_ranges3 = self.get_best_ranges_new_gen("simple_profit",results_days, 8,0.6,period,-5)
        best_ranges4 = self.get_best_ranges_new_gen("std",results_days, 8,0.6,period,-5)
        best_ranges5 = self.get_best_ranges_new_gen("std_median",results_days, 8,0.6,period,-5)
        best_ranges6 = self.get_best_ranges_new_gen("extra",results_days, 8,0.6,period,-5)
        best_ranges7 = self.get_best_ranges_new_gen("best_ranges",results_days,8,0.6,period,-5)
        best_ranges8 = self.get_best_ranges_new_gen("period_profit",results_days, 8,0.6,period,-1)
        best_ranges9 = self.get_ranges_by_dayweek(curr_date)
        best_ranges10 = self.get_ranges_by_dayweek_new(curr_date)
        if not best_ranges1 or not best_ranges2 or not best_ranges3 or not best_ranges4 or not best_ranges5 or not best_ranges6 or not best_ranges7 or not best_ranges8:
            log.info("No some best ranges, lets skip")
            return [-1], [-1], [-1], []
        best_ranges = best_ranges1 + best_ranges2 + best_ranges3 + best_ranges4 + best_ranges5 + best_ranges6 + best_ranges7 + best_ranges8+best_ranges9+best_ranges10

        for tmp_delta, tmp_loss, tmp_prof,take_schema in [[delta, loss, 2,"Noschema"],[delta, loss, 2,"simple"],[delta, loss, 2,"take_innsta_0.01"],[delta, loss,  2, 'take_atrts_0.0075']]: #[[delta, loss, 200],[0.0015, loss, 200],[0.0015, 0.015, 200],[0.005, 0.02, 200]]:
            for best_range in best_ranges:
                real_delta = tmp_delta
                real_loss = tmp_loss
                real_prof = tmp_prof
                real_schema = take_schema
                ranges_counter+=1
                begin_time,check_time,start_time,end_time = best_range[0], best_range[1], best_range[2], best_range[3]
                if len(best_range) > 5:
                    real_delta = best_range[5]
                    real_loss = best_range[6]
                    real_prof = best_range[7]
                    real_schema = best_range[8]
                    used_ranges.append(best_range)
                else:
                    used_ranges.append(best_range+[real_delta, real_loss, real_prof, real_schema])    
                #day_profit, day_count, day_procent, day_list_profit = self.analyze_by_day(period_day_tickers, check_time, start_time, end_time, 0, tmp_delta, tmp_loss, best_range[4], tmp_prof, True)
                #log.info("Period %s: day_profit %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                log.info("Begin %s, check %s, start %s, end %s,trade direct %s" % (begin_time,check_time,start_time,end_time,best_range[4]))
                if simulate_trade:
                    day_tickers = self.filter_tickers(self.tickers, begin_time,end_time,curr_date,curr_date)
                    day_profit, day_count, day_procent, day_list_profit,zero_day = self.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, real_delta, real_loss, best_range[4], real_prof, True,real_schema)
                    day_profit_list.append(day_profit)
                    day_count_list.append(day_count)
                    log.info("day_profit %s %s, day_count %s, day_procent %s" % (ranges_counter,day_profit, day_count, day_procent))
                    trade_direction_list.append(best_range[4])
                else:
                    day_profit_list.append(0)
                    day_count_list.append(1)
                    log.info("day_profit %s, day_count %s, day_procent %s" % (0, 1, 1))
                    trade_direction_list.append(1)
            
        return day_profit_list, day_count_list,trade_direction_list,used_ranges

    def robot(self, date_start=-1, period = 10, period2 = 0, day_end = -1, delta = 0.0015, loss = 0.015):
        self.tickers = self.filter_tickers(self.tickers, 94000,160000,-1,-1)
        best_prof=0.7
        max_prof=1.3
        methods_list=[29]
        changer_period=3
        if date_start > 0:
            date_start_index=self.days.index(date_start)
            """for i in range(10):
                reserv_tickers=[]
                results_procent_dir=[]
                results_procent_rev=[]
                reserv_tickers+=self.tickers
                curr_date=self.days[date_start_index-i]
                dayweek = self.get_day_week(curr_date)
                if not self.allowed_times[dayweek]:
                    self.tickers=self.filter_tickers(self.tickers, 94000,160000,-1,-1,dayweek)
                    results_days_all,results_profit_all,results_procent_all = self.start_analyzer_threaded(-1,-1,4,delta,loss)
                    for result in results_procent_all:
                        if result[10] == 1:
                            results_procent_dir.append(result)
                        else:
                            results_procent_rev.append(result)
                    if self.get_ranges_by_dayweek(curr_date)[0][4] == 1:
                        results_procent=results_procent_dir
                    else:
                        results_procent=results_procent_rev
                    self.set_allowed_times(results_procent[-50:],dayweek)
                    self.tickers=reserv_tickers
                    del reserv_tickers
                    del results_procent_all
                    del results_procent_dir
                    del results_procent_rev
                    del results_days_all
                    del results_profit_all"""
            self.days=self.days[-len(self.days)+date_start_index-max(period,period2*5)-1:]
        if day_end > 0 and day_end not in self.days:
            self.days.append(day_end)

        #check
        for day in self.days:
            day_got=0
            for ticker in self.tickers:
                if ticker[3] == 95000 and ticker[2]==day:
                    day_got = 1
            if day_got == 0:
                log.info("No start tickers found for day %s" % day)

        total_profit_list=[]
        total_profit = []
        total_count = []
        total_procent_profit = []
        total_extra_profit = []
        saved_times=[]
        for single_day in self.days:
            if day_end < 0 or day_end > single_day:
                day_analyze_time_start=time.time()
                day_profit_list, day_count_list,trade_direction_list,used_ranges=self.get_day_profit_old(single_day, period,period2,delta=delta,loss=loss)
                if len(total_profit_list) > changer_period:           
                    accumul_prof=1
                    tmp_best_prof=best_prof
                    if len(day_count_list) > 18: 
                        for saved_prof_ind in range(min(len(day_count_list),40)):
                            method_per_prof=1
                            for prev_profit in range(changer_period):
                                method_per_prof=method_per_prof*total_profit_list[-prev_profit-1][saved_prof_ind]
                            log.info("TotalProfit method %s: %s with day profit %s" % (saved_prof_ind,method_per_prof,day_count_list[saved_prof_ind]))
                            if method_per_prof > tmp_best_prof:
                                #if method_per_prof > 1.9 and saved_prof_ind in [0,2]:
                                #    accumul_prof = 1
                                #    break
                                if saved_prof_ind in methods_list and method_per_prof < max_prof: #[0,8,10,14]
                                    log.info("Let's use method %s with times %s" % (saved_prof_ind,used_ranges[saved_prof_ind]))
                                    tmp_best_prof = method_per_prof
                                    accumul_prof = day_count_list[saved_prof_ind]
                                    saved_times=used_ranges[saved_prof_ind]
                        day_count_list.append(accumul_prof)
                    day_profit_list.append(0) 
                    if accumul_prof > 1:
                        day_profit_list[-1] = 1
                    elif accumul_prof < 1:
                        day_profit_list[-1] = -1
                    trade_direction_list.append(1)  
                if len(total_profit) <= len(day_profit_list) and len(day_profit_list) > 1:
                    for check_func in range(min(len(day_profit_list),len(day_count_list))):
                        day_count=day_count_list[check_func]
                        day_profit=day_profit_list[check_func]
                        if len(total_profit)<check_func+1:
                            total_profit.append(1)
                            total_count.append(0)
                            total_procent_profit.append(1)
                            total_extra_profit.append(1)
                        if day_count > 0:
                                log.info("Date %s, profit %s, count %s" % (single_day, day_profit, day_count))
                                total_profit[check_func]=total_profit[check_func]+(day_count-1)
                                total_procent_profit[check_func] = total_procent_profit[check_func]*day_count
                                total_count[check_func]+=day_profit
                                total_extra_profit[check_func]=max(total_extra_profit[check_func]-round(total_extra_profit[check_func]/2)+round(total_extra_profit[check_func]/2)*day_count,1)
                        log.info("Method %s!!! Total profit %s, total procent profit %s, total count %s, total extra profit %s,time %s" % (check_func,total_profit[check_func],total_procent_profit[check_func],total_count[check_func], total_extra_profit[check_func], time.time()-day_analyze_time_start))
                    if len(day_profit_list) > 1:
                        total_profit_list.append(day_count_list)
        if day_end > 0:            
            saved_times=None
            day_analyze_time_start=time.time()
            day_profit_list, day_count_list,trade_direction_list,used_ranges=self.get_day_profit_old(day_end, period,period2,simulate_trade=False,delta=delta,loss=loss)
            if len(total_profit_list) > changer_period:           
                accumul_prof=1
                tmp_best_prof=best_prof
                if len(day_count_list) > 18: 
                    for saved_prof_ind in range(min(len(day_count_list),40)):
                        method_per_prof=1
                        for prev_profit in range(changer_period):
                            method_per_prof=method_per_prof*total_profit_list[-prev_profit-1][saved_prof_ind]
                        log.info("TotalProfit method %s: %s with day profit %s" % (saved_prof_ind,method_per_prof,day_count_list[saved_prof_ind]))
                        if method_per_prof > tmp_best_prof:
                            if saved_prof_ind in methods_list and method_per_prof < max_prof: #[0,8,10,14]
                                log.info("Let's finally use method %s with times %s" % (saved_prof_ind,used_ranges[saved_prof_ind]))
                                tmp_best_prof = method_per_prof
                                accumul_prof = day_count_list[saved_prof_ind]
                                saved_times=used_ranges[saved_prof_ind]
                day_count_list.append(accumul_prof)
                day_profit_list.append(0) 
                if accumul_prof > 1:
                    day_profit_list[-1] = 1
                elif accumul_prof < 1:
                    day_profit_list[-1] = -1
                trade_direction_list.append(1)  
            if len(total_profit) <= len(day_profit_list) and len(day_profit_list) > 1:
                for check_func in range(min(len(day_profit_list),len(day_count_list))):
                    day_count=day_count_list[check_func]
                    day_profit=day_profit_list[check_func]
                    if len(total_profit)<check_func+1:
                        total_profit.append(1)
                        total_count.append(0)
                        total_procent_profit.append(1)
                        total_extra_profit.append(1)
                    if day_count > 0:
                        #if trade_direction > 0:
                            log.info("Date %s, profit %s, count %s" % (day_end, day_profit, day_count))
                            total_profit[check_func]=total_profit[check_func]+(day_count-1)
                            total_procent_profit[check_func] = total_procent_profit[check_func]*day_count
                            total_count[check_func]+=day_profit
                            total_extra_profit[check_func]=max(total_extra_profit[check_func]-round(total_extra_profit[check_func]/2)+round(total_extra_profit[check_func]/2)*day_count,1)
                    log.info("Method %s!!! Total profit %s, total procent profit %s, total count %s, total extra profit %s,time %s" % (check_func,total_profit[check_func],total_procent_profit[check_func],total_count[check_func], total_extra_profit[check_func], time.time()-day_analyze_time_start))
                if len(day_profit_list) > 1:
                    total_profit_list.append(day_count_list)
        return [saved_times]

if __name__ == "__main__":
    start_timer=time.time()
    pa = ProfileAnalyser("US1.BAC_160104_170630.txt")
    #begin_time,check_time,start_time,end_time = 100000, 111000, 130000, 173000
    #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20170630,20170630)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20150705,20160104)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20160104,20160705)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20160705,20170104)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20170104,20170506)
    #print pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, 0.01,0.015,1)
    #print pa.analyze_by_day(day_tickers, 115000, 120000, 124000, 0, 0,0,-1)
    #print pa.analyze_by_day(day_tickers, 115000, 121000, 141000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 115000, 141000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 122000, 141000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 121000, 140000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 114000, 121000, 135000, 0, 0.0005,0.015,1)
    #print pa.analyze_by_day(day_tickers, 125000, 141000, 165000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 143000, 175000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 144000, 175000, 0, 0.0015)
    #print pa.analyze_by_day(pa.tickers, 111000, 142000, 175000, 0, 0.0015)
    #log.info(pa.robot(-1,5,delta=0,loss=0.015))
    #print pa.start_analyzer_threaded()
    #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000)
    #log.info( pa.analyze_by_day(day_tickers, 111000, 143000, 180000, 0, 0.0015))
    #dates=[20150105,20150401,20150701,20151001,20160101,20160401,20160701,20161001,20170101,20170505]
    #for sdi in range(len(dates)-2):
    """best_results = []
    for weekday in [0,1,2,3,4]:
        log.info("New day")
        for delta in [0,0.0015,0.003,0.005,0.0075,0.01,0.015]:
            for loss in [0,0.0015,0.003,0.005,0.0075,0.01,0.015,0.02]:
                log.info("delta %s, stop %s" % (delta, loss))
                pa = ProfileAnalyser("US1.C_160104_170630.txt")
                day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,-1,-1,weekday)
                pa.tickers = day_tickers
                results_days=[]
                results_profit=[]
                results_procent=[]
                results_days_rev=[]
                results_profit_rev=[]
                results_procent_rev=[]
                results_days_dir=[]
                results_profit_dir=[]
                results_procent_dir=[]
                #spec_dates_list=[20150105,20150705,20160104,20160705,20170104,20170506,20170506]
                spec_dates_list=[-1,-1]
                for tmpdate in range(len(spec_dates_list)-1):
                    results_days=[]
                    results_profit=[]
                    results_procent=[]
                    results_days_rev=[]
                    results_profit_rev=[]
                    results_procent_rev=[]
                    results_days_dir=[]
                    results_profit_dir=[]
                    results_procent_dir=[]
                    results_days_all, results_profit_all, results_procent = pa.start_analyzer_threaded(day_start=spec_dates_list[tmpdate],day_end=spec_dates_list[tmpdate+1],threads=16,direction_delta=delta,stop_loss=loss)

                    for result in results_days_all:
                        if result[10] == 1:
                            results_days_dir.append(result)
                        else:
                            results_days_rev.append(result)
                    for result in results_profit_all:
                        if result[10] == 1:
                            results_profit_dir.append(result)
                        else:
                            results_profit_rev.append(result)
                    for single_result in results_procent[-5:]:
                        best_results.append([single_result[0],single_result[5],delta,loss])
                        log.info(single_result)
                    for logic_key in ["best_ranges2","simple_profit"]: #["std","extra","extra2","median","std_median","period_profit","percentile","simple_profit"]:
                        ranges = pa.get_best_ranges_new_gen(logic_key,results_days_all, 8,0.6,5,-10, return_all = True)
                        if ranges:
                            for single_range in ranges:
                                begin_time,check_time,start_time,end_time,trade = single_range
                                log.info("Time %s" % logic_key)
                                log.info( "%s, %s, %s, %s" % (begin_time,check_time,start_time,end_time))

                                log.info( "Result %s" % logic_key)
                                day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,spec_dates_list[tmpdate],spec_dates_list[tmpdate+1])
                                log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,trade))
                                #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20150105,20150705)
                                #log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,trade))
                                #day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20150705,20160104)
                                #log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,trade))
                                day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20160104,20160705)
                                log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,trade))
                                day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20160705,20170104)
                                log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,trade))
                                day_tickers = pa.filter_tickers(pa.tickers, 94000,160000,20170104,20170506)
                                log.info(pa.analyze_by_day(day_tickers, check_time, start_time, end_time, 0, delta, loss,trade))
                del pa
                del day_tickers
                del results_days
                del results_profit
                del results_procent
                del results_days_rev
                del results_profit_rev
                del results_procent_rev
                del results_days_dir
                del results_profit_dir
                del results_procent_dir
    best_results.sort()
    log.info(best_results)"""
    log.info( time.time()-start_timer)
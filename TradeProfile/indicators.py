'''
Created on 19 aug 2017 

@author: Kurliana
'''
import numpy

class TradeIndicators():
    
    def __init__(self, all_tickers):
        self.all_tickers=all_tickers
        
    def _get_pvv_sign(self,ticker,prev_sign):
        #if abs(ticker[4]-ticker[7]) >= 0.5*abs(ticker[5]-ticker[6]):
        """ N/B this is finally resolved config
        if abs(ticker[5]-ticker[7]) > abs(ticker[7]-ticker[6]):
            sign=-1
        else:
            sign=1
        """
        #if abs(ticker[4]-ticker[7]) >= 0.5*abs(ticker[5]-ticker[6]):
        if abs(ticker[5]-ticker[7]) > abs(ticker[7]-ticker[6]):
            sign=-1
        else:
            sign=1
        #else:
        #    sign=0
        """else:
            #if abs(ticker[5]-max(ticker[4],ticker[7])) > abs(min(ticker[4],ticker[7])-ticker[6]):
            if abs(ticker[5]-ticker[7]) > abs(ticker[7]-ticker[6]):
                if ticker[4] > ticker[7]:
                    sign=0
                else:
                    sign=0
            else:
                if ticker[4] <= ticker[7]:
                    sign=0
                else:
                    sign=0"""
                    
        return sign
    
    def _get_skating_mean_old(self, index_arr):
        skating_plus = 0
        skating_minus = 0
        for ind in range(len(index_arr)-1,-1,-1):
            if index_arr[ind] > 0:
                skating_plus+=1
            elif index_arr[ind] < 0:
                skating_minus+=1
            if skating_plus > len(index_arr)/2:
                return abs(index_arr.mean())
            if skating_minus > len(index_arr)/2:
                return -abs(index_arr.mean())
        return 0
    
    def _get_skating_mean_weight(self, index_arr):
        skating=0
        for ind in range(len(index_arr)-1):
            skating=0.3*skating+0.7*index_arr[ind]
        return skating

    def _get_skating_mean(self, index_arr):
        skating=0
        min_value=999999999999999999
        max_value=0
        for ind in range(len(index_arr)-1):
            if index_arr[ind][5] > max_value:
                max_value = index_arr[ind][5]
            if index_arr[ind][6] < min_value:
                min_value = index_arr[ind][6]
        if abs(max_value-index_arr[-1][7]) > abs(index_arr[-1][7]-min_value):
            skating=-1
        else:
            skating=1


        return skating
            
    def getATR(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        interval=kwargs.get("interval",14)
        ATR_list=[]
        TrueRangeList=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            TrueRangeList.append(max(single_ticker[5]-single_ticker[6],abs(tickers[single_ticker_id-1][7]-single_ticker[5]),abs(tickers[single_ticker_id-1][7]-single_ticker[6])))
        TrueRangeList=numpy.array(TrueRangeList)
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if single_ticker_id < interval:
                ATR_list.append(float(0))
            else:
                ATR_list.append(numpy.mean(TrueRangeList[single_ticker_id-interval+1:single_ticker_id+1]))
                #ATR_list.append(numpy.mean(TrueRangeList))
        return ATR_list
    
    def getEMA(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        interval=kwargs.get("interval",14)
        alpha=(2.0/(interval+1))
        EMA_list=[]
        PriceList=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            PriceList.append(single_ticker[7])
        PriceList=numpy.array(PriceList)
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if single_ticker_id < interval:
                EMA_list.append(float(0))
            elif single_ticker_id == interval:
                EMA_list.append(numpy.mean(PriceList[:interval+1]))
            else:
                EMA_list.append(alpha*PriceList[single_ticker_id]+(1-alpha)*EMA_list[-1])
        return EMA_list

    def getPVV(self,**kwargs):
        sign=0
        prev_sign=0
        tickers=kwargs.get("tickers",[])
        interval=kwargs.get("interval",14)
        alpha=(2.0/(interval+1))
        PVV_list=[]
        PVV_list2=[]
        PVV_rel=[]
        PVV_rel2=[]
        tmp_pvv_list=[]
        tmp_pvv_list2=[]
        volume_list=[]
        for single_ticker in tickers:
            med_price=(single_ticker[4]+single_ticker[5]+single_ticker[6]+single_ticker[7])/4
            #price_max_diff=(single_ticker[5]-single_ticker[6])/med_price
            #price_tot_diff=(single_ticker[7]-single_ticker[4])/med_price
            volume_list.append(single_ticker[8])
            prev_sign=sign
            sign = self._get_pvv_sign(single_ticker,prev_sign)
            #if single_ticker[7] >= single_ticker[4]:
            #    tmp_pvv_list.append((single_ticker[5]-single_ticker[6]+abs(single_ticker[7]-single_ticker[4]))/(2*med_price))
            #else:
            #    tmp_pvv_list.append(-(single_ticker[5]-single_ticker[6]+abs(single_ticker[7]-single_ticker[4]))/(2*med_price))
            #if single_ticker[4] < (single_ticker[5]+single_ticker[6])/2 and single_ticker[7] > (single_ticker[5]+single_ticker[6])/2 and single_ticker[7] > single_ticker[4]:
            #    tmp_pvv_list.append(((single_ticker[5]-single_ticker[6])+abs(single_ticker[7]-single_ticker[4]))*(single_ticker[7]-single_ticker[4])/single_ticker[7])
            #elif single_ticker[4] > (single_ticker[5]+single_ticker[6])/2 and single_ticker[7] < (single_ticker[5]+single_ticker[6])/2 and single_ticker[7] < single_ticker[4]:
            #    tmp_pvv_list.append(((single_ticker[5]-single_ticker[6])+abs(single_ticker[7]-single_ticker[4]))*(single_ticker[7]-single_ticker[4])/single_ticker[7])
            #else:
            #    tmp_pvv_list.append(0)
            tmp_pvv_list2.append(sign*((single_ticker[5]-single_ticker[6])+abs(single_ticker[7]-single_ticker[4]))*abs(single_ticker[7]-single_ticker[4])/single_ticker[7])
            full_move=max(0,single_ticker[5]-max(single_ticker[7],single_ticker[4]))*2+max(0,min(single_ticker[7],single_ticker[4])-single_ticker[6])*2+abs(single_ticker[7]-single_ticker[4])
            if abs(single_ticker[7]-single_ticker[4]) > 0:
                #tmp_pvv_list.append((single_ticker[7]-single_ticker[4])/((single_ticker[8]*abs(single_ticker[7]-single_ticker[4])/full_move)))
                tmp_pvv_list.append(sign/(single_ticker[8]/full_move))
            else:
                tmp_pvv_list.append(0)
            
        volume_list=numpy.array(volume_list)
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if single_ticker_id < interval:
                PVV_list.append(float(0))
                PVV_list2.append(float(0))
            else:
                #PVV_list.append((tmp_pvv_list[single_ticker_id]*single_ticker[8])/numpy.mean(volume_list[single_ticker_id-interval+1:single_ticker_id+1]))
                PVV_list.append(tmp_pvv_list[single_ticker_id])
                PVV_list2.append(tmp_pvv_list2[single_ticker_id])

        PVV_list=numpy.array(PVV_list)      
        PVV_list2=numpy.array(PVV_list2) 
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if single_ticker_id < interval:
                PVV_rel.append(float(0))
                PVV_rel2.append(float(0))
            #elif single_ticker_id == interval:
             #   PVV_list2.append(numpy.mean(PVV_list[:interval+1]))
            else:
                #PVV_list2.append(alpha*PVV_list[single_ticker_id]+(1-alpha)*PVV_list[-1])
                #/PVV_list[single_ticker_id-1])
                #PVV_list2.append(numpy.mean(PVV_list[single_ticker_id-interval+1:single_ticker_id+1]))
                pvlist_cut=numpy.array(PVV_list[single_ticker_id-interval+1:single_ticker_id+1])
                #PVV_rel.append(abs(PVV_list[single_ticker_id])/pvlist_cut.mean())
                #pvlist_cut=numpy.array(PVV_list2[single_ticker_id-interval+1:single_ticker_id+1])
                if not PVV_list2[single_ticker_id] == 0:
                    PVV_rel2.append(PVV_list2[single_ticker_id]/abs(PVV_list2[single_ticker_id]))
                else:
                    PVV_rel2.append(0)
                PVV_rel.append(numpy.mean(PVV_list[single_ticker_id-interval+1:single_ticker_id+1]))
                #PVV_rel.append(self._get_skating_mean(tickers[single_ticker_id-interval+1:single_ticker_id+1]))
                #PVV_rel2.append((pvlist_cut.sum()-pvlist_cut.min()-pvlist_cut.max())/(interval-2))#*abs(single_ticker[7]-single_ticker[4]))#/abs(single_ticker[7]-single_ticker[4]))#/single_ticker[7])
                #PVV_rel.append(numpy.mean(volume_list[single_ticker_id-interval+1:single_ticker_id+1])/numpy.sum(volume_list[single_ticker_id-interval+1:single_ticker_id+1]))
                #PVV_list2.append(PVV_list[single_ticker_id]/abs(numpy.mean(PVV_list[single_ticker_id-interval+1:single_ticker_id])))
                #PVV_list2.append(numpy.sum(PVV_list[single_ticker_id-interval+1:single_ticker_id+1])/abs(numpy.sum(PVV_list[single_ticker_id-interval*2+1:single_ticker_id-interval+1])))

        return PVV_rel, PVV_rel2
    
    def getVWAP(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        VWAP_list=[]
        sum_volume=0
        sum_volume_price=0
        day_str = 0
        for single_ticker in tickers:
            if single_ticker[2] == day_str:
                sum_volume+=single_ticker[8]
                sum_volume_price+=single_ticker[8]*(single_ticker[4]+single_ticker[5]+single_ticker[6]+single_ticker[7])/4
            else:
                day_str = single_ticker[2]
                sum_volume=single_ticker[8]
                sum_volume_price=single_ticker[8]*(single_ticker[4]+single_ticker[5]+single_ticker[6]+single_ticker[7])/4
            VWAP_list.append(sum_volume_price/sum_volume)

        return VWAP_list
    
    def getVWMA(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        interval=kwargs.get("interval",14)
        VWMA_list=[]
        VolumePriceList=[]
        VolumeList=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            VolumePriceList.append(single_ticker[8]*(single_ticker[4]+single_ticker[5]+single_ticker[6]+single_ticker[7])/4)
            VolumeList.append(single_ticker[8])
        VolumePriceList=numpy.array(VolumePriceList)
        VolumeList=numpy.array(VolumeList)
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if single_ticker_id < interval:
                VWMA_list.append(float(0))
            else:
                VWMA_list.append(numpy.sum(VolumePriceList[single_ticker_id-interval+1:single_ticker_id+1])/numpy.sum(VolumeList[single_ticker_id-interval+1:single_ticker_id+1]))
        return VWMA_list
    
    def getEVWMA(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        interval=kwargs.get("interval",14)
        EVWMA_list=[]
        VolumeList=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            VolumeList.append(single_ticker[8])
        VolumeList=numpy.array(VolumeList)    
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if single_ticker_id <= interval:
                EVWMA_list.append(single_ticker[7])
            else:
                alpha = numpy.mean(VolumeList[single_ticker_id-interval+1:single_ticker_id])*interval
                EVWMA_list.append(((alpha-VolumeList[single_ticker_id])*EVWMA_list[-1]+VolumeList[single_ticker_id]*single_ticker[7])/alpha)
        return EVWMA_list    
    
    def getATRTrailingStop_real(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        multiplyer=kwargs.get("multiplyer",3)
        retries=kwargs.get("retries",0)
        curr_retry=0
        ATRTS_list=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            ATR=0
            if "ATR" in single_ticker[9].keys():
                PVV=single_ticker[9]["ATR"]
                #VOL=single_ticker[9]["PVVREL"]
                if multiplyer > 0:
                    ATR=PVV*multiplyer
                else:
                    ATR=0
            if not ATRTS_list:
                ATRTS_list.append(single_ticker[5]-ATR)
            else:
                if ATRTS_list[-1] < tickers[single_ticker_id-1][6]: # upstream
                    if single_ticker[6] > ATRTS_list[-1]: #upstream continue
                        #curr_retry=0
                        ATRTS_list.append(max(ATRTS_list[-1],single_ticker[5]-ATR))
                    else:
                        if curr_retry < retries:
                            curr_retry+=1
                            ATRTS_list.append(max(ATRTS_list[-1],single_ticker[5]-ATR))
                        else:
                            curr_retry=0
                            ATRTS_list.append(single_ticker[6]+ATR)
                else: # downsteam
                    if single_ticker[5] < ATRTS_list[-1]: #downsteam continue
                        #curr_retry=0
                        ATRTS_list.append(min(ATRTS_list[-1],single_ticker[6]+ATR))
                    else:
                        if curr_retry < retries:
                            curr_retry+=1
                            ATRTS_list.append(min(ATRTS_list[-1],single_ticker[6]+ATR))
                        else:
                            curr_retry=0
                            ATRTS_list.append(single_ticker[5]-ATR)
        return ATRTS_list

    def getATRTrailingStop(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        multiplyer=kwargs.get("multiplyer",3)
        retries=kwargs.get("retries",0)
        curr_retry=0
        ATRTS_list=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            ATR=0
            if "PVV" in single_ticker[9].keys():
                PVV=single_ticker[9]["PVV"]
                #VOL=single_ticker[9]["PVVREL"]
                if multiplyer > 0:
                    ATR=PVV*multiplyer
                else:
                    ATR=0
            if not ATRTS_list:
                ATRTS_list.append(single_ticker[5]-ATR)
            else:
                if ATRTS_list[-1] < tickers[single_ticker_id-1][6]: # upstream
                    if single_ticker[6] > ATRTS_list[-1]: #upstream continue
                        #curr_retry=0
                        ATRTS_list.append(single_ticker[5]-ATR)
                    else:
                        if curr_retry < retries:
                            curr_retry+=1
                            ATRTS_list.append(single_ticker[5]-ATR)
                        else:
                            curr_retry=0
                            ATRTS_list.append(single_ticker[6]+ATR)
                else: # downsteam
                    if single_ticker[5] < ATRTS_list[-1]: #downsteam continue
                        #curr_retry=0
                        ATRTS_list.append(single_ticker[6]+ATR)
                    else:
                        if curr_retry < retries:
                            curr_retry+=1
                            ATRTS_list.append(single_ticker[6]+ATR)
                        else:
                            curr_retry=0
                            ATRTS_list.append(single_ticker[5]-ATR)
        return ATRTS_list
    
    def _get_day_min_max_lists(self, day_tickers):
        min_list = []
        max_list = []
        min_value=200000000
        min_ticker=0
        max_value=0
        max_ticker=0
        for single_ticker_id in range(len(day_tickers)):
            single_ticker=day_tickers[single_ticker_id]
            if single_ticker[5] > max_value:
                max_value=single_ticker[5]
                max_ticker=single_ticker_id
            if single_ticker[6] < min_value:
                min_value=single_ticker[6]
                min_ticker=single_ticker_id
            min_list.append(single_ticker[7]-min_value)
            max_list.append(max_value-single_ticker[7])
        return min_list, max_list
    
    def times_from_last_minmax(self,**kwargs):
        day_tickers=[]
        min_index_list=[]
        max_index_list=[]
        tickers=kwargs.get("tickers",[])
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if not day_tickers or single_ticker[2] == day_tickers[-1][2]:
                day_tickers.append(single_ticker)
            else:
                tmp_min_index_list, tmp_max_index_list = self._get_day_min_max_lists(day_tickers)
                min_index_list+=tmp_min_index_list
                max_index_list+=tmp_max_index_list
                day_tickers=[single_ticker]
        tmp_min_index_list, tmp_max_index_list = self._get_day_min_max_lists(day_tickers)
        min_index_list+=tmp_min_index_list
        max_index_list+=tmp_max_index_list
        return min_index_list, max_index_list
    
    def getOBV(self,**kwargs):
        day_tickers=[]
        obv_list=[]
        max_volume=0
        tickers=kwargs.get("tickers",[])
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if not day_tickers or single_ticker[2] == day_tickers[-1][2]:
                day_tickers.append(single_ticker)
            else:
                obv_value=0
                max_volume=0
                sum_volume=0
                tmp_obv_list=[]
                for one_ticker in day_tickers:
                    sum_volume+=one_ticker[8]
                    full_move=max(0,one_ticker[5]-max(one_ticker[7],one_ticker[4]))*2+max(0,min(one_ticker[7],one_ticker[4])-one_ticker[6])*2+abs(one_ticker[7]-one_ticker[4])
                    if full_move > 0:
                        obv_value+=one_ticker[8]*(one_ticker[7]-one_ticker[4])/full_move
                        tmp_obv_list.append(obv_value)
                    else:
                        tmp_obv_list.append(0)
                    if abs(obv_value) > max_volume:
                        max_volume=abs(obv_value)
                    if max_volume == 0:
                        obv_list.append(0)
                    else:
                        obv_list.append(tmp_obv_list[-1])
                day_tickers=[single_ticker]
        obv_value=0
        max_volume=0
        sum_volume=0
        tmp_obv_list=[]
        for one_ticker in day_tickers:
            sum_volume+=one_ticker[8]
            full_move=max(0,one_ticker[5]-max(one_ticker[7],one_ticker[4]))*2+max(0,min(one_ticker[7],one_ticker[4])-one_ticker[6])*2+abs(one_ticker[7]-one_ticker[4])
            if full_move > 0:
                obv_value+=one_ticker[8]*(one_ticker[7]-one_ticker[4])/full_move
                tmp_obv_list.append(obv_value)
            else:
                tmp_obv_list.append(0)
            if abs(obv_value) > max_volume:
                max_volume=abs(obv_value)
            if max_volume == 0:
                obv_list.append(0)
            else:
                obv_list.append(tmp_obv_list[-1])
        return obv_list
    
    def count_indicators(self,indicators_list, interval = 14):
        #for indicator_name in indicators_list:
        ATR_ind = self.getATR(tickers = self.all_tickers, interval =interval)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATR"] = ATR_ind[single_ticker_id]
            
        PVV_ind, PVV_rel = self.getPVV(tickers = self.all_tickers, interval =7)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["PVV"] = PVV_ind[single_ticker_id]
            self.all_tickers[single_ticker_id][9]["PVVREL"] = PVV_rel[single_ticker_id]
        
        for multiplyer in [0,1,1.5,2,3,4,5,10]:
            ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = multiplyer)
            for single_ticker_id in range(len(self.all_tickers)):
                self.all_tickers[single_ticker_id][9]["ATRTS%s"%multiplyer] = ATR_ind[single_ticker_id]

        EMA_ind = self.getEMA(tickers = self.all_tickers, interval =9)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EMA9"] = EMA_ind[single_ticker_id]
            
        EMA_ind = self.getEMA(tickers = self.all_tickers, interval =14)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EMA14"] = EMA_ind[single_ticker_id]
            
        EMA_ind = self.getEMA(tickers = self.all_tickers, interval =20)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EMA20"] = EMA_ind[single_ticker_id]
            
        EMA_ind = self.getEMA(tickers = self.all_tickers, interval =27)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EMA27"] = EMA_ind[single_ticker_id]

        VWAP_ind = self.getVWAP(tickers = self.all_tickers)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["VWAP"] = VWAP_ind[single_ticker_id]

        VWMA_ind = self.getVWMA(tickers = self.all_tickers, interval =9)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["VWMA9"] = VWMA_ind[single_ticker_id]
            
        VWMA_ind = self.getVWMA(tickers = self.all_tickers, interval =14)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["VWMA14"] = VWMA_ind[single_ticker_id]
            
        VWMA_ind = self.getVWMA(tickers = self.all_tickers, interval =20)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["VWMA20"] = VWMA_ind[single_ticker_id]
            
        VWMA_ind = self.getVWMA(tickers = self.all_tickers, interval =27)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["VWMA27"] = VWMA_ind[single_ticker_id]

        EVWMA_ind = self.getEVWMA(tickers = self.all_tickers, interval =5)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EVWMA5"] = EVWMA_ind[single_ticker_id]

        EVWMA_ind = self.getEVWMA(tickers = self.all_tickers, interval =9)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EVWMA9"] = EVWMA_ind[single_ticker_id]
            
        EVWMA_ind = self.getEVWMA(tickers = self.all_tickers, interval =14)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EVWMA14"] = EVWMA_ind[single_ticker_id]
            
        EVWMA_ind = self.getEVWMA(tickers = self.all_tickers, interval =20)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EVWMA20"] = EVWMA_ind[single_ticker_id]
            
        EVWMA_ind = self.getEVWMA(tickers = self.all_tickers, interval =27)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["EVWMA27"] = EVWMA_ind[single_ticker_id]

        min_ind, max_ind = self.times_from_last_minmax(tickers = self.all_tickers)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["MININD"] = min_ind[single_ticker_id]
            self.all_tickers[single_ticker_id][9]["MAXIND"] = max_ind[single_ticker_id]
        
        OBV_ind = self.getOBV(tickers = self.all_tickers)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["OBV"] = OBV_ind[single_ticker_id]

        
        return self.all_tickers
    
    def get_avg_indicator_value(self, tickers, ind_key):
        ind_value_list=[]
        for single_ticker in tickers:
            ind_value_list.append(single_ticker[9][ind_key])
        ind_value_list=numpy.array(ind_value_list)
        return numpy.mean(ind_value_list)
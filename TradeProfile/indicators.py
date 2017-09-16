'''
Created on 19 aug 2017 

@author: Kurliana
'''
import numpy

class TradeIndicators():
    
    def __init__(self, all_tickers):
        self.all_tickers=all_tickers
    
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
        alpha=(2.0/(interval+1))
        EVWMA_list=[]
        VWMAList=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            VWMAList.append(single_ticker[9]["VWMA%d" % interval])
        VWMAList=numpy.array(VWMAList)
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            if single_ticker_id < interval:
                EVWMA_list.append(float(0))
            elif single_ticker_id == interval:
                EVWMA_list.append(numpy.mean(VWMAList[:interval+1]))
            else:
                EVWMA_list.append(alpha*VWMAList[single_ticker_id]+(1-alpha)*VWMAList[-1])
        return EVWMA_list    
    
    def getATRTrailingStop(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        multiplyer=kwargs.get("multiplyer",3)
        ATRTS_list=[]
        for single_ticker_id in range(len(tickers)):
            single_ticker=tickers[single_ticker_id]
            ATR=0
            if "ATR" in single_ticker[9].keys():
                ATR=single_ticker[9]["ATR"]
            if not ATRTS_list:
                ATRTS_list.append(single_ticker[5]-ATR*multiplyer) 
            else:
                if ATRTS_list[-1] < tickers[single_ticker_id-1][6]: # upstream
                    if single_ticker[6] > ATRTS_list[-1]: #upstream continue
                        ATRTS_list.append(max(ATRTS_list[-1],single_ticker[5]-ATR*multiplyer))
                    else:
                        ATRTS_list.append(single_ticker[6]+ATR*multiplyer)
                else: # downsteam
                    if single_ticker[5] < ATRTS_list[-1]: #downsteam continue
                        ATRTS_list.append(min(ATRTS_list[-1],single_ticker[6]+ATR*multiplyer))
                    else:
                        ATRTS_list.append(single_ticker[5]-ATR*multiplyer)
        return ATRTS_list
                    
    
    def count_indicators(self,indicators_list, interval = 14):
        #for indicator_name in indicators_list:
        ATR_ind = self.getATR(tickers = self.all_tickers, interval =interval)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATR"] = ATR_ind[single_ticker_id]
            
        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 1)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATRTS1"] = ATR_ind[single_ticker_id]
        
        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 1.5)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATRTS1.5"] = ATR_ind[single_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 2)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATRTS2"] = ATR_ind[single_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 3)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATRTS3"] = ATR_ind[single_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 4)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATRTS4"] = ATR_ind[single_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 5)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATRTS5"] = ATR_ind[single_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 10)
        for single_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[single_ticker_id][9]["ATRTS10"] = ATR_ind[single_ticker_id]

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

        return self.all_tickers
    
    def get_avg_indicator_value(self, tickers, ind_key):
        ind_value_list=[]
        for single_ticker in tickers:
            ind_value_list.append(single_ticker[9][ind_key])
        ind_value_list=numpy.array(ind_value_list)
        return numpy.mean(ind_value_list)
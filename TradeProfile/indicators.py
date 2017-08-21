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
        for sigle_ticker_id in range(len(tickers)):
            sigle_ticker=tickers[sigle_ticker_id]
            TrueRangeList.append(max(sigle_ticker[5]-sigle_ticker[6],abs(tickers[sigle_ticker_id-1][7]-sigle_ticker[5]),abs(tickers[sigle_ticker_id-1][7]-sigle_ticker[6])))
        TrueRangeList=numpy.array(TrueRangeList)
        for sigle_ticker_id in range(len(tickers)):
            sigle_ticker=tickers[sigle_ticker_id]
            if sigle_ticker_id < interval:
                ATR_list.append(float(0))
            else:
                ATR_list.append(numpy.mean(TrueRangeList[sigle_ticker_id-13:sigle_ticker_id+1]))
        return ATR_list
    
    def getATRTrailingStop(self,**kwargs):
        tickers=kwargs.get("tickers",[])
        multiplyer=kwargs.get("multiplyer",3)
        ATRTS_list=[]
        for sigle_ticker_id in range(len(tickers)):
            sigle_ticker=tickers[sigle_ticker_id]
            ATR=0
            if "ATR" in sigle_ticker[9].keys():
                ATR=sigle_ticker[9]["ATR"]
            if not ATRTS_list:
                ATRTS_list.append(sigle_ticker[5]-ATR*multiplyer) 
            else:
                if ATRTS_list[-1] < tickers[sigle_ticker_id-1][6]: # upstream
                    if sigle_ticker[6] > ATRTS_list[-1]: #upstream continue
                        ATRTS_list.append(max(ATRTS_list[-1],sigle_ticker[5]-ATR*multiplyer))
                    else:
                        ATRTS_list.append(sigle_ticker[6]+ATR*multiplyer)
                else: # downsteam
                    if sigle_ticker[5] < ATRTS_list[-1]: #downsteam continue
                        ATRTS_list.append(min(ATRTS_list[-1],sigle_ticker[6]+ATR*multiplyer))
                    else:
                        ATRTS_list.append(sigle_ticker[5]-ATR*multiplyer)
        return ATRTS_list
                    
    
    def count_indicators(self,indicators_list):
        #for indicator_name in indicators_list:
        ATR_ind = self.getATR(tickers = self.all_tickers, interval = 14)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATR"] = ATR_ind[sigle_ticker_id]
            
        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 1)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATRTS1"] = ATR_ind[sigle_ticker_id]
        
        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 1.5)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATRTS1.5"] = ATR_ind[sigle_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 2)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATRTS2"] = ATR_ind[sigle_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 3)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATRTS3"] = ATR_ind[sigle_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 4)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATRTS4"] = ATR_ind[sigle_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 5)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATRTS5"] = ATR_ind[sigle_ticker_id]

        ATR_ind = self.getATRTrailingStop(tickers = self.all_tickers, multiplyer = 10)
        for sigle_ticker_id in range(len(self.all_tickers)):
            self.all_tickers[sigle_ticker_id][9]["ATRTS10"] = ATR_ind[sigle_ticker_id]
            
        return self.all_tickers
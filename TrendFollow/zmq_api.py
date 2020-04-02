#############################################################################
# DWX-ZMQ required imports 
#############################################################################
import sys
sys.path.append('../')

# Import ZMQ-Strategy from relative path
from module.DWX_ZMQ_Strategy import DWX_ZMQ_Strategy
from trendfollow import EA_TrendFollow
from module.symbol_obj import symbol_obj
#############################################################################
# Other required imports
#############################################################################

from pandas import DataFrame,concat
from threading import Thread
from time import sleep
from datetime import datetime

#############################################################################
# Class derived from DWZ_ZMQ_Strategy includes data processor for PULL,SUB data
#############################################################################

class zmq_api(DWX_ZMQ_Strategy):
    
    def __init__(self,master_port,obj_input):
        #master_port = _PUSH_PORT,_PULL_PORT,_SUB_PORT [32768,32769,32770]
        _name="PRICES_SUBSCRIPTIONS"
        _broker_gmt=3
        _verbose=False

        # call DWX_ZMQ_Strategy constructor and passes itself as data processor for handling
        # received data on PULL and SUB ports 
        super().__init__(_name,
                         [],          # Empty symbol list (not needed for this example)
                         _broker_gmt,
                         [self],      # Registers itself as handler of pull data via self.onPullData()
                         [self],      # Registers itself as handler of sub data via self.onSubData()
                         _verbose,master_port)
        
        # This strategy's variables
        self._symbols=[sub + obj_input.postfix for sub in obj_input.symbols]
        self.sb_len=len(self._symbols[0])
        
        self.timer_ea=datetime.now()
        self.timeout=60
        self.timeout_count=0
        
        self.ea = []
        self.sb = []
        self.api_obj = None
        self.obj_input=obj_input
        self._EA_Thread = None
        self.all_orders = None
        
    ##########################################################################  
    def ReListTotalOrders(self,_data):
        _df = DataFrame(data=_data['_trades'].values())
        _df = _df[(_df._type<=1) & (_df._magic!=0)]
        df_orders=concat([_df,self.all_orders]).drop_duplicates(keep=False)
        if len(df_orders)>0:
            print("------------------------------------------------------------------------------------------------------")
            print("ReListData")
            self.all_orders = _df
            for i in range(len(df_orders)):
                get_ea = list(filter(lambda x: x.comment == df_orders.iloc[i]._comment and x.symbol.Name==df_orders.iloc[i]._symbol, self.ea))
                if len(get_ea) > 0:
                    get_ea[0].ReListData()
            
    ##########################################################################    
    def onPullData(self, _data):        
        """
        Callback to process new data received through the PULL port
        """        
        if "_action" in _data.keys(): #and \
            #(_data['_action'] == "EXECUTION" or _data['_action'] == "CLOSE"):
            self.trade_data=_data
        if "_onEvent" in _data.keys():
            if _data['_onEvent'] == "onTrade":
                Thread(target=self.ReListTotalOrders(_data)).start()
        
    ##########################################################################    
    def onSubData(self, _data):        
        """
        Callback to process new data received through the SUB port
        """
        self.timer_ea=datetime.now()
        self.timeout_count=0
        #print(_data)
        # split msg to get topic and message
        _topic, _msg = _data.split(";")
        
        #print('\rData on Topic={} with Message={}'.format(_topic, _msg))
        if len(_topic)==self.sb_len:
            _bid,_ask=_msg.split(",")
            get_sb = list(filter(lambda x: x.Name == _topic, self.sb))
            if len(get_sb) > 0:
                if get_sb[0].Bid!=float(_bid) or get_sb[0].Ask!=float(_ask):
                    get_sb[0].Bid=float(_bid)
                    get_sb[0].Ask=float(_ask)
                    if get_sb[0].Updated==False:
                        get_sb[0].Updated=True
        else:
            _time,_open,_high,_low,_close =_msg.split(",")
            #print([float(_close),float(_open),float(_high),float(_low),_time])
            get_ea = list(filter(lambda x: x.Name == _topic, self.ea))
            #print("Update Price Rate : "+_time)
            if len(get_ea) > 0:
                price=[float(_close),float(_open),float(_high),float(_low),_time]
                Thread(target=get_ea[0].CalDiffTP(price)).start()

    ##########################################################################  
    def onPriceUpdate(self):
        while self._zmq._ACTIVE:
            self.CheckStatus()
                
            for s in self.sb:
                if s.Updated:
                    #print('{} {}:{}'.format(s.Name, s.Bid,s.Ask))
                    get_ea = list(filter(lambda x: x.symbol.Name == s.Name, self.ea))
                    if len(get_ea) > 0:
                        for ea in get_ea:
                            if ea.ExeFlag==False:
                                Thread(target=ea.UpdatePrice()).start()
                    s.Updated=False
    
            sleep(self._delay)
    
    ##########################################################################    
    def run(self):        
        """
        Starts price subscriptions
        """        
        self._finished = False
        self.all_orders=self.GetOpenOrders()
        for s in self._symbols:
            self._instruments.append((s,30))
        
        i=1
        for s in self._symbols:
            sb_obj=symbol_obj(s)
            self.sb.append(sb_obj)
            self.obj_input.timeframe=30
            self.ea.append(EA_TrendFollow(sb_obj, self,self.obj_input,i))
            i+=1
            
        self.line.line_token=self.obj_input.line_token
        # Subscribe to all symbols in self._symbols to receive bid,ask prices
        self.SubscribeRateFeeds()
        
        self.timer_ea=datetime.now()
        self._EA_Thread = Thread(target=self.onPriceUpdate)
        self._EA_Thread.start()
        self.line.send_Line_msg("Dual Grid EA Started...")

    ##########################################################################    
    def stop(self):
        self.UnSubscribeRateFeeds()
        try:
            # Acquire lock
            self._lock.acquire()
            self._zmq._DWX_MTX_UNSUBSCRIBE_ALL_MARKETDATA_REQUESTS_()
        
        finally:
            # Release lock
            self._lock.release()
            sleep(self._delay)
        
        self._EA_Thread=None
        self._finished = True

""" -----------------------------------------------------------------------------------------------
    -----------------------------------------------------------------------------------------------
    SCRIPT SETUP
    -----------------------------------------------------------------------------------------------
    -----------------------------------------------------------------------------------------------
"""
# if __name__ == "__main__":
  
#   # creates object with a predefined configuration: intrument list including EURUSD_M1 and GDAXI_M5
#   print('\rLoading example...')
  
#   example = zmq_api([32778,32779,32780],dg_input())  

#   # Starts example execution
#   print('\Running example...')  
  #example.run()


  # Waits example termination
  # print('\rWaiting example termination...')
  # while not example.isFinished():
  #   sleep(1)
  # print('\rBye!!!')

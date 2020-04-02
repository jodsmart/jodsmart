# -*- coding: utf-8 -*-

"""
    DWX_ZMQ_Strategy.py
    --
    @author: Darwinex Labs (www.darwinex.com)
    
    Copyright (c) 2019 onwards, Darwinex. All rights reserved.
    
    Licensed under the BSD 3-Clause License, you may not use this file except 
    in compliance with the License. 
    
    You may obtain a copy of the License at:    
    https://opensource.org/licenses/BSD-3-Clause
"""

from module.DWX_ZeroMQ_Connector_v2_0_2_RC1 import DWX_ZeroMQ_Connector

from module.line_msg import line_msg

from pandas import DataFrame
from datetime import datetime
from threading import Lock
from time import sleep

class DWX_ZMQ_Strategy(object):
    
    def __init__(self, _name="DEFAULT_STRATEGY",    # Name 
                 _symbols=[('EURUSD',0.01),     # List of (Symbol,Lotsize) tuples
                           ('AUDNZD',0.01),
                           ('NDX',0.10),
                           ('UK100',0.1),
                           ('GDAXI',0.01),
                           ('XTIUSD',0.01),
                           ('SPX500',1.0),
                           ('STOXX50E',0.10),
                           ('XAUUSD',0.01)],
                 _broker_gmt=3,                 # Darwinex GMT offset
                 _pulldata_handlers = [],       # Handlers to process data received through PULL port.
                 _subdata_handlers = [],        # Handlers to process data received through SUB port.
                 _verbose=False,
                 _port=[32768,32769,32770]):
        
        self._verbose=_verbose
        self._delay=0.1
        self._wbreak=50
        self._magic=4565
        self._name = _name
        self._symbols = _symbols
        self._broker_gmt = _broker_gmt
        self._symbols=[]
        self._instruments=[]
        self.trade_data=None
        self.updated_list=False
        
        self.timer_ea=datetime.now()
        self.timeout=60
        self.timeout_count=0
        
        self._lock = Lock()
        
        # Not entirely necessary here.
        self._zmq = DWX_ZeroMQ_Connector(_PUSH_PORT=_port[0],_PULL_PORT=_port[1],
                                         _SUB_PORT=_port[2],_pulldata_handlers=_pulldata_handlers,
                                         _subdata_handlers=_subdata_handlers,
                                         _verbose=self._verbose)
        
        self.line=line_msg()
    ##########################################################################
    def CheckStatus(self):
        t=(datetime.now()-self.timer_ea).seconds
        if t>self.timeout:
            msg=self.IsConnected()
            if msg=="Connected":
                if self.timeout_count<=5:
                    self.SubscribeRateFeeds()
            elif msg=="Market_Closed":
                self.timeout_count=0
                #print("Line msg : " + str(self.line.send_Line_msg("Market Closed")))
            elif msg=="Disconnected" or msg is None:
                if self.timeout_count==6:
                    print("Line msg : " + str(self.line.send_Line_msg("MT4 Disconnected.")))
                    #self.stop()
            self.timeout_count+=1
            self.timer_ea=datetime.now()
            
    ##########################################################################
    def WaitDataUpdated(self,name):
        _ws = datetime.now()
        t=0
        if name=="GetMarketHist":
            t=300
        while self.trade_data is None or self.updated_list==False:
            sleep(self._delay)
            if (datetime.now() - _ws).seconds > (self._delay * (self._wbreak+t)):
                print(name+" Timeout...")
                return False
        return True
    ##########################################################################
    def IsConnected(self):
        self.trade_data=None
        self.updated_list=True
        _ret=None
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_SEND_IsConnected_REQUEST_()
            if self.WaitDataUpdated("IsConnected"):
                _ret= self.trade_data["_data"]

        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
        # Default
        return _ret          
    ##########################################################################
        
    def GetAccInfo(self):
        self.trade_data=None
        self.updated_list=True
        _ret=None
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_SEND_ACCINFO_REQUEST_()
        
            if self.WaitDataUpdated("GetAccInfo"):
                _ret= self.trade_data["_data"]

        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
        # Default
        return _ret
    
    ##########################################################################
        
    def GetMarketInfo(self,symbol):
        self.trade_data=None
        self.updated_list=True
        _ret=None
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_SEND_MARKETINFO_REQUEST_(symbol)
            
            if self.WaitDataUpdated("GetMarketInfo"):
                _ret= self.trade_data["_data"]

        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
        # Default
        return _ret
    
    ##########################################################################
        
    def OrderSendBuy(self,symbol,lot,comment):
        _default_order = self._zmq._generate_default_order_dict()
        _default_order['_action'] = 'OPEN'
        _default_order['_type'] = 0 #OP_BUY
        _default_order['_symbol'] = symbol
        _default_order['_lots'] = lot
        _default_order['_SL'] = _default_order['_TP'] = 0
        _default_order['_comment'] = comment
        _default_order['_magic'] = self._magic
        _ret=None
        self.trade_data=None
        self.updated_list=False
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_NEW_TRADE_(_order=_default_order)
            
            if self.WaitDataUpdated("OrderSendBuy"):
                _ret= self.trade_data

        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
        # Default
        return _ret
    
    ##########################################################################
    
    def OrderSendSell(self,symbol,lot,comment):
        _default_order = self._zmq._generate_default_order_dict()
        _default_order['_action'] = 'OPEN'
        _default_order['_type'] = 1 #OP_SELL
        _default_order['_symbol'] = symbol
        _default_order['_lots'] = lot
        _default_order['_SL'] = _default_order['_TP'] = 0
        _default_order['_comment'] = comment
        _default_order['_magic'] = self._magic
        _ret=None
        self.trade_data=None
        self.updated_list=False
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_NEW_TRADE_(_order=_default_order)
            
            if self.WaitDataUpdated("OrderSendSell"):
                _ret= self.trade_data
            
        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
        # Default
        return _ret
    
    ##########################################################################
    
    def OrderClose(self,ticket):
        self.trade_data=None
        self.updated_list=False
        _ret=None
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_CLOSE_TRADE_BY_TICKET_(ticket)
            
            if self.WaitDataUpdated("OrderClose"):
                _ret= self.trade_data
            
        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
        # Default
        return _ret
    
    ##########################################################################
    
    def OrderPartialClose(self,ticket,lot):
        self.trade_data=None
        self.updated_list=False
        _ret=None
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_CLOSE_PARTIAL_BY_TICKET_(ticket,lot)
            
            if self.WaitDataUpdated("OrderPartialClose"):
                _ret= self.trade_data
            
        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
        # Default
        return _ret
    ##########################################################################
    
    def GetOpenOrders(self, symbol="",comment=""):
        self.trade_data=None
        self.updated_list=True
        status=None
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()
            status=self.WaitDataUpdated("GetOpenOrders")
        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
            
        if status:
            _response= self.trade_data
            
            if ('_trades' in _response.keys()
                and len(_response['_trades']) > 0):
                
                _df = DataFrame(data=_response['_trades'].values())
                if symbol=="" and comment=="":
                    return _df[_df._type<=1]
                else:
                    return _df[(_df._comment==comment) & (_df._symbol==symbol) & (_df._type<=1)]
            
        # Default
        return DataFrame()
    ##########################################################################
    #--------max length 30 candle
    def GetMarketHist(self,symbol,timeframe,start,end):
        self.trade_data=None
        self.updated_list=True
        status=None
        try:
            self._lock.acquire()
            self._zmq._DWX_MTX_SEND_MARKETHIST_REQUEST_(symbol,timeframe,start,end)
            status=self.WaitDataUpdated("GetMarketHist")
        finally:
            # Release lock
            self._lock.release()      
            sleep(self._delay)
            
        if status:
            _response= self.trade_data
            
            if ('_data' in _response.keys()
                and len(_response['_data']) > 0):
                
                _df = DataFrame(data=_response['_data'].values())
                return _df.sort_values(by='time', ascending=False)
        # Default
        return DataFrame()
    ##########################################################################
    def SubscribeRateFeeds(self):
        if len(self._instruments) > 0:
            # subscribe to all instruments' rate feeds
            for s in self._symbols:
              try:
                # Acquire lock
                self._lock.acquire()
                self._zmq._DWX_MTX_SUBSCRIBE_MARKETDATA_(s, _string_delimiter=';')
              finally:
                # Release lock
                self._lock.release()        
              sleep(self._delay)
              
            # configure symbols to receive price feeds        
            try:
              # Acquire lock
              self._lock.acquire()
              self._zmq._DWX_MTX_SEND_TRACKPRICES_REQUEST_(self._symbols)
              print('\rConfiguring price feed for {} symbols'.format(len(self._symbols)))
                
            finally:
              # Release lock
              self._lock.release()
              sleep(self._delay)
              
            # configure instruments to receive price rates feeds
            try:
              # Acquire lock
              self._lock.acquire()
              self._zmq._DWX_MTX_SEND_TRACKRATES_REQUEST_(self._instruments)
              print('\rConfiguring rate feed for {} instruments'.format(len(self._instruments)))
                
            finally:
              # Release lock
              self._lock.release()
              sleep(self._delay) 
    ##########################################################################    
    def UnSubscribeRateFeeds(self):
        """
        unsubscribe from all market symbols and exits
        """
        try:
            # Acquire lock
            self._lock.acquire()
            self._zmq._DWX_MTX_SEND_TRACKPRICES_REQUEST_([])        
            print('\rRemoving symbols list')
            sleep(self._delay)
            self._zmq._DWX_MTX_SEND_TRACKRATES_REQUEST_([])
            print('\rRemoving instruments list')
          
        finally:
            # Release lock
            self._lock.release()
            sleep(self._delay)
        
        for s in self._symbols:
        # remove subscriptions and stop symbols price feeding
            try:
                # Acquire lock
                self._lock.acquire()
                self._zmq._DWX_MTX_UNSUBSCRIBE_MARKETDATA_(s)
            
            finally:
                # Release lock
                self._lock.release()
                sleep(self._delay)
    
    ##########################################################################
    def _run_(self):
        
        """
        Enter strategy logic here
        """
         
    ##########################################################################

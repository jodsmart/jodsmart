from datetime import datetime
from time import sleep
from copy import deepcopy

# ------My PY File-------------------------
from module.mysql_exe import *
from module.iATR import iATR
from module.iMA import iMA
from var_input import var_input


class EA_TrendFollow:
    # ------------------------------------------------------------------------------------------------------
    def ReListData(self):
        print("------------------------------------------------------------------------------------------------------")
        print("ReListData : " + self.Name)

        all_orders=self.objClient.all_orders
        self.all_orders=all_orders[(all_orders._comment==self.comment) & (all_orders._symbol==self.symbol.Name)]
        self.total_orders=len(self.all_orders)
        self.buy_list = self.all_orders[self.all_orders._type==0]
        self.sell_list = self.all_orders[self.all_orders._type==1]
                    
        self.buy_list.sort_values(by='_open_price')
        self.buy_total_order = len(self.buy_list)
        if self.buy_total_order > 0:
            self.buy_total_lots = self.buy_list._lots.sum()
            self.buy_min_order = self.buy_list.loc[self.buy_list._open_price==self.buy_list._open_price.min()]
            self.buy_max_order = self.buy_list.loc[self.buy_list._open_price==self.buy_list._open_price.max()]
        else:
            self.buy_total_lots = 0
            self.buy_min_order = None
            self.buy_max_order = None
        
        self.sell_list.sort_values(by='_open_price')
        self.sell_total_order = len(self.sell_list)
        if self.sell_total_order > 0:
            self.sell_total_lots = self.sell_list._lots.sum()
            self.sell_min_order = self.sell_list.loc[self.sell_list._open_price==self.sell_list._open_price.min()]
            self.sell_max_order = self.sell_list.loc[self.sell_list._open_price==self.sell_list._open_price.max()]
        else:
            self.sell_total_lots = 0
            self.sell_min_order = None
            self.sell_max_order = None
        
        print("BuyTotalList : " + str(self.buy_total_order) + (
                    "(%.3f" % self.buy_total_lots) + ") SellTotalList : " + str(self.sell_total_order) + (
                          "(%.3f" % self.sell_total_lots) + ")")
        print("------------------------------------------------------------------------------------------------------")
    # ------------------------------------------------------------------------------------------------------
    def WaitOrderUpdated(self,ticket,type_order):
        _ws = datetime.now()
        while len(self.all_orders[self.all_orders._ticket==ticket])==type_order:
            sleep(self.objClient._delay)
            if (datetime.now() - _ws).seconds > (self.objClient._delay * self.objClient._wbreak):
                print(self.Name+" WaitOrderUpdated Timeout...")
                return False
        return True
    # ------------------------------------------------------------------------------------------------------
    def CalDiffTP(self,price=None):
        #print(self.Name+" CalDiffTP")
        if price is not None:
            self.iatr.UpdateATR(price)
        try:
            self.objClient._lock.acquire()
            #self.balance = float(self.objClient.GetAccInfo()["_balance"])
        finally:
            # Release lock
            self.objClient._lock.release()        
            sleep(self.objClient._delay)
            
        atr=self.iatr.atr[0]
        self.obj_input.SL=atr*self.sl_ratio
        self.obj_input.Trail=atr*self.trail_ratio
        self.obj_input.Order_diff = atr*self.diff_ratio
        self.obj_input.TP = atr

    # ------------------------------------------------------------------------------------------------------
    def PrintStatus(self):
        #print("PrintStatus")
        ##-------- Print Status ------------
        t = datetime.now()
        tt = str(t.strftime('%y-%m-%d %H:%M:%S'))
        print(tt + " : " + self.Name + 
              " >> Trail(" + str(round(self.obj_input.Trail*(10**self.digit))) + 
              "),Diff(" + str(round(self.obj_input.Order_diff*(10**self.digit))) + 
              "),SL(" + str(round(self.obj_input.SL*(10**self.digit))) + 
              "),TP(" + str(round(self.obj_input.TP*(10**self.digit))) + 
              "),Failed(" + str(self.failed) + 
              "),Flag " + str(self.flag))
            
        if self.flag>0:
            print("Over "+str(self.l_p_over)+" Under "+str(self.l_p_under))
        elif self.flag<0:
            print("Over "+str(self.s_p_over)+" Under "+str(self.s_p_over))
    
    # ------------------------------------------------------------------------------------------------------
    def CalLot(self, cal_lot):
        #print("CalLot")
        cal_lot = self.obj_input.start_lot
        if self.obj_input.MM==1:
            ratio=int(self.balance/self.obj_input.start_money)
            cal_lot = int(cal_lot*ratio*100)/100
        
        #cal_lot=int(cal_lot*(self.obj_input.Multiply**self.failed)*100)/100
        
        if cal_lot > self.max_lot:
            return self.max_lot
        if cal_lot < self.min_lot:
            return self.min_lot

        return cal_lot

    # ------------------------------------------------------------------------------------------------------
    def UpdateDB(self):
        if self.failed>self.max_failed:
            self.max_failed=self.failed
            
        sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET"+ \
            " win="+str(self.win) + \
            " ,loss="+str(self.loss) + \
            " ,profit="+str(self.profit) + \
            " ,lose="+str(self.lose) + \
            " ,failed="+str(self.failed) + \
            " ,max_failed="+str(self.max_failed) + \
            " ,buy_over_list='"+str(self.buy_over_list)+"'"+\
            " ,sell_under_list='"+str(self.sell_under_list)+"'"+\
            " WHERE `symbol`='" + self.symbol.Name + "' and acc_id=" + str(self.acc_id) + " and timeframe="+str(self.obj_input.timeframe)
        #print(sql)
        exeDB(sql)
    # ------------------------------------------------------------------------------------------------------
    def Open_Long_Control(self):
        #print("Open_Long_Control")
        price = self.symbol.Ask
        if self.l_p_under==0:
            return False
        if self.l_p_under + self.obj_input.Trail<= price:
            x = self.CalLot(self.buy_total_order)
            if self.buy_min_order is None:
                try:
                    self.objClient._lock.acquire()
                    ticket=self.objClient.OrderSendBuy(self.symbol.Name, x,self.comment,self.magic)
                finally:
                    # Release lock
                    self.objClient._lock.release()      
                    sleep(self.objClient._delay)
                
                if ticket is not None:
                    if ticket['_response_value']=="SUCCESS":
                        msg = "@Init Long Buy : " + self.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                        print(msg)
                        print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                        self.WaitOrderUpdated(ticket['_ticket'],0)
                        return True
        return False

    # ------------------------------------------------------------------------------------------------------
    def Close_Long_Control(self):
        #print("Close_Long_Control")
        if self.buy_min_order is None:
            return False

        price = self.symbol.Bid
        if self.l_p_over==0:
            if self.flag<=0:
                self.l_p_over=price
            return False
        
        o_price = float(self.buy_min_order._open_price)
        #o_lot = float(self.buy_min_order._lots)
        o_ticket = int(self.buy_min_order._ticket)
        if self.l_p_over - self.obj_input.Trail >= price:
            try:
                self.objClient._lock.acquire()
                obj_order=self.objClient.OrderClose(o_ticket)
            finally:
                # Release lock
                self.objClient._lock.release()        
                sleep(self.objClient._delay)
            
            if obj_order is not None:
                if obj_order['_response_value']=="SUCCESS":
                    if float(obj_order['_profit'])>0:
                        self.profit+=float(obj_order['_profit'])
                        self.failed=0
                        self.win+=1
                    else:
                        self.loss+=float(obj_order['_profit'])
                        self.failed+=1
                        self.lose-=1
                        
                    self.UpdateDB()
                
                    msg = "Close Long : " + self.Name + " Profit " + ("%.2f" % float(obj_order['_profit']))
                    print(msg)
                    print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                    self.WaitOrderUpdated(o_ticket,1)
                    return True
        return False
    # ------------------------------------------------------------------------------------------------------
    def Open_Short_Control(self):
        #print("Open_Short_Control")
        price = self.symbol.Bid
        if self.s_p_over==0:
            return False
        if self.s_p_over - self.obj_input.Trail >= price:
            x = self.CalLot(self.sell_total_order)
            if self.sell_max_order is None:
                try:
                    self.objClient._lock.acquire()
                    ticket=self.objClient.OrderSendSell(self.symbol.Name, x,self.comment,self.magic)
                finally:
                    # Release lock
                    self.objClient._lock.release()        
                    sleep(self.objClient._delay)
                
                if ticket is not None:
                    if ticket['_response_value']=="SUCCESS":
                        msg = "@Init Short Sell : " + self.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                        print(msg)
                        print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                        self.WaitOrderUpdated(ticket['_ticket'],0)
                        return True
        return False

    # ------------------------------------------------------------------------------------------------------
    def Close_Short_Control(self):
        #print("Close_Short_Control")
        if self.sell_max_order is None:
            return False

        price = self.symbol.Ask
        if self.s_p_under==0:
            if self.flag>=0:
                self.s_p_under=price
            return False
        
        o_price = float(self.sell_max_order._open_price)
        #o_lot = float(self.sell_max_order._lots)
        o_ticket = int(self.sell_max_order._ticket)
        if self.s_p_under + self.obj_input.Trail<= price:
            try:
                self.objClient._lock.acquire()
                obj_order=self.objClient.OrderClose(o_ticket)
            finally:
                # Release lock
                self.objClient._lock.release()        
                sleep(self.objClient._delay)
                
            
            if obj_order is not None:
                if obj_order['_response_value']=="SUCCESS":
                    if float(obj_order['_profit'])>0:
                        self.profit+=float(obj_order['_profit'])
                        self.failed=0
                        self.win+=1
                    else:
                        self.loss+=float(obj_order['_profit'])
                        self.failed+=1
                        self.lose-=1
                        
                    self.UpdateDB()
                
                    msg = "Close Short : " + self.Name + " Profit " + ("%.2f" % float(obj_order['_profit']))
                    print(msg)
                    print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                    self.WaitOrderUpdated(o_ticket,1)
                    return True

        return False

    # ------------------------------------------------------------------------------------------------------
    def Processing(self):
        #print("Processing")
        obj_input=self.obj_input
        if (self.flag >0 and obj_input.long_only):
            if self.Open_Long_Control():
                self.l_p_under=0
                return
    
        if (self.flag <0 and obj_input.short_only):
            if self.Open_Short_Control():
                self.s_p_over=0
                return
    
        if self.Close_Long_Control():
            self.l_p_over=0
            return
        if self.Close_Short_Control():
            self.s_p_under=0
            return
    # ------------------------------------------------------------------------------------------------------
    def SetTrend(self,price=None):
        #print(self.Name+" SetTrend")
        obj_input=self.obj_input
        if price is not None:
            self.fma.UpdateMA(price)
            self.sma.UpdateMA(price)
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        #[mean,upper,lower,close]
        self.ma=[[0 for i in range(5)]for j in range(obj_input.candle_trend+1)]
        #0 - MODE_MAIN, 1 - MODE_UPPER, 2 - MODE_LOWER)

        for j in range(obj_input.candle_trend+1):
            self.ma[j][0]=self.fma.price[j][0]#close
            self.ma[j][1]=self.fma.price[j][2]#high
            self.ma[j][2]=self.fma.price[j][3]#low
            self.ma[j][3]=self.fma.ma[j]
            self.ma[j][4]=self.sma.ma[j]

        s=0
        for i in range(0,obj_input.candle_trend):
            s+= (self.ma[i][2]>self.ma[i][3] and self.ma[i][2]>self.ma[i][4])
        if s>=obj_input.candle_trend and self.ma[0][3]>self.ma[0][4] and self.trend<=0:
            self.trend=1
            self.l_p_under = 0
            self.s_p_over = 0
            self.flag=0
            self.order_count=0
            self.PrintStatus()
            self.UpdateDB()
        if self.ma[0][4]>self.ma[0][3] and self.trend==1:
            self.trend=0
            self.flag=0
            self.l_p_under = 0
            self.s_p_over = 0
            msg=self.Name+" Reset Trend Buy"
            print(msg)
            print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            self.PrintStatus()
            self.UpdateDB()
        
        s=0
        for i in range(0,obj_input.candle_trend):
            s+= (self.ma[i][1]<self.ma[i][3] and self.ma[i][1]<self.ma[i][4])
        if s>=obj_input.candle_trend and self.ma[0][3]<self.ma[0][4] and self.trend>=0:
            self.trend=-1
            self.l_p_under = 0
            self.s_p_over = 0
            self.flag=0
            self.order_count=0
            self.PrintStatus()
            self.UpdateDB()
        if self.ma[0][4]<self.ma[0][3] and self.trend==-1:
            self.trend=0
            self.flag=0
            self.l_p_under = 0
            self.s_p_over = 0
            msg=self.Name+" Reset Trend Sell"
            print(msg)
            print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            self.PrintStatus()
            self.UpdateDB()     
    # ------------------------------------------------------------------------------------------------------
    def SetFlag(self,price=None):
        #print("SetFlag")
        #['close','open','high','low','time']
        p_list=self.iatr.price
        obj_input=self.obj_input
        
        if self.flag==0:
            s=0
            for i in range(obj_input.candle_trend-1):
                if p_list[i][3]>p_list[i+1][3]:
                    s+=1
            if s==obj_input.candle_trend-1:
                self.flag=1
                self.l_p_under=self.symbol.Ask
                self.s_p_over=0
                self.PrintStatus()
                return
            s=0
            for i in range(obj_input.candle_trend-1):
                if p_list[i][2]<p_list[i+1][2]:
                    s+=1
            if s==obj_input.candle_trend-1:
                self.flag=-1
                self.s_p_over=self.symbol.Bid
                self.l_p_under=0
                self.PrintStatus()
            return
        
        price=self.symbol.Ask
        m=p_list[0][2]
        for i in range(1,obj_input.candle_trend):
            m=max(p_list[i][2],m)
        if price>m and self.flag<=0:
            self.flag=1
            self.l_p_under=price
            self.s_p_over=0
            self.PrintStatus()
            return
        
        price=self.symbol.Bid
        m=p_list[0][3]
        for i in range(1,obj_input.candle_trend):
            m=min(p_list[i][3],m)
        if price<m and self.flag>=0:
            self.flag=-1
            self.s_p_over=price
            self.l_p_under=0
            self.PrintStatus()
            
    # ------------------------------------------------------------------------------------------------------
    def UpdatePrice(self):
        #print("UpdatePrice")
        self.ExeFlag=True
        if self.symbol.Bid!=0 and self.symbol.Ask!=0:
            #--------Update Trail
            price = self.symbol.Bid
            if self.l_p_over < price and self.l_p_over != 0:
                self.l_p_over = price
            if self.s_p_over < price and self.s_p_over != 0:
                self.s_p_over = price
    
            price = self.symbol.Ask
            if self.l_p_under > price and self.l_p_under != 0:
                self.l_p_under = price
            if self.s_p_under > price and self.s_p_under != 0:
                self.s_p_under = price
            
            self.SetFlag()
            #if t1 < t1.replace(hour=2, minute=30) or t1 > t1.replace(hour=6, minute=10):
            if self.obj_input.Enable:
                self.Processing()

        self.ExeFlag=False

    # ------------------------------------------------------------------------------------------------------
    def __init__(self, symbol, obj_client,obj_input,magic):
        self.Name=symbol.Name+str(obj_input.timeframe)
        print("------------------------------------EA Trend Follow "+self.Name+" Start-----------------------------------------------------")
        #--------------- Init Data -----------------------------------------------------------------------------------
        self.objClient = obj_client
        self.acc_id = int(self.objClient.GetAccInfo()["_id"])
        self.symbol = symbol
        self.obj_input=deepcopy(obj_input)
        self.magic=magic
        
        mk_info=self.objClient.GetMarketInfo(self.symbol.Name)
        self.digit = int(mk_info["_digits"])
        self.max_lot = float(mk_info["_maxlot"])
        self.min_lot = float(mk_info["_minlot"])
        self.lot_step = float(mk_info["_lotstep"])
        self.comment = "trendfollow_ea"+str(obj_input.timeframe)
        self.db_name="trendfollow_status"
        self.ExeFlag=False
        
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        
        self.sl_ratio=self.obj_input.SL/self.obj_input.TP
        self.trail_ratio=self.obj_input.Trail/self.obj_input.TP
        self.diff_ratio=self.obj_input.Order_diff/self.obj_input.TP
        self.obj_input.TP=self.obj_input.TP/10**self.digit
        self.obj_input.SL=self.obj_input.SL/10**self.digit
        self.obj_input.Trail=self.obj_input.Trail/10**self.digit
        self.obj_input.Order_diff=self.obj_input.Order_diff/10**self.digit
        
        self.l_p_over = 0
        self.l_p_under = 0
        self.s_p_over = 0
        self.s_p_under = 0
        self.s_c_under = 0
        self.l_c_over = 0
        
        #-------------------------------------------------------------------------------------------------------------
        
        sql = "select * from th_tfex.`"+self.db_name+"` where symbol='" + symbol.Name + "' and acc_id=" + str(self.acc_id) + " and timeframe="+str(self.obj_input.timeframe)
        rows = selectDB(sql)
        if rows is None:
            cnt = exeDB("INSERT INTO th_tfex.`"+self.db_name+"`(acc_id,symbol,timeframe) VALUES(" + str(
                self.acc_id) + ",'" + self.symbol.Name +"'," + str(obj_input.timeframe)+ ")" )
            print("Data Insert " + str(cnt) + " Row")
            rows = selectDB(sql)
        row = rows[0]
        self.profit = row["profit"]
        self.loss = row["loss"]
        self.win = row["win"]
        self.lose = row["lose"]
        self.failed=row["failed"]
        self.max_failed=row["max_failed"]
        #self.trend=row["trend"]
        self.flag=0#row["flag"]
        self.buy_over_list=[]
        blist=row["buy_over_list"][1:-1]
        if blist!="":
            self.buy_over_list = list(map(int,blist.split(",")))
        self.sell_under_list=[]
        slist=row["sell_under_list"][1:-1]
        if slist!="":
            self.sell_under_list = list(map(int,slist.split(",")))
                        
        price=self.objClient.GetMarketHist(self.symbol.Name,obj_input.timeframe,1,obj_input.atr_period+1)
        
        self.iatr=iATR(self.symbol.Name,price,obj_input.timeframe,obj_input.atr_period)
        
        self.CalDiffTP()
        self.fma=iMA(self.symbol.Name,price,obj_input.timeframe,obj_input.fma_period,obj_input.fma_method,obj_input.fma_applied)
        self.sma=iMA(self.symbol.Name,price,obj_input.timeframe,obj_input.sma_period,obj_input.sma_method,obj_input.sma_applied)
        self.SetTrend()
        self.PrintStatus()
        self.ReListData()
        print("Dual Grid Init Completed")
        

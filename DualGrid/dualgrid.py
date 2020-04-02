from datetime import datetime
from time import sleep
from copy import deepcopy

# ------My PY File-------------------------
from module.mysql_exe import *
from module.iATR import iATR
from module.iMA import iMA
from var_input import var_input


class EA_DualGrid:
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
    def UpdateBuyProfit(self,profit=0):
        if profit <= 0.0:
            self.long_profit += profit
        else:
            if len(self.all_orders)==0:
                self.save_profit += profit/3
                self.long_profit += profit/3
                self.short_profit += profit/3
            else:
                profit=profit/100
                self.save_profit += profit*10
                self.long_profit += profit*90*self.buy_total_lots/(self.buy_total_lots+self.sell_total_lots)
                self.short_profit += profit*90*self.sell_total_lots/(self.buy_total_lots+self.sell_total_lots)
        
        self.UpdateDB()
    # ------------------------------------------------------------------------------------------------------
    def UpdateSellProfit(self,profit=0):
        if profit <= 0.0:
            self.short_profit += profit
        else:
            if len(self.all_orders)==0:
                self.save_profit += profit/3
                self.long_profit += profit/3
                self.short_profit += profit/3
            else:
                profit=profit/100
                self.save_profit += profit*10
                self.long_profit += profit*90*self.buy_total_lots/(self.buy_total_lots+self.sell_total_lots)
                self.short_profit += profit*90*self.sell_total_lots/(self.buy_total_lots+self.sell_total_lots)

        self.UpdateDB()
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
              " >> Diff(" + str(round(self.obj_input.Order_diff*(10**self.digit))) + 
              ") , TP(" + str(round(self.obj_input.TP*(10**self.digit))) + 
              ") , Trail(" + str(round(self.obj_input.Trail*(10**self.digit))) + 
              ") , Flag " + str(self.flag)+" , Trend " + str(self.trend))
            
        if self.flag>0:
            print("Over "+str(self.l_p_over)+" Under "+str(self.l_p_under))
        elif self.flag<0:
            print("Over "+str(self.s_p_over)+" Under "+str(self.s_p_under))
        
        self.UpdateDB()
    
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
    def XShortLot(self):
        #print("XShortLot")
        if self.sell_max_order is None:
            return self.obj_input.start_lot

        x = float(self.sell_max_order._open_price)
        price = self.symbol.Bid
        z = int(abs(price - x) / self.obj_input.Order_diff * self.obj_input.step_lot*100)/100
        cal_lot=self.obj_input.start_lot+z
        
        return cal_lot

    # ------------------------------------------------------------------------------------------------------
    def XBuyLot(self):
        #print("XBuyLot")
        if self.buy_min_order is None:
            return self.obj_input.start_lot

        x = float(self.buy_min_order._open_price)
        price = self.symbol.Ask
        z = int(abs(price - x) / self.obj_input.Order_diff * self.obj_input.step_lot*100)/100
        cal_lot=self.obj_input.start_lot+z
        
        return cal_lot
    # ------------------------------------------------------------------------------------------------------
    def UpdateDB(self):
        sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET"+ \
            " save_pf=" + ("%.3f" % self.save_profit) +\
            " ,long_pf=" + ("%.3f" % self.long_profit) +\
            " ,short_pf=" + ("%.3f" % self.short_profit) +\
            " ,trend="+str(self.trend) + \
            " ,flag="+str(self.flag) + \
            " ,buy_over_list='"+str(self.buy_over_list)+"'"+\
            " ,sell_under_list='"+str(self.sell_under_list)+"'"+\
            " WHERE symbol='" + self.symbol.Name + "' and acc_id=" + str(self.acc_id)
        #print(sql)
        exeDB(sql)
    # ------------------------------------------------------------------------------------------------------
    def Open_Long_Control(self):
        #print("Open_Long_Control")
        price = self.symbol.Ask
        if self.l_p_under==0:
            self.l_p_under=price
            return False
        if self.l_p_under + self.obj_input.Trail<= price:
            x = self.CalLot(self.XBuyLot())
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
                        self.WaitOrderUpdated(ticket['_ticket'],0)
                        msg = "@Init Long Buy : " + self.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                        print(msg)
                        print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                        return True
    
            elif float(self.buy_min_order._open_price) - self.obj_input.Order_diff > price:
                try:
                    self.objClient._lock.acquire()
                    ticket=self.objClient.OrderSendBuy(self.symbol.Name, x,self.comment,self.magic)
                finally:
                    # Release lock
                    self.objClient._lock.release()        
                    sleep(self.objClient._delay)
                if ticket is not None:
                    if ticket['_response_value']=="SUCCESS":
                        self.WaitOrderUpdated(ticket['_ticket'],0)
                        msg = "Long Buy Under : " + self.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                        print(msg)
                        print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                        return True
        # if self.buy_min_order != None:
        #     if self.buy_min_order.OpenPrice+self.obj_input.TP+self.obj_input.Trail*(2+len(self.buy_over_list))<price:
        #         ticket=self.objClient.OrderSendBuy(self.symbol.Name,self.obj_input.start_lot,self.comment)
        #         if ticket != 0:
        #             self.buy_over_list.append(ticket)
        #             self.UpdateDB()
        #             msg = "Long Buy Over : " + self.symbol.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % self.obj_input.start_lot)
        #             print(msg)
        #             print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
        #             return True
        return False

    # ------------------------------------------------------------------------------------------------------
    def Close_Long_Control(self):
        #print("Close_Long_Control")
        if self.buy_min_order is None:
            return False

        price = self.symbol.Bid
        o_price = float(self.buy_min_order._open_price)
        o_lot = float(self.buy_min_order._lots)
        o_ticket = int(self.buy_min_order._ticket)
        if self.l_p_over==0:
            if o_price + self.obj_input.TP+self.obj_input.Trail <= price:
                self.l_p_over=price
                msg = "TP Flag Set :" + self.Name + " ID " + str(o_ticket)
                print(msg)
                print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            return False
        
        if self.l_p_over - self.obj_input.Trail >= price:
            # if len(self.buy_over_list)>0:
            #     self.objClient.OrderCloseTicketList(self.buy_over_list)
            #     msg = "Close Long Over : " + self.symbol.Name
            #     print(msg)
            #     print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            #     self.UpdateDB()
            try:
                self.objClient._lock.acquire()
                obj_order=self.objClient.OrderClose(o_ticket)
            finally:
                # Release lock
                self.objClient._lock.release()        
                sleep(self.objClient._delay)
            if obj_order is not None:
                if obj_order['_response_value']=="SUCCESS":
                    profit=float(obj_order['_profit'])
                    self.WaitOrderUpdated(o_ticket,1)
                    self.UpdateBuyProfit(profit)
                    msg = "Take Profit Long : " + self.Name + " Profit " + ("%.2f" % profit)
                    print(msg)
                    print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                    if self.buy_total_order > self.obj_input.list_cut:
                        o_price = float(self.buy_max_order._open_price)
                        o_lot = float(self.buy_max_order._lots)
                        o_ticket = int(self.buy_max_order._ticket)
                        profit=abs(o_price-price)*o_lot*10**self.digit
                        if profit + self.long_profit>0:
                            try:
                                self.objClient._lock.acquire()
                                obj_order=self.objClient.OrderClose(o_ticket)
                            finally:
                                # Release lock
                                self.objClient._lock.release()        
                                sleep(self.objClient._delay)
                            if obj_order is not None and obj_order['_response_value']=="SUCCESS":
                                profit=float(obj_order['_profit'])
                                self.WaitOrderUpdated(o_ticket,1)
                                self.UpdateBuyProfit(profit)
                                msg = "CutLoss Long : " + self.Name + " Profit " + ("%.2f" % profit)
                                print(msg)
                                print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                    return True

        return False
    # ------------------------------------------------------------------------------------------------------
    def Open_Short_Control(self):
        #print("Open_Short_Control")
        price = self.symbol.Bid
        if self.s_p_over==0:
            self.s_p_over=price
            return False
        if self.s_p_over - self.obj_input.Trail >= price:
            x = self.CalLot(self.XShortLot())
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
                        self.WaitOrderUpdated(ticket['_ticket'],0)
                        msg = "@Init Short Sell : " + self.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                        print(msg)
                        print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                        return True
    
            elif float(self.sell_max_order._open_price) + self.obj_input.Order_diff <= price:
                try:
                    self.objClient._lock.acquire()
                    ticket=self.objClient.OrderSendSell(self.symbol.Name, x,self.comment,self.magic)
                finally:
                    # Release lock
                    self.objClient._lock.release()        
                    sleep(self.objClient._delay)
                if ticket is not None:
                    if ticket['_response_value']=="SUCCESS":
                        self.WaitOrderUpdated(ticket['_ticket'],0)
                        msg = "Short Sell Upper : " + self.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                        print(msg)
                        print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                        return True
        # if self.sell_max_order != None:
        #     if self.sell_max_order.OpenPrice-self.obj_input.TP-self.obj_input.Trail*(2+len(self.sell_under_list))>price:
        #         ticket=self.objClient.OrderSendSell(self.symbol.Name,self.obj_input.start_lot,self.comment)
        #         if ticket != 0:
        #             self.sell_under_list.append(ticket)
        #             self.UpdateDB()
        #             msg = "Short Sell Under : " + self.symbol.Name + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % self.obj_input.start_lot)
        #             print(msg)
        #             print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
        #             return True
        return False

    # ------------------------------------------------------------------------------------------------------
    def Close_Short_Control(self):
        #print("Close_Short_Control")
        if self.sell_max_order is None:
            return False

        price = self.symbol.Ask
        o_price = float(self.sell_max_order._open_price)
        o_lot = float(self.sell_max_order._lots)
        o_ticket = int(self.sell_max_order._ticket)
        if self.s_p_under==0:
            if o_price - self.obj_input.TP-self.obj_input.Trail >= price:
                self.s_p_under=price
                msg = "TP Flag Set :" + self.Name + " ID " + str(o_ticket)
                print(msg)
                print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            return False   
                
                
        if self.s_p_under + self.obj_input.Trail<= price:
            # if len(self.sell_under_list)>0:
            #     self.objClient.OrderCloseTicketList(self.sell_under_list)
            #     msg = "Close Short Under : " + self.symbol.Name
            #     print(msg)
            #     print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            #     self.UpdateDB()
            try:
                self.objClient._lock.acquire()
                obj_order=self.objClient.OrderClose(o_ticket)
            finally:
                # Release lock
                self.objClient._lock.release()        
                sleep(self.objClient._delay)
            if obj_order is not None:
                if obj_order['_response_value']=="SUCCESS":
                    profit=float(obj_order['_profit'])
                    self.WaitOrderUpdated(o_ticket,1)
                    self.UpdateSellProfit(profit)
                    msg = "Take Profit Short : " + self.Name + " Profit " + ("%.2f" % profit)
                    print(msg)
                    print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                    if self.sell_total_order> self.obj_input.list_cut:
                        o_price = float(self.sell_min_order._open_price)
                        o_lot = float(self.sell_min_order._lots)
                        o_ticket = int(self.sell_min_order._ticket)
                        profit=abs(o_price-price)*o_lot*10**self.digit
                        if  profit + self.short_profit>0:
                            try:
                                self.objClient._lock.acquire()
                                obj_order=self.objClient.OrderClose(o_ticket)
                            finally:
                                # Release lock
                                self.objClient._lock.release()        
                                sleep(self.objClient._delay)
                            if obj_order is not None and obj_order['_response_value']=="SUCCESS":
                                profit=float(obj_order['_profit'])
                                self.WaitOrderUpdated(o_ticket,1)
                                self.UpdateSellProfit(profit)
                                msg = "CutLoss Short : " + self.Name + " Profit " + ("%.2f" % profit)
                                print(msg)
                                print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
                    return True

        return False

    # ------------------------------------------------------------------------------------------------------
    def Processing(self):
        #print("Processing")
        obj_input=self.obj_input
        if (self.flag >0 and self.trend>0 and obj_input.long_only):
            if self.Open_Long_Control():
                self.l_p_under=0
                return
    
        if (self.flag <0 and self.trend<0 and obj_input.short_only):
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
    def SetFlag(self,price=None):
        #print("SetFlag")
        obj_input=self.obj_input
        if price is not None:
            self.flag_fma.UpdateMA(price)
            self.flag_sma.UpdateMA(price)
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        #[mean,upper,lower,close]
        self.flag_ma=[[0 for i in range(5)]for j in range(obj_input.candle_trend)]
        #0 - MODE_MAIN, 1 - MODE_UPPER, 2 - MODE_LOWER)

        for j in range(obj_input.candle_trend):
            self.flag_ma[j][0]=self.flag_fma.price[j][0]#close
            self.flag_ma[j][1]=self.flag_fma.price[j][2]#high
            self.flag_ma[j][2]=self.flag_fma.price[j][3]#low
            self.flag_ma[j][3]=self.flag_fma.ma[j]
            self.flag_ma[j][4]=self.flag_sma.ma[j]

        s=0
        for i in range(0,obj_input.candle_trend):
            s+= (self.flag_ma[i][2]>self.flag_ma[i][3] and self.flag_ma[i][2]>self.flag_ma[i][4])
        if s>=obj_input.candle_trend and self.flag_ma[0][3]>self.flag_ma[0][4] and self.flag<=0 and self.trend==1:
            self.l_p_under = 0
            self.s_p_over = 0
            self.flag=1
            self.PrintStatus()
        if self.flag_ma[0][4]>self.flag_ma[0][3] and self.flag==1:
            self.flag=0
            self.l_p_under = 0
            self.s_p_over = 0
            msg=self.Name+" Reset Flag Buy"
            print(msg)
            print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            self.PrintStatus()
        
        s=0
        for i in range(0,obj_input.candle_trend):
            s+= (self.flag_ma[i][1]<self.flag_ma[i][3] and self.flag_ma[i][1]<self.flag_ma[i][4])
        if s>=obj_input.candle_trend and self.flag_ma[0][3]<self.flag_ma[0][4] and self.flag>=0 and self.trend==-1:
            self.l_p_under = 0
            self.s_p_over = 0
            self.flag=-1
            self.PrintStatus()
        if self.flag_ma[0][4]<self.flag_ma[0][3] and self.flag==-1:
            self.flag=0
            self.l_p_under = 0
            self.s_p_over = 0
            msg=self.Name+" Reset Flag Sell"
            print(msg)
            print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            self.PrintStatus()

    # ------------------------------------------------------------------------------------------------------
    def SetTrend(self,price=None):
        #print(self.Name+" SetTrend")
        obj_input=self.obj_input
        if price is not None:
            self.trend_fma.UpdateMA(price)
            self.trend_sma.UpdateMA(price)
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        #[mean,upper,lower,close]
        self.trend_ma=[[0 for i in range(5)]for j in range(obj_input.candle_trend)]
        #0 - MODE_MAIN, 1 - MODE_UPPER, 2 - MODE_LOWER)

        for j in range(obj_input.candle_trend):
            self.trend_ma[j][0]=self.trend_fma.price[j][0]#close
            self.trend_ma[j][1]=self.trend_fma.price[j][2]#high
            self.trend_ma[j][2]=self.trend_fma.price[j][3]#low
            self.trend_ma[j][3]=self.trend_fma.ma[j]
            self.trend_ma[j][4]=self.trend_sma.ma[j]

        s=0
        for i in range(0,obj_input.candle_trend):
            s+= (self.trend_ma[i][2]>self.trend_ma[i][3] and self.trend_ma[i][2]>self.trend_ma[i][4])
        if s>=obj_input.candle_trend and self.trend_ma[0][3]>self.trend_ma[0][4] and self.trend<=0:
            self.trend=1
            self.l_p_under = 0
            self.s_p_over = 0
            self.flag=0
            self.PrintStatus()
        if self.trend_ma[0][4]>self.trend_ma[0][3] and self.trend==1:
            self.trend=0
            self.flag=0
            self.l_p_under = 0
            self.s_p_over = 0
            msg=self.Name+" Reset Trend Buy"
            print(msg)
            print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            self.PrintStatus()
        
        s=0
        for i in range(0,obj_input.candle_trend):
            s+= (self.trend_ma[i][1]<self.trend_ma[i][3] and self.trend_ma[i][1]<self.trend_ma[i][4])
        if s>=obj_input.candle_trend and self.trend_ma[0][3]<self.trend_ma[0][4] and self.trend>=0:
            self.trend=-1
            self.l_p_under = 0
            self.s_p_over = 0
            self.flag=0
            self.PrintStatus()
        if self.trend_ma[0][4]<self.trend_ma[0][3] and self.trend==-1:
            self.trend=0
            self.flag=0
            self.l_p_under = 0
            self.s_p_over = 0
            msg=self.Name+" Reset Trend Sell"
            print(msg)
            print("Line msg : " + str(self.objClient.line.send_Line_msg(msg)))
            self.PrintStatus()
        
        # tt = datetime.now()
        # t=(obj_input.TimeFrame-datetime.now().minute%obj_input.TimeFrame)*60
        # #print("SetTrend time"+str(t))
        # Timer(t, self.SetTrend).start()  
        #print("SetTrend Done.")

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
            
            #if t1 < t1.replace(hour=2, minute=30) or t1 > t1.replace(hour=6, minute=10):
            if self.obj_input.Enable:
                self.Processing()

        self.ExeFlag=False

    # ------------------------------------------------------------------------------------------------------
    def __init__(self, symbol, obj_client,obj_input,magic):
        self.Name=symbol.Name
        print("------------------------------------EA Grid "+self.Name+" Start-----------------------------------------------------")
        #--------------- Init Data -----------------------------------------------------------------------------------
        self.objClient = obj_client
        self.acc_id = int(self.objClient.GetAccInfo()["_id"])
        self.symbol = symbol
        self.obj_input=deepcopy(obj_input)
        self.magic=magic
        
        self.sl_ratio=self.obj_input.SL/self.obj_input.TP
        self.trail_ratio=self.obj_input.Trail/self.obj_input.TP
        self.diff_ratio=self.obj_input.Order_diff/self.obj_input.TP
        mk_info=self.objClient.GetMarketInfo(self.symbol.Name)
        self.digit = int(mk_info["_digits"])
        self.max_lot = float(mk_info["_maxlot"])
        self.min_lot = float(mk_info["_minlot"])
        self.lot_step = float(mk_info["_lotstep"])
        self.comment = "dualgrid_ea"
        self.db_name="dual_grid"
        self.l_p_over = 0
        self.s_p_under = 0
        self.l_p_under = 0
        self.s_p_over = 0
        self.ExeFlag=False
        
        #-------------------------------------------------------------------------------------------------------------
        
        sql = "select * from th_tfex.`"+self.db_name+"` where symbol='" + symbol.Name + "' and acc_id=" + str(self.acc_id)
        rows = selectDB(sql)
        if rows is None:
            cnt = exeDB("INSERT INTO th_tfex.`"+self.db_name+"`(acc_id,symbol) VALUES(" + str(
                self.acc_id) + ",'" + self.symbol.Name + "')")
            print("Data Insert " + str(cnt) + " Row")
            rows = selectDB(sql)
        row = rows[0]
        self.save_profit = row["save_pf"]
        self.long_profit = row["long_pf"]
        self.short_profit = row["short_pf"]
        self.flag = row["flag"]  # 0 default -1 sell 1 buy
        self.trend=row["trend"]
        
        self.buy_over_list=[]
        blist=row["buy_over_list"][1:-1]
        if blist!="":
            self.buy_over_list = list(map(int,blist.split(",")))
        self.sell_under_list=[]
        slist=row["sell_under_list"][1:-1]
        if slist!="":
            self.sell_under_list = list(map(int,slist.split(",")))

        max_cal = self.obj_input.start_lot * 5  # Max lot 5x
        if self.max_lot > max_cal:
            self.max_lot = max_cal
                        
        price=self.objClient.GetMarketHist(self.symbol.Name,obj_input.timeframe,1,obj_input.atr_period+1)
        i_price=self.objClient.GetMarketHist(self.symbol.Name,obj_input.i_timeframe,1,obj_input.sma_period+obj_input.candle_trend+1)
        
        self.iatr=iATR(self.symbol.Name,price,obj_input.timeframe,obj_input.atr_period)
        self.flag_fma=iMA(self.symbol.Name,i_price,obj_input.timeframe,obj_input.fma_period,obj_input.fma_method,obj_input.fma_applied)
        self.flag_sma=iMA(self.symbol.Name,i_price,obj_input.timeframe,obj_input.sma_period,obj_input.sma_method,obj_input.sma_applied)
        self.CalDiffTP()
        self.SetFlag()
        self.trend_fma=iMA(self.symbol.Name,i_price,obj_input.i_timeframe,obj_input.fma_period,obj_input.fma_method,obj_input.fma_applied)
        self.trend_sma=iMA(self.symbol.Name,i_price,obj_input.i_timeframe,obj_input.sma_period,obj_input.sma_method,obj_input.sma_applied)
        self.SetTrend()  #300= 5 min
        #self.SetFlag(1.0)       #1= 1 sec
        self.PrintStatus()
        self.ReListData()
        print("Dual Grid Init Completed")
        

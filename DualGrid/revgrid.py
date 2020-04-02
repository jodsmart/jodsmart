import pymysql
import clr
import datetime
import threading

clr.AddReference('MtApi')
# ------Import DLL File-------------------------
from MtApi import *
# ------My PY File-------------------------
from mysql_exe import *
from line_msg import *
from MT_API import *
from functools import reduce


class EA_RevGrid:

    def SetExeFlag(self, flag):
        self.timeFlag = datetime.datetime.now()
        self.objClient.ExeFlag = flag

    # ------------------------------------------------------------------------------------------------------
    def ReListData(self,pos, profit):
        print("------------------------------------------------------------------------------------------------------")
        print("ReListData : " + self.symbol)
        orders = self.objClient.MT_obj.GetOrders(OrderSelectSource.MODE_TRADES)
        self.all_orders = list(filter(lambda x: x.Symbol == self.symbol and x.Comment==self.comment, orders))

        self.buy_list = list(filter(lambda x: x.Operation == TradeOperation.OP_BUY, self.all_orders))
        self.buy_list.sort(key=lambda x: x.OpenPrice)
        self.buy_total_order = len(self.buy_list)
        if self.buy_total_order > 0:
            self.buy_total_lots = round(reduce(lambda x, y: x + y, list(map(lambda x: x.Lots, self.buy_list))), 2)
            self.buy_min_order = self.buy_list[0]
            self.buy_max_order = self.buy_list[self.buy_total_order - 1]
        else:
            self.buy_total_lots = 0
            self.buy_min_order = None
            self.buy_max_order = None

        self.sell_list = list(filter(lambda x: x.Operation == TradeOperation.OP_SELL, self.all_orders))
        self.sell_list.sort(key=lambda x: x.OpenPrice)
        self.sell_total_order = len(self.sell_list)
        if self.sell_total_order > 0:
            self.sell_total_lots = round(reduce(lambda x, y: x + y, list(map(lambda x: x.Lots, self.sell_list))), 2)
            self.sell_min_order = self.sell_list[0]
            self.sell_max_order = self.sell_list[self.sell_total_order - 1]
        else:
            self.sell_total_lots = 0
            self.sell_min_order = None
            self.sell_max_order = None

        
        if profit < 0.0:
            if pos=="Long":
                self.long_profit += profit
            if pos=="Short":
                self.short_profit += profit
        else:
            if len(self.all_orders)==0:
                self.save_profit += profit
            else:
                profit=profit/100
                self.save_profit += profit*10
                self.long_profit += profit*90*self.buy_total_lots/(self.buy_total_lots+self.sell_total_lots)
                self.short_profit += profit*90*self.sell_total_lots/(self.buy_total_lots+self.sell_total_lots)

        sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET `save_pf`=" + ("%.3f" % self.save_profit)
        sql += ",`long_pf`=" + ("%.3f" % self.long_profit)
        sql += ",`short_pf`=" + ("%.3f" % self.short_profit)
        sql += " WHERE `symbol`='" + self.symbol + "' and acc_id="+str(self.acc_id)

        row = exeDB(sql)
        self.SetExeFlag(False)
        print("Data Updated "+str(row)+" Row")
        print("BuyTotalList : " + str(self.buy_total_order) + (
                    "(%.3f" % self.buy_total_lots) + ") SellTotalList : " + str(self.sell_total_order) + (
                          "(%.3f" % self.sell_total_lots) + ")")
        print("Save Profit : " + ("%.3f" % self.save_profit) + 
              " Long Profit : " + ("%.3f" % self.long_profit)+ 
              " Short Profit : " + ("%.3f" % self.short_profit))
        print("------------------------------------------------------------------------------------------------------")
    # ------------------------------------------------------------------------------------------------------
    def CalDiffTP(self):
        if self.objClient.ExeFlag == False:
            self.SetExeFlag(True)
            #print("CalDiffTP")
            # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
            self.balance = self.objClient.MT_obj.AccountEquity()
            self.SetExeFlag(False)
            atr = self.objClient.MT_obj.iATR(self.symbol, self.diff_tp_period, 14, 0)
            if atr < self.min_sl:
                atr = self.min_sl
            self.zone_diff = atr
            self.zone_tp = atr
    
            # atr = self.objClient.MT_obj.iATR(self.symbol, self.diff_sl_period, 14, 0)
            # self.zone_sl=atr
            threading.Timer(self.diff_tp_period*60, self.CalDiffTP).start()
        else:
            self.objClient.Busy_msg("CalDiffTP")
            threading.Timer(1, self.CalDiffTP).start()
            

    # ------------------------------------------------------------------------------------------------------
    def PrintStatus(self,p):
        #print("PrintStatus")
        ##-------- Print Status ------------
        t = datetime.datetime.now()
        tt = str(t.strftime('%y-%m-%d %H:%M:%S'))
        print(tt + " : " + self.symbol + 
              " >> Diff(" + str(round(self.zone_diff*(10**self.digit))) + 
              ") , TP(" + str(round(self.zone_tp*(10**self.digit))) + 
              ") , Flag " + str(self.flag)+" , Trend " + str(self.trend))
            
        if self.flag>0:
            print("Over "+str(self.l_p_over)+" Under "+str(self.l_p_under))
        elif self.flag<0:
            print("Over "+str(self.s_p_over)+" Under "+str(self.s_p_under))
            
        threading.Timer(p, self.PrintStatus, args=(p,)).start() 
    
    # ------------------------------------------------------------------------------------------------------
    def CalLot(self, cal_lot):
        #print("CalLot")
        if cal_lot > self.max_lot:
            return self.max_lot
        if cal_lot < self.min_lot:
            return self.min_lot

        return cal_lot

    # ------------------------------------------------------------------------------------------------------
    def XShortLot(self):
        #print("XShortLot")
        if self.sell_max_order == None:
            return self.start_lot

        x = self.sell_max_order.OpenPrice
        price = self.Bid
        z = int(abs(price - x) / self.zone_diff * self.step_lot*100)/100
        cal_lot=self.start_lot+z
        
        if self.trend<0:
            if self.fibo[2]>price and price>self.fibo[4]:
                cal_lot=int(cal_lot*1.5*100)/100
        return cal_lot

    # ------------------------------------------------------------------------------------------------------
    def XBuyLot(self):
        #print("XBuyLot")
        if self.buy_min_order == None:
            return self.start_lot

        x = self.buy_min_order.OpenPrice
        price = self.Ask
        z = int(abs(price - x) / self.zone_diff * self.step_lot*100)/100
        cal_lot=self.start_lot+z
        
        if self.trend>0:
            if self.fibo[4]>price and price>self.fibo[2]:
                cal_lot=int(cal_lot*1.5*100)/100

        return cal_lot

    # ------------------------------------------------------------------------------------------------------
    def Open_Long_Control(self):
        #print("Open_Long_Control")
        price = self.Ask
        if self.l_p_under + self.zone_diff/2.0< price:
            x = self.CalLot(self.XBuyLot())
            if self.buy_max_order == None:
                if self.objClient.MT_obj.OrderSendBuy(self.symbol, x, self.slipage,0.0,0.0,self.comment,self.magic) != 0:
                    msg = "@Init Long Buy : " + self.symbol + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                    print(msg)
                    print("Line msg : " + str(send_Line_msg(msg)))
                    self.l_p_under = price
                    return True
    
            if self.buy_max_order.OpenPrice - self.zone_diff > price:
                print("OrderSendBuy " + str(self.symbol) + " " + str(x))
                if self.objClient.MT_obj.OrderSendBuy(self.symbol, x, self.slipage,0.0,0.0,self.comment,self.magic) != 0:
                    msg = "Long Buy Over : " + self.symbol + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                    print(msg)
                    print("Line msg : " + str(send_Line_msg(msg)))
                    self.l_p_under = price
                    return True

        return False

    # ------------------------------------------------------------------------------------------------------
    def Close_Long_Control(self):
        #print("Close_Long_Control")
        if self.buy_min_order == None:
            return False

        price = self.Ask
        if self.l_p_over - self.zone_tp/2.0 < price:
            return False
        o_price = self.buy_min_order.OpenPrice
        o_lot = self.buy_min_order.Lots
        o_ticket = self.buy_min_order.Ticket
        if o_price + self.zone_tp < price:
            if self.objClient.MT_obj.OrderClose(o_ticket, self.slipage):
                c_price = self.objClient.MT_obj.OrderClosePrice(o_ticket)
                msg = "Take Profit Long : " + self.symbol + " : Open " + ("%.4f" % o_price) + " : Close " + ("%.4f" % c_price) + " : " + ("%.2f" % o_lot)
                print(msg)
                print("Line msg : " + str(send_Line_msg(msg)))
                if self.buy_total_order > self.list_cut:
                    o_price = self.buy_max_order.OpenPrice
                    o_lot = self.buy_max_order.Lots
                    o_ticket = self.buy_max_order.Ticket
                    profit=abs(o_price-price)*o_lot*10**self.digit
                    if  profit < self.long_profit:
                        if self.objClient.MT_obj.OrderClose(o_ticket, self.slipage):
                            c_price = self.objClient.MT_obj.OrderClosePrice(o_ticket)
                            msg = "CutLoss Long : " + self.symbol + " : Open " + ("%.4f" % o_price) + " : Close " + ("%.4f" % c_price) + " : " + ("%.2f" % o_lot)
                            print(msg)
                            print("Line msg : " + str(send_Line_msg(msg)))
                self.l_p_under = price
                return True

        return False
    # ------------------------------------------------------------------------------------------------------
    def Cut_Long_Control(self):
        #print("Cut Lose_Long_Control")
        if self.buy_max_order == None:
            return False

        price = self.Ask
        o_price = self.buy_max_order.OpenPrice
        o_lot = self.buy_max_order.Lots
        o_ticket = self.buy_max_order.Ticket
        if self.l_c_over==0:
            if self.l_p_under + self.diff_tp_period < o_price:
                self.l_c_over=price
                msg = "Cut loss Flag Set :" + self.symbol + " ID " + str(o_ticket)
                print(msg)
                print("Line msg : " + str(send_Line_msg(msg)))
            return False
        if self.l_c_over - self.diff_tp_period/2 < price:
            return False

        if self.objClient.MT_obj.OrderClose(o_ticket, self.slipage):
            c_price = self.objClient.MT_obj.OrderClosePrice(o_ticket)
            msg = "Cut Loss Long : " + self.symbol + " : Open " + ("%.4f" % o_price) + " : Close " + ("%.4f" % c_price) + " : " + ("%.2f" % o_lot)
            print(msg)
            print("Line msg : " + str(send_Line_msg(msg)))
            return True

        return False
    # ------------------------------------------------------------------------------------------------------
    def Open_Short_Control(self):
        #print("Open_Short_Control")
        price = self.Bid
        
        if self.s_p_over - self.zone_diff/2.0 > price:
            x = self.CalLot(self.XShortLot())
            if self.sell_max_order == None:
                if self.objClient.MT_obj.OrderSendSell(self.symbol, x, self.slipage,0.0,0.0,self.comment,self.magic) != 0:
                    msg = "@Init Short Sell : " + self.symbol + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                    print(msg)
                    print("Line msg : " + str(send_Line_msg(msg)))
                    self.s_p_under = price
                    return True
    
            if self.sell_max_order.OpenPrice + self.zone_diff < price:
                if self.objClient.MT_obj.OrderSendSell(self.symbol, x, self.slipage,0.0,0.0,self.comment,self.magic) != 0:
                    msg = "Short Sell Upper : " + self.symbol + " : Open" + ("%.4f" % price) + " : " + ("%.2f" % x)
                    print(msg)
                    print("Line msg : " + str(send_Line_msg(msg)))
                    self.s_p_under = price
                    return True

        return False

    # ------------------------------------------------------------------------------------------------------
    def Close_Short_Control(self):
        #print("Close_Short_Control")
        if self.sell_max_order == None:
            return False

        price = self.Bid
        if self.s_p_under + self.zone_tp/2.0> price:
            return False
        o_price = self.sell_max_order.OpenPrice
        o_lot = self.sell_max_order.Lots
        o_ticket = self.sell_max_order.Ticket
        if o_price - self.zone_tp > price:
            if self.objClient.MT_obj.OrderClose(o_ticket, self.slipage):
                c_price = self.objClient.MT_obj.OrderClosePrice(o_ticket)
                msg = "Take Profit Short : " + self.symbol + " : Open " + ("%.4f" % o_price) + " : Close " + ("%.4f" % c_price) + " : " + ("%.2f" % o_lot)
                print(msg)
                print("Line msg : " + str(send_Line_msg(msg)))
                if self.sell_total_order > self.list_cut:
                    o_price = self.sell_min_order.OpenPrice
                    o_lot = self.sell_min_order.Lots
                    o_ticket = self.sell_min_order.Ticket
                    profit=abs(o_price-price)*o_lot*10**self.digit
                    if  profit < self.short_profit:
                        if self.objClient.MT_obj.OrderClose(o_ticket, self.slipage):
                            c_price = self.objClient.MT_obj.OrderClosePrice(o_ticket)
                            msg = "CutLoss Short : " + self.symbol + " : Open " + ("%.4f" % o_price) + " : Close " + ("%.4f" % c_price) + " : " + ("%.2f" % o_lot)
                            print(msg)
                            print("Line msg : " + str(send_Line_msg(msg)))
                self.s_p_over = price
                return True

        return False
    # ------------------------------------------------------------------------------------------------------
    def Cut_Short_Control(self):
        #print("Cut Lose_Short_Control")
        if self.sell_min_order == None:
            return False

        price = self.Bid
        o_price = self.sell_min_order.OpenPrice
        o_lot = self.sell_min_order.Lots
        o_ticket = self.sell_min_order.Ticket
        if self.s_c_under==0:
            if self.s_p_over - self.diff_tp_period> o_price:
                self.s_c_under=price
                msg = "Cut loss Flag Set :" + self.symbol + " ID " + str(o_ticket)
                print(msg)
                print("Line msg : " + str(send_Line_msg(msg)))
            return False
        if self.s_c_under + self.diff_tp_period/2 > price:
            return False

        if self.objClient.MT_obj.OrderClose(o_ticket, self.slipage):
            c_price = self.objClient.MT_obj.OrderClosePrice(o_ticket)
            msg = "Cut Loss Short : " + self.symbol + " : Open " + ("%.4f" % o_price) + " : Close " + ("%.4f" % c_price) + " : " + ("%.2f" % o_lot)
            print(msg)
            print("Line msg : " + str(send_Line_msg(msg)))
            return True

        return False
    # ------------------------------------------------------------------------------------------------------
    def Processing(self):
        #print("Processing")
        #threading.Timer(t, self.Processing, args=(t,)).start()
        msg = ""      
        try:
#
            if (self.flag >0 and self.long_only == 1):
                if self.Open_Long_Control():
                    return

            if (self.flag <0 and self.short_only == 1):
                if self.Open_Short_Control():
                    return

            if self.Cut_Long_Control():
                return
            if self.Cut_Short_Control():
                return

            self.SetExeFlag(False)
        except MtConnectionException as ex:
            msg = "MtConnectionException: " + ex.Message
            print(msg)
            print("Line msg : " + str(send_Line_msg(msg)))
            self.SetExeFlag(False)
        except MtExecutionException as ex:
            msg = ""
            if ex.ErrorCode == 4108:
                msg = "Error " + self.symbol + ":" + ex.Message + ";Code = " + str(
                    ex.ErrorCode) + ";OrderClosed Already."
                self.ReListData("",0)
            elif ex.ErrorCode == 138:
                msg = "Error " + self.symbol + ":" + ex.Message + ";Code = " + str(ex.ErrorCode) + ";Price changed."
            else:
                msg = "Error " + self.symbol + ":" + ex.Message + ";Code = " + str(ex.ErrorCode)

            print(msg)
            print("Line msg : " + str(send_Line_msg(msg)))
            self.SetExeFlag(False)
        # except:
        #     msg="Unknow Error!!!"
        #     print(msg)
        #     print("Line msg : "+str(send_Line_msg(msg)))
        #     self.SetExeFlag(False)
            
    # ------------------------------------------------------------------------------------------------------
    def SetFlag(self):
        #print("SetFlag")
        price = self.Bid
        if self.s_p_over - self.zone_diff * self.swap_side > price and (self.flag == 1 or self.flag == 0):
            self.flag = -1
            self.l_p_under = price
            sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET `flag`='-1' WHERE `symbol`='" + self.symbol + "' and acc_id="+str(self.acc_id)
            row = exeDB(sql)
            print("SetFlag Sell : Updated " + str(row) + " Row")
            return

        price = self.Ask
        if self.l_p_under + self.zone_diff * self.swap_side < price and (self.flag == -1 or self.flag == 0):
            self.flag = 1
            self.s_p_over = price
            sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET `flag`='1' WHERE `symbol`='" + self.symbol + "' and acc_id="+str(self.acc_id)
            row = exeDB(sql)
            print("SetFlag Buy : Updated " + str(row) + " Row")
        
        #threading.Timer(p, self.SetFlag, args=(p,)).start()
    # ------------------------------------------------------------------------------------------------------
    def UpdateFibo(self):
        #print("UpdateFibo")
        if self.objClient.ExeFlag == False:
            self.SetExeFlag(True)
            for i in range(7):
                # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
                # Use 0=0 1=23.6 2=38.2 3=50 4=61.8 5=100 6=161.8 7=261.8 8=423.6
                self.fibo[i]=self.objClient.MT_obj.iCustom(self.symbol,self.diff_sl_period,"Projects\\Auto_Fibo",0,i)
            
            self.SetExeFlag(False)
            if self.fibo[2]>self.fibo[4]:
                self.trend=-1
            if self.fibo[4]>self.fibo[2]:
                self.trend=1
            threading.Timer(self.diff_tp_period*60, self.UpdateFibo).start()
        else:
            self.objClient.Busy_msg("UpdateFibo")
            threading.Timer(1, self.UpdateFibo).start()
    # ------------------------------------------------------------------------------------------------------
    def UpdatePrice(self,t):
        #print("UpdatePrice")
        threading.Timer(t, self.UpdatePrice, args=(t,)).start()
        t = datetime.datetime.now()      
        if self.objClient.ExeFlag == False and self.Bid!=0 and self.Ask!=0:
            #--------Update Trail
            price = self.Bid
            if self.l_p_over < price or self.l_p_over == 0:
                self.l_p_over = price
                sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET `l_p_over`=" + ("%.5f" % self.l_p_over) + \
                      " WHERE `symbol`='" + self.symbol + "' and acc_id=" + str(self.acc_id)
                exeDB(sql)
            if self.s_p_over < price or self.s_p_over == 0:
                self.s_p_over = price
                sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET `s_p_over`=" + ("%.5f" % self.s_p_over) + \
                      " WHERE `symbol`='" + self.symbol + "' and acc_id=" + str(self.acc_id)
                exeDB(sql)
            if self.l_c_over!=0:
                if self.l_c_over < price or self.l_c_over == 0:
                    self.l_c_over = price
    
            price = self.Ask
            if self.l_p_under > price or self.l_p_under == 0:
                self.l_p_under = price
                sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET `l_p_under`=" + ("%.5f" % self.l_p_under) + \
                      " WHERE `symbol`='" + self.symbol + "' and acc_id=" + str(self.acc_id)
                exeDB(sql)
            if self.s_p_under > price or self.s_p_under == 0:
                self.s_p_under = price
                sql = "UPDATE `th_tfex`.`"+self.db_name+"` SET `s_p_under`=" + ("%.5f" % self.s_p_under) + \
                      " WHERE `symbol`='" + self.symbol + "' and acc_id=" + str(self.acc_id)
                exeDB(sql)
            if self.s_c_under!=0:
                if self.s_c_under > price or self.s_c_under == 0:
                    self.s_c_under = price
            
            self.SetFlag()
            ##------- Set Time to Trade ---------
        
            if t < t.replace(hour=3, minute=30) or t > t.replace(hour=5, minute=10):
                self.SetExeFlag(True)
                self.Processing()
        else:
            tt = int((t - self.timeFlag).total_seconds())
            #print("Wait Updated:" + str(tt))
            if tt > 60:
                self.ReListData("",0.0)
                print("Time Out.....")

    # ------------------------------------------------------------------------------------------------------
    def __init__(self, symbol, obj):
        print("------------------------------------EA Grid "+symbol+" Start-----------------------------------------------------")
        #--------------- Init Data -----------------------------------------------------------------------------------
        self.objClient = obj
        self.acc_id = self.objClient.MT_obj.AccountNumber()
        self.symbol = symbol
        self.slipage = 3
        self.digit = self.objClient.MT_obj.SymbolInfoInteger(self.symbol, 17)  # SYMBOL_DIGITS = 17
        self.contract_size = self.objClient.MT_obj.SymbolInfoDouble(self.symbol, 28)  # SYMBOL_TRADE_CONTRACT_SIZE = 28
        self.min_sl = self.objClient.MT_obj.MarketInfo(self.symbol,13)*10 / 10**self.digit  # must over than 10x from spread
        self.comment = "revgrid_ea"
        self.magic=565
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        self.flag_period = 1440
        self.zone_diff=0
        self.zone_tp=0
        self.min_cut_pf=50
        self.s_c_under = 0
        self.l_c_over = 0
        self.Bid=0
        self.Ask=0
        self.trend=0
        self.db_name="rev_grid"

        #-------------------------------------------------------------------------------------------------------------

        sql = "select * from th_tfex.`"+self.db_name+"` where symbol='" + symbol + "' and acc_id=" + str(self.acc_id)
        rows = selectDB(sql)
        if rows is None:
            cnt = exeDB("INSERT INTO th_tfex.`"+self.db_name+"`(acc_id,symbol) VALUES(" + str(
                self.acc_id) + ",'" + self.symbol + "')")
            print("Data Insert " + str(cnt) + " Row")
            rows = selectDB(sql)
        row = rows[0]
        self.save_profit = row["save_pf"]
        self.long_profit = row["long_pf"]
        self.short_profit = row["short_pf"]
        self.mm = row["mm"]
        self.list_cut = row["list_cut"]
        self.long_only = row["long_only"]
        self.short_only = row["short_only"]
        self.flag = row["flag"]  # 0 default -1 sell 1 buy
        self.swap_side = row["swap"]
        self.start_lot = row["start_lot"]
        self.step_lot = row["step_lot"]
        self.l_p_over = row["l_p_over"]
        self.l_p_under = row["l_p_under"]
        self.s_p_over = row["s_p_over"]
        self.s_p_under = row["s_p_under"]
        self.diff_tp_period = row["tf_pf"]
        self.diff_sl_period = row["tf_sl"]


        ##        self.long_under_trail=0.0
        ##        self.long_over_trail=0.0
        ##        self.short_over_trail=0.0
        ##        self.short_under_trail=0.0
        self.max_lot = self.objClient.MT_obj.MarketInfo(self.symbol, MarketInfoModeType.MODE_MAXLOT)
        self.min_lot = self.objClient.MT_obj.MarketInfo(self.symbol, MarketInfoModeType.MODE_MINLOT)

        max_cal = self.start_lot * 5  # Max lot 5x
        if self.max_lot > max_cal:
            self.max_lot = max_cal
            
        if self.flag >0:
            print("SetFlag Buy")
        elif self.flag <0:
            print("SetFlag Sell")
        
        self.CalDiffTP()
        self.ReListData("",0)
        self.fibo=[0,1,2,3,4,5,6]
        self.UpdateFibo()  #300= 5 min
        self.UpdatePrice(0.5)#0.5= 0.5sec
        #self.SetFlag(1.0)       #1= 1 sec
        self.PrintStatus(300.0) #300= 5 min
        #self.Processing(0.5)
        print("Dual Grid Init Completed")
        

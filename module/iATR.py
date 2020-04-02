
class iATR:
    def __init__(self,symbol,price,timeframe=60,period=80):
        self.Name=symbol+str(timeframe)
        self.atr=[]
        self.price=price[['close','open','high','low','time']].values.tolist()
        self.timeframe=timeframe
        self.period=period
        
        self.ATR()
        
    def UpdateATR(self,price):
        if price[4]==self.price[0][4]:
            #print("Already this price series.")
            return
        self.price.pop()
        self.price.insert(0,price)
        self.ATR()
        
    def ATR(self):
        if len(self.atr)>0:
            tr=max([self.price[0][2]-self.price[0][3],
                    abs(self.price[1][0]-self.price[0][2]),
                    abs(self.price[1][0]-self.price[0][3])])/self.period
            tr-=max([self.price[self.period-1][2]-self.price[self.period-1][3],
                         abs(self.price[self.period][0]-self.price[self.period-1][2]),
                        abs(self.price[self.period][0]-self.price[self.period-1][3])])/self.period
            tr+=self.atr[0]
            self.atr.pop()
            self.atr.insert(0,tr)
        else:
            tr=0
            for i in reversed(range(len(self.price)-1)):
                tr+=max([self.price[i][2]-self.price[i][3],
                         abs(self.price[i+1][0]-self.price[i][2]),
                        abs(self.price[i+1][0]-self.price[i][3])])/self.period
                if i<=len(self.price)-self.period-1:
                    self.atr.insert(0,tr)
                    tr-=max([self.price[i+self.period-1][2]-self.price[i+self.period-1][3],
                         abs(self.price[i+self.period][0]-self.price[i+self.period-1][2]),
                        abs(self.price[i+self.period][0]-self.price[i+self.period-1][3])])/self.period

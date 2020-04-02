
class iMA:
    def __init__(self,symbol,price,timeframe=60,period=14,method=0,apply=0):
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        self.Name=symbol+str(timeframe)
        self.ma=[]
        self.price=price[['close','open','high','low','time']].values.tolist()
        self.timeframe=timeframe
        self.period=period
        #Method SMA=0 EMA=1 SMMA=2 LWMA=3
        self.method=method
        #Applied Price Close=0 Open=1 High=2 Low=3 HL/2=4 HLC/3=5 Weight_HLCC/4=6
        self.apply=apply
        
        if method==0:
            self.SMA()
        elif method==1:
            self.EMA()
            
    def UpdateMA(self,price):
        if price[4]==self.price[0][4]:
            #print("Already this price series.")
            return
        self.price.pop()
        self.price.insert(0,price)
        if self.method==0:
            self.SMA()
        elif self.method==1:
            self.EMA()
        
    def SMA(self):
        if len(self.ma)>0:
            self.ma.insert(0,self.price[0][self.apply]/self.period+self.ma[0]
                           -self.price[self.period][self.apply]/self.period)
            self.ma.pop()
        else:
            prev_ma=0
            for i in reversed(range(len(self.price))):
                prev_ma+=self.price[i][self.apply]/self.period
                if i<=len(self.price)-self.period:
                    self.ma.insert(0,prev_ma)
                    prev_ma-=self.price[i+self.period-1][self.apply]/self.period
    
    def EMA(self):
        sm_fac=2.0/(1.0+self.period)
        if len(self.ma)>0:
            self.ma.insert(0,(self.price[0][self.apply]-self.ma[0])*sm_fac+self.ma[0])
            self.ma.pop()
        else:
            prev_ma=self.price[-1][self.apply]
            for i in reversed(range(len(self.price)-1)):
                self.ma.insert(0,(self.price[i][self.apply]-prev_ma)*sm_fac+prev_ma)
                prev_ma=self.ma[0]
        
    
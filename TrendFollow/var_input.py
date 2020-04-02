class var_input:
   
    def __init__(self):
        self.line_token="QIigVnDkALwcSo5ZnDLDf1VZOvxIzMvDTfo6QBAamDK"
        self.Enable=1
        self.long_only=1
        self.short_only=1
        self.TP=100
        self.SL=100
        self.Trail=30
        self.Order_diff=100
        self.list_cut=3
        self.swap_side=2
        self.Multiply=1.5
        self.candle_trend=3 #min 1
        self.MM=0 #0=disable 1=enable
        self.start_lot=0.01
        self.step_lot=0.01
        self.start_money=100
        self.symbols=["AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDUSD","CADCHF","CADJPY",
                    "CHFJPY","EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD",
                    "EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD",
                    "NZDCAD","NZDCHF","NZDJPY","NZDUSD","USDCAD","USDCHF","USDJPY"]
        self.postfix="."
        # PERIOD M5=5 M30=30 H1=60 H4=240 D1=1440 W1=10080 MN=43200
        self.timeframe=60
        
        self.atr_period=80


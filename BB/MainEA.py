from zmq_api import zmq_api
from var_input import var_input

var_input1=var_input()
var_input1.Manual=1
var_input1.Enable=1
var_input1.MM=0
var_input1.start_lot=0.01
var_input1.Multiply=2
var_input1.start_money=100
#var_input1.symbols=["AUDCAD","AUDUSD","GBPJPY","EURCHF","EURNZD","GBPCHF","NZDCAD","USDJPY"]
var_input1.symbols=["AUDCAD","AUDCHF","AUDJPY","AUDNZD","AUDUSD","CADCHF","CADJPY",
                    "CHFJPY","EURAUD","EURCAD","EURCHF","EURGBP","EURJPY","EURNZD",
                    "EURUSD","GBPAUD","GBPCAD","GBPCHF","GBPJPY","GBPNZD","GBPUSD",
                    "NZDCAD","NZDCHF","NZDJPY","NZDUSD","USDCAD","USDCHF","USDJPY"]
var_input1.postfix="."
client1=zmq_api([32790,32791,32792],var_input1)

client1.run()
#client1.stop()

#client1.ea[5].PrintStatus()


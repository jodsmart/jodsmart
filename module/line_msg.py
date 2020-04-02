import urllib.parse
import requests

class line_msg:
    
    def __init__(self,token="yNigOUri5stLMrG1v2J8c8x3r6Wx8f9ZIZbyYK1W08K"):
        # Line Notify-------------------------------------------------------
        self.line_token=token
        self.url = "https://notify-api.line.me/api/notify"
        
    def send_Line_msg(self,message):
        msg = urllib.parse.urlencode({"message":message})
        headers = {'Content-Type':'application/x-www-form-urlencoded',"Authorization":"Bearer "+self.line_token}
        session = requests.Session()
        a=session.post(self.url, headers=headers, data=msg)
        code = {200:"Success",400:"Unauthorized request",401:"Invalid access token",500:"Failure due to server error"}
        return code.get(a.status_code,"Processed over time or stopped")


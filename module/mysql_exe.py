import pymysql

host="192.168.1.4"
port=3307
user="root"
passwd="123456"
database="th_tfex"

#------------------------------------------------------------------------------------------------------
def selectDB(sql):
    try:
        results=None
        db = pymysql.connect(host=host,port=port,user=user,passwd=passwd,db=database)
        cursor = db.cursor(pymysql.cursors.DictCursor)
        total_rows=cursor.execute(sql)
        if total_rows!=0:
            results = cursor.fetchall()
        # print("selectDB : "+str(total_rows)+" row")
        cursor.close()
        db.close()
        return results
    except Error as e:
        print("selectDB Error : "+e.Message)
        cursor.close()
        db.close()

#------------------------------------------------------------------------------------------------------
def exeDB(sql):
    db = pymysql.connect(host=host,port=port,user=user,passwd=passwd,db=database)
    cursor = db.cursor()
    total_rows=cursor.execute(sql)
    db.commit()
    cursor.close()
    db.close()
    # print("exeDB:"+str(total_rows))
    return total_rows

import sys
import MySQLdb 

# Réception des paramètres
remote_station = sys.argv[1]
local_station = sys.argv[2]
pages = sys.argv[3]
total_pages = sys.argv[4]
code = sys.argv[5]
caller = sys.argv[6]
uuid = sys.argv[7]

#Variables MySQL
myHost = "mysqlhost"
myUser = "mysqluser"
myPass = "mysqlpass"
myDb = "mysqldb"

conn = MySQLdb.connect (host = myHost,
                           user = myUser,
                           passwd = myPass,
                           db = myDb)
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO rss_faxes(uuid,caller_id,remote_station,local_station,pages,pages_total,code,date_received)
    VALUES
    (%s,%s,%s,%s,%s,%s,%s,NOW())
""", (uuid,caller,remote_station,local_station,pages,total_pages,code))
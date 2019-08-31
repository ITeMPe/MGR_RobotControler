import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
import time
import spidev
import MySQLdb
from datetime import datetime
import threading

request_get_data_flag = False
temporary_flag = False
# ip_address = "192.168.0.50"
ip_address = "192.168.1.87"
sektor_1 = "11AABBCC"
sektor_2 = "22AABBCC"
sektor_3 = "33AABBCC"
myresult = ""


def SendGetDataRequest():
    global request_get_data_flag
    request_get_data_flag = True
    threading.Timer(10.0, SendGetDataRequest).start()
    # print "ZAPYTANIE CMD_GAT_DATA\r\n"

class FrameRequest:
    def __init__(self, cmd, payload):
        self.cmd = cmd
        self.payload = payload

def PerformAction(rec_id_card,rec_id_sector,rec_iterator):
    print "Perform action start"
    db = MySQLdb.connect(host=ip_address,    # your host, usually localhost
        user="AdminPI",         # your username
        passwd="Magisterka",  # your password
        db="magazyn")        # name of the data base
    cur = db.cursor()
    cur.execute("SELECT * FROM magazyn.supplier")
    myresult = cur.fetchall()
    db.close()
    my_id_card = rec_id_card[0:2]+":"+rec_id_card[2:4]+":"+rec_id_card[4:6]+":"+rec_id_card[6:8]
    my_id_sector = rec_id_sector[0:2]+":"+rec_id_sector[2:4]+":"+rec_id_sector[4:6]+":"+rec_id_sector[6:8]
    # print "Znane produkty:"  #dla debugu
    for x in myresult:
        # print x #dla debugu
        if my_id_card in x:
            print "Znaleziony UID:"
            print x
            my_id = x[0]
            my_uid = x[1]
            my_name = x[2]
            db = MySQLdb.connect(host= ip_address,    # your host, usually localhost
                user="AdminPI",         # your username
                passwd="Magisterka",  # your password
                db="magazyn")        # name of the data base
            cur = db.cursor()
            # sprawdzenie czy jest juz taki produkt w magazynie - jesli tak to nie ma sensu go dodawac, jesli nie nalezy dodac
            cur.execute("SELECT * FROM magazyn.cargo WHERE (supplier_id = "+str(x[0])+")")
            myresult2 = cur.fetchall()
            number_of_records = cur.rowcount
            if 0 == number_of_records:
                print "Brak produktu w magazynie ---> Dodano nowy produkt"
                if rec_id_sector == sektor_1:
                    int_val_sec = 1
                elif rec_id_sector == sektor_2:
                    int_val_sec = 2
                elif rec_id_sector == sektor_3:
                    int_val_sec = 3
                else:    
                    int_val_sec = int(rec_id_sector,16) / 1000
                int_val_itr = int(rec_iterator)
                val = (x[0],my_id_sector,rec_iterator,x[4])
                sql = "INSERT INTO `magazyn`.`cargo` (`supplier_id`, `position_x`, `position_y`, `price`) VALUES (%s, %s, %s, %s)"
                cur.execute(sql,val)
            else:        
                print("Liczba rekordów w bazie danych: %d"%number_of_records)
                find_record = False
                for i in myresult2:
                    print i
                    if x[0] == int(i[1]):
                        print "Znaleziono taki produkt w magazynie"
                        find_record = True
                        break
                if False == find_record: #TO SIE NIE POWINNO WYDAZYC - BO ALBO PRODUKTU NIE MA I GO DODAJEMY ALBO JEST I KONIEC
                    print "Nie ma takiego produktu w magazynie ---> Dodano nowy produkt"
                    if rec_id_sector == sektor_1:
                        int_val_sec = 1
                    elif rec_id_sector == sektor_2:
                        int_val_sec = 2
                    elif rec_id_sector == sektor_3:
                        int_val_sec = 3
                    else:    
                        int_val_sec = int(rec_id_sector,16) / 1000
                    int_val_itr = int(rec_iterator)
                    val = (x[0],int_val_sec,int_val_itr,x[4])
                    sql = "INSERT INTO `magazyn`.`cargo` (`supplier_id`, `position_x`, `position_y`, `price`) VALUES (%s, %s, %s, %s)"
                    cur.execute(sql,val)
            db.commit()
            
    print "Perform action stop"

def ParserRecData(data):
    if data != '':
        cmd = (data[0])
        if cmd == '1':
            print("Rec response  OK STOP")
            return 1
        elif cmd == '2':
            print("Rec response  OK START")    
            return 2
        elif cmd == '3':
            print("Rec response  OK STATUS") 
            return 3
        elif cmd == '4':
            print("Rec response  OK CONFIG")
            return 4
        elif cmd == '5':
            print("Rec response  OK GET DATA")
            id_card = data[1:9]
            id_sector = data[9:17]
            iterator =  data[17:len(data)]
            print("id_card: %s",id_card)
            print("id_sector: %s",id_sector)
            print("iterator: %s",iterator)
            PerformAction(id_card,id_sector,iterator)
            return 5
        else:
            print("Error !!")
            return 0
    else:
        print("Error, Rec data is empty !!")
        return 0

GPIO.setmode(GPIO.BCM)

# pipes = [[0xE8, 0xE8, 0xF0, 0xF0, 0xE1], [0xF0, 0xF0, 0xF0, 0xF0, 0xE1]]  # for Rpi to Arduino
# pipes = [[0x01,0x01,0x01,0x01,0x01], [0xc2,0xc2,0xc2,0xc2,0xc2]]  # for Rpi to Rpi
pipes = [[0xc2,0xc2,0xc2,0xc2,0xc2],[0x01,0x01,0x01,0x01,0x01]]  # for Rpi to STM32


radio = NRF24(GPIO, spidev.SpiDev())
radio.begin(0, 17)

radio.setRetries(15,15)
radio.setPALevel(NRF24.PA_MAX)
radio.setDataRate(NRF24.BR_250KBPS)
radio.setPayloadSize(32)
radio.openWritingPipe(pipes[0])
radio.openReadingPipe(1,  pipes[1])

# radio.setChannel(0x76)
radio.printDetails()

# cmd_stop = FrameRequest("CMD_STOP","asda",)
# print(cmd_stop.cmd)
# print(cmd_stop.payload)

# rec_frame1 = "1OK->CMD_STOP"
# rec_frame2 = "2OK->CMD_START"
# rec_frame3 = "3OK->CMD_STATUS"
# rec_frame4 = "4OK->CMD_CONFIG"
rec_frame5 = "51122334455667788170"
rec_frame6 = "5660289145566778814"
# ParserRecData(rec_frame1)
# ParserRecData(rec_frame2)
# ParserRecData(rec_frame3)
# ParserRecData(rec_frame4)
# ParserRecData(rec_frame5)
# ParserRecData(rec_frame6)


SendGetDataRequest()

while(1):
    # global temporary_flag = False
    if request_get_data_flag == True:
        print("Flga request_get_data_flag", request_get_data_flag)
        request_get_data_flag = False
        # radio.stopListening()
        message = list("5_CMD_GET_DATA")
        temporary_flag = True
    else:
        # print("Flga request_get_data_flag", request_get_data_flag)
        db = MySQLdb.connect(host=ip_address,    # your host, usually localhost
                user="AdminPI",         # your username
                passwd="Magisterka",  # your password
                db="magazyn")        # name of the data base
        cur = db.cursor()
        cur.execute("SELECT * FROM `comandsmode` WHERE id=(SELECT MAX(id) FROM `comandsmode`)")
        myresult = cur.fetchone()
        db.close()
        var = myresult[2]
        if var == 0:
            # print myresult  
            for raw in cur.fetchall():
                print raw
            if myresult[1] == 1:
                message = list("1_CMD_STOP")
            elif myresult[1] == 2:
                message = list("2_CMD_START")
            elif myresult[1] == 3:
                message = list("3_CMD_STATUS")
            elif myresult[1] == 4:
                message = list("4_CMD_CONFIG")
            elif myresult[1] == 5:
                message = list("5_CMD_GET_DATA")
            else:
                message = list("No command to send !!")    
            temporary_flag = True
    if temporary_flag == True:
        temporary_flag = False
        radio.stopListening()
        while len(message)<32:
            message.append(0)
        start = time.time()
        radio.write(message)
        # pirint("Status send: %d",status_send )
        print("Sent the message: {}".format(message))
        radio.startListening()
        while not radio.available(0):
            time.sleep(1 / 100)
            if time.time() - start > 2:
                print("Timed out.")
                break
        receivedMessage = []
        radio.read(receivedMessage, radio.getDynamicPayloadSize())
        print("Received: {}".format(receivedMessage))
        print("Translating the receivedMessage into unicode characters")
        string = ""
        for n in receivedMessage:
            # Decode into standard unicode set
            if (n >= 32 and n <= 126):
                string += chr(n)
        print("Out received message decodes to: {}".format(string))
        res = ParserRecData(string)
        # radio.stopListening()
        if res == 1 or res == 2:
            db = MySQLdb.connect(host=ip_address,    # your host, usually localhost
                    user="AdminPI",         # your username
                    passwd="Magisterka",  # your password
                    db="magazyn")        # name of the data base
            cur = db.cursor()
            str_sql = "UPDATE magazyn.`comandsmode` SET exe = '1', date = " +"'"+ datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"'"+ "  WHERE (id = "+ str(myresult[0])+")"
            print(str_sql)
            cur.execute(str_sql)   
            db.commit()
            db.close()
        elif res == 5:
            db = MySQLdb.connect(host=ip_address,    # your host, usually localhost
                    user="AdminPI",         # your username
                    passwd="Magisterka",  # your password
                    db="magazyn")        # name of the data base
            cur = db.cursor()
        # time.sleep(0.5)
        time.sleep(1)
        # For release version shoud be without delay :)

    


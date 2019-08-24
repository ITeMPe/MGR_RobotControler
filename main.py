import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
import time
import spidev
import MySQLdb
from datetime import datetime
import threading

request_get_data_flag = False

def SendGetDataRequest():
    global request_get_data_flag
    request_get_data_flag = True
    threading.Timer(3.0, SendGetDataRequest).start()
    print "ZAPYTANIE CMD_GAT_DATA\r\n"

class FrameRequest:
    def __init__(self, cmd, payload):
        self.cmd = cmd
        self.payload = payload

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
            iterator =  (data[17:len(data)])
            print("id_card: %s",id_card)
            print("id_sector: %s",id_sector)
            print("iterator: %s",iterator)
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

cmd_stop = FrameRequest("CMD_STOP","asda",)
print(cmd_stop.cmd)
print(cmd_stop.payload)

# rec_frame1 = "1OK->CMD_STOP"
# rec_frame2 = "2OK->CMD_START"
# rec_frame3 = "3OK->CMD_STATUS"
# rec_frame4 = "4OK->CMD_CONFIG"
# rec_frame5 = "5123456789"
# ParserRecData(rec_frame1)
# ParserRecData(rec_frame2)
# ParserRecData(rec_frame3)
# ParserRecData(rec_frame4)
# ParserRecData(rec_frame5)

SendGetDataRequest()

while(1):
    if request_get_data_flag == True:
        print("Flga request_get_data_flag", request_get_data_flag)
        request_get_data_flag = False
        radio.stopListening()
        message = list("5_CMD_GET_DATA")
        while len(message)<32:
            message.append(0)
        start = time.time()
        radio.write(message)
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
        radio.stopListening()
        # if res == 5:
        #     db = MySQLdb.connect(host="192.168.0.51",    # your host, usually localhost
        #             user="AdminPI",         # your username
        #             passwd="Magisterka",  # your password
        #             db="magazyn")        # name of the data base
        #     cur = db.cursor()
        #     str_sql = "UPDATE magazyn.`comandsmode` SET exe = '1', date = " +"'"+ datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"'"+ "  WHERE (id = "+ str(myresult[0])+")"
        #     print(str_sql)
        #     cur.execute(str_sql)   
        #     db.commit()
        #     db.close()
    else:
        print("Flga request_get_data_flag", request_get_data_flag)
        db = MySQLdb.connect(host="192.168.0.51",    # your host, usually localhost
                user="AdminPI",         # your username
                passwd="Magisterka",  # your password
                db="magazyn")        # name of the data base
        cur = db.cursor()
        cur.execute("SELECT * FROM `comandsmode` WHERE id=(SELECT MAX(id) FROM `comandsmode`)")
        myresult = cur.fetchone()
        db.close()
        print myresult
        var = myresult[2]
        if var == 0:
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
            radio.stopListening()
            while len(message)<32:
                message.append(0)
            start = time.time()
            radio.write(message)
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
            radio.stopListening()
            if res == 1 or res == 2:
                db = MySQLdb.connect(host="192.168.0.51",    # your host, usually localhost
                        user="AdminPI",         # your username
                        passwd="Magisterka",  # your password
                        db="magazyn")        # name of the data base
                cur = db.cursor()
                str_sql = "UPDATE magazyn.`comandsmode` SET exe = '1', date = " +"'"+ datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"'"+ "  WHERE (id = "+ str(myresult[0])+")"
                print(str_sql)
                cur.execute(str_sql)   
                db.commit()
                db.close()
        time.sleep(0.5)


    


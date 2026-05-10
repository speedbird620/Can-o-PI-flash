# FLARM-blinker
#
# Revision 0.1, first version
#
# avionics@skyracer.net

#import machine
from machine import ADC, UART, Pin
import utime
import math
import time

# Variables
MessageFromNMEAPort = ""
MySpeed = 0
MyLat = 0
MyLong = 0
Validity = "V"
Validity_Old = ""
ActivateFlasher = False
ActivateFlasher_old = False
tajm = 0
timeout = 0
no_comm_time = 4
AlarmDist_H = 1000
AlarmDist_V = 250
MinSpeed = 10
init = True

# Pins
EnableWatchDog_Pin = Pin(9, Pin.IN, Pin.PULL_UP)       # Ouput to the hardware watchdog
Deactivate_Pin = Pin(15, Pin.OUT)            # Latch to keep the FLARM on

#Coms
#u0 = UART(0, baudrate=19200, bits=8, parity=None, stop=1)
u0 = UART(0, baudrate=19200, bits=8, parity=None, stop=1)
u1 = UART(1, baudrate=19200, bits=8, parity=None, stop=1)

def subCheckSum(sentence):

    strCalculated = ""

    # Saving the incoming checksum for reference
    strOriginal = sentence[-2:]

    # Remove checksum
    sentence = sentence[:-3]

    # Remove $
    sentence = sentence[1:]

    chksum = ""
    calc_cksum = 0

    #print("Scrutinized string: " + sentence)

    # Calculating checksum
    for s in sentence:

        #print "s: " + str(s)
        calc_cksum ^= ord(s)     #calc_cksum ^= ord(s)
        strCalculated = hex(calc_cksum).upper()

    # Removing the  "0X" from the hex value
    try:
        strCalculated = strCalculated[2:]

        # If the checksum is a single digit, adding a zero in front of the digit
        if len(strCalculated) == 1:
            strCalculated = "0" + strCalculated

        #print("chksum: " + strCalculated + " " + " sentence: " + sentence)

    except:
        whatever = True

    # Returning the provided checksum (from the original message) and the calculated 
    return strOriginal, strCalculated


class clGPRMCMessage(object):

    def __init__(self, sentance):

        # Example $GPRMC,150242.00,A,5911.22585,N,01739.40910,E,0.201,294.43,280821,,,A*60

        # 150242.00     Time Stamp
        # A             Validity - A-ok, V-invalid
        # 5911.22585    Current Latitude
        # N             North/South
        # 01739.40910   Current Longitude
        # W             East/West
        # 0.201         Speed in knots
        # 294.43        True course
        # 280821        Date Stamp
        #               Variation
        #               Var dir
        # A             Mode ind
        # *60           checksum

        (self.GPGGA,
         self.Time,
         self.Valid,
         self.Lat,
         self.N_or_S,
         self.Long,
         self.E_or_W,
         self.Speed,
         self.TCourse,
         self.Date,
         self.VarDir,
         self.MagVar,
         self.CRC
        ) = sentance.replace("\r\n","").replace(":",",").split(",")

class clPFLAAMessage_8(object):

    def __init__(self, sentance):

        #Example: $PFLAA,0,-123,456,-50,1,4B3F51,180,,55,2,1*1A
        # 
        # 0         AlarmLevel
        # -123      RelativeNorth
        # 456       RelativeEast
        # -50       RelativeVertical
        # 1         IDType
        # 4B3F51    ID
        # 180       Track
        #           TurnRate
        # 55        GroundSpeed
        # 2         ClimbRate
        # 1         AcftType
        # 1         Notrack
        # 1A        Checksum

        (self.PFLAA,
         self.AlarmLevel,
         self.RelativeNorth,
         self.RelativeEast,
         self.RelativeVertical,
         self.IDType,
         self.ID,
         self.Track,
         self.TurnRate,
         self.GroundSpeed,
         self.ClimbRate,
         self.AcftType,
         self.NoTrack,
         self.CRC
        ) = sentance.replace("\r\n","").replace(":",",").split(",")

class clPFLAAMessage_sub8(object):

    def __init__(self, sentance):

        #Example: $PFLAA,0,-123,456,-50,1,4B3F51,180,,55,2,1*1A
        # 
        # 0         AlarmLevel
        # -123      RelativeNorth
        # 456       RelativeEast
        # -50       RelativeVertical
        # 1         IDType
        # 4B3F51    ID
        # 180       Track
        #           TurnRate
        # 55        GroundSpeed
        # 2         ClimbRate
        # 1         AcftType
        # 1         Notrack
        # 1A        Checksum

        (self.PFLAA,
         self.AlarmLevel,
         self.RelativeNorth,
         self.RelativeEast,
         self.RelativeVertical,
         self.IDType,
         self.ID,
         self.Track,
         self.TurnRate,
         self.GroundSpeed,
         self.AcftType,
         self.CRC
        ) = sentance.replace("\r\n","").replace(":",",").split(",")



class clPFLAUMessage(object):

    def __init__(self, sentance):

        # Example: $PFLAU,RX,TX,GPS,Power,AlarmLevel,RelativeBearing,AlarmType,RelativeVertical,RelativeDistance,ID*Checksum
        #
        #           PFLAU,0 ,1 ,1  ,1    ,0         ,               ,0        ,                ,                ,*4F
        
        (self.PFLAU,
         self.RX,
         self.TX,
         self.GPS,
         self.Power,
         self.AlarmLevel,
         self.RelativeBearing,
         self.AlarmType,
         self.RelativeVertical,
         self.RelativeDistance,
         self.CRC
        ) = sentance.replace("\r\n","").replace(":",",").split(",")

def subExtractNMEAInfo(Sentence, MessageType):
    Lat = 0
    Long = 0
    Time = ""

    # Recieves the NMEA sentence. Time to assemble the string and make some sense of it

    # strNMEASplit = clGPRMCMessage(Sentence)
    if MessageType == "GPRMC":
        strNMEASplit = clGPRMCMessage(Sentence)

        Sentence=Sentence[:-6]

        if (len(strNMEASplit.Lat) > 0 or len(strNMEASplit.Long) > 0):

            # Lat = DDMM.mmmmm shall be recalculated into DD.ddddddd
            if strNMEASplit.N_or_S == "S":                # Is this cricket? Scruteny please!
                LatDegrees = strNMEASplit.Lat[:2] * -1
            else:
                LatDegrees = strNMEASplit.Lat[:2]

            LatMinutes = strNMEASplit.Lat[-8:]
            Lat = float(LatDegrees) + (float(LatMinutes)/60)

            # Long = DDDMM.mmmmm shall be recalculated into DD.ddddddd
            if strNMEASplit.E_or_W == "W":                  # Is this cricket? Scruteny please!
                LongDegrees = strNMEASplit.Long[:3] * -1
            else:
                LongDegrees = strNMEASplit.Long[:3]

            LongMinutes = strNMEASplit.Long[-8:]
            Long = float(LongDegrees) + (float(LongMinutes)/60)

        return Lat, Long, strNMEASplit.Valid, strNMEASplit.Speed

    elif MessageType == "PFLAA":
        try:
            strNMEASplit = clPFLAAMessage_8(Sentence)
        except:
            strNMEASplit = clPFLAAMessage_sub8(Sentence)
                
        return strNMEASplit.AlarmLevel, strNMEASplit.RelativeNorth, strNMEASplit.RelativeEast, strNMEASplit.RelativeVertical

    elif MessageType == "PFLAU":
        strNMEASplit = clPFLAUMessage(Sentence)
        if strNMEASplit.RelativeBearing == "":
            strNMEASplit.RelativeBearing = "0"
        if strNMEASplit.RelativeVertical == "":
            strNMEASplit.RelativeVertical = "0"
        if strNMEASplit.RelativeDistance == "":
            strNMEASplit.RelativeDistance = "0"
        print("RX: " + strNMEASplit.RX + " TX: " + strNMEASplit.TX + " GPS: " + strNMEASplit.GPS + " Power: " + strNMEASplit.Power + " AlarmLevel: " + strNMEASplit.AlarmLevel + " RelBear: " + strNMEASplit.RelativeBearing + " RelVert: " + strNMEASplit.RelativeVertical + " RelDist: " + strNMEASplit.RelativeDistance)
        return strNMEASplit.RX, strNMEASplit.TX, strNMEASplit.AlarmLevel, strNMEASplit.GPS, strNMEASplit.RelativeDistance, strNMEASplit.RelativeVertical

    else:
        return Lat, Long, Time, ""


def split_nmea(buf):
    """
    Split a bytes/string buffer into complete NMEA sentences.

    Args:
        buf (bytes|bytearray|str): input buffer containing zero or more NMEA sentences.

    Returns:
        (sentences, remainder)
        - sentences: list of str (each starts with '$' and has no trailing CRLF)
        - remainder: bytes with any trailing partial data (may be empty)
    """
    # Normalize to immutable bytes
    if isinstance(buf, str):
        b = buf.encode('utf-8', 'ignore')
    else:
        b = bytes(buf)

    sentences = []
    i = 0
    L = len(b)

    while True:
        # Find next start marker
        start = b.find(b'$', i)
        if start == -1:
            # no more complete sentences
            break

        # Find CRLF after the $ start
        end = b.find(b'\r\n', start)
        if end == -1:
            # partial sentence (incomplete) -> keep as remainder
            break

        # Extract sentence bytes (without CRLF)
        sentence_bytes = b[start:end]

        # Safe decode: ignore malformed bytes
        try:
            s = sentence_bytes.decode('utf-8', 'ignore')
        except Exception:
            s = sentence_bytes.decode('latin-1', 'ignore')

        sentences.append(s)

        # Move index after this CRLF
        i = end + 2
        if i >= L:
            break

    # remainder: anything after the last processed index
    remainder = b[i:] if i < L else b''

    return sentences, remainder



while True:
    
    if init:
        init = False
        if EnableWatchDog_Pin == False:
            print("Internal watchdog is avtivated")
        else:
            print("No watchdog avtivated")
    
    #MessageFromNMEAPort = u0.readline()decode('utf-8', errors='ignore').rstrip('\r\n')

    #print("u0: " + MessageFromNMEAPort)

    #b = u0.read().decode('utf-8')
    #raw = u0.read()

    MessageFromNMEAPort = ""
    
    if u0.any():
        #b = u0.read().decode('utf-8')
        MessageFromNMEAPort = u0.read()
        #MessageFromNMEAPort = b.decode('utf-8', 'ignore')
        #print("u0: " + str(MessageFromNMEAPort))

    elif u1.any():
        #b = u0.read().decode('utf-8')
        MessageFromNMEAPort = u1.read()
        #MessageFromNMEAPort = b.decode('utf-8', 'ignore')
        #print("u0: " + str(MessageFromNMEAPort))

    if len(MessageFromNMEAPort) > 0:
        #raw = b"$GPRMC,131049.00,A,5911.23097,N,01739.42720,E,0.121,,170426,,,A*76\r\n$GPGGA,131049.00,5911.23097,N,01739.42720,E,1,08,1.11,27.5,M,25.4,M,,*64\r\n$GPGSA,A,3,10,02,23,15,01,14,32,27,,,,,1.94,1.11,1.58*05\r\n"
        sentences, rem = split_nmea(MessageFromNMEAPort)
        # sentences will be 3 strings (no trailing CRLF)
        # rem will be b'' (empty) because we consumed all complete lines
        for s in sentences:
            #print("=>", s)        
                
            # Extracting a sentence for further handling
            NMEALine = s[:(s.find("\r\n"))]
            
            #print("A")

            chkSumLine, chkCalculated = subCheckSum(NMEALine)

            #print(chkSumLine + " calculated: " + chkCalculated)
            
            
            if NMEALine.find("GPRMC") == 1: # and chkSumLine == chkCalculated:
                MyLat, MyLong, Validity, MySpeed = subExtractNMEAInfo(NMEALine, "GPRMC")
                print("GPRMC MyLat: " + str(MyLat) + " MyLong: " + str(MyLong) + " Validity: " + Validity + " MySpeed: " + MySpeed)

                if Validity == "A":
                    ActivateFlasher = False
                    timeout = time.time()
                else:
                    ActivateFlasher = True

            if NMEALine.find("PFLAU") == 1: # and chkSumLine == chkCalculated:

                #print("C")

                RX, TX, AlarmLevel, GPS, RelativeDistance, RelativeVertical = subExtractNMEAInfo(NMEALine, "PFLAU")

                #if (RX != "0" and (int(RelativeDistance) < AlarmDist_H or int(RelativeDistance) > -AlarmDist_H or int(RelativeVertical) < AlarmDist_V or int(RelativeVertical) > -AlarmDist_V)) and  float(MySpeed) > int(MinSpeed): 
                #    print("PFLAU RelDist: " + str(RelativeDistance) + " RelVert: " + str(RelativeVertical))
                #    #ActivateFlasher = True

                if AlarmLevel != "0": 
                    print("PFLAU TX: " + str(TX))
                    ActivateFlasher = True
                elif int(RelativeDistance) < AlarmDist_H and (int(RelativeVertical) < AlarmDist_V or int(RelativeVertical) > -AlarmDist_V) and GPS == 2:
                    ActivateFlasher = True
    
    
    if time.time() > (timeout + no_comm_time):
        ActivateFlasher = True

    if (Deactivate_Pin.value() == 1 and tajm == 0) or ActivateFlasher:
        tajm = time.time()

    if ActivateFlasher or time.time() < (tajm + 10):
        Deactivate_Pin.value(0)
        #print("Alarming")
    else:
        Deactivate_Pin.value(1)
        #print("yy")
        tajm = 0

    ActivateFlasher = False

    time.sleep(0.1)

    #print("remains = " + MessageFromNMEAPort)












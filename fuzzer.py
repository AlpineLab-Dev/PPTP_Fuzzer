
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
        raise ValueError("startControlSession error")
    return pocClient

def stopControlSession(client : CtlClient):
    initializeCtlConnection = StopControlConnectionRequest()
    client.CtlSendMsg(initializeCtlConnection)
    StopControlReply_raw = client.CtlRecvMsg()
    initializeCtlResponse = StopControlConnectionReply(packetBytes=StopControlReply_raw)
    if initializeCtlResponse.ErrorCode != 0 or initializeCtlResponse.ResultCode != 1:
        raise ValueError("stopControlSession error")
    
def echoTest(client : CtlClient):
    EchoRequestMsg = EchoRequest()
    client.CtlSendMsg(EchoRequestMsg)
    EchoReply_raw = client.CtlRecvMsg()
    EchoResponse = EchoReply(packetBytes=EchoReply_raw)
    if EchoResponse.ErrorCode != 0 or EchoResponse.ResultCode != 1:
        raise ValueError("echoTest error")
    
def OutgoingCallTest(client : CtlClient):
    newOutgoingCallRequest = OutgoingCallRequest()
    client.CtlSendMsg(newOutgoingCallRequest)
    OutgoingCallReply_raw = client.CtlRecvMsg()
    newOutgoingCallReply = OutgoingCallReply(packetBytes=OutgoingCallReply_raw)
    if newOutgoingCallReply.ResultCode != 1 or newOutgoingCallReply.ErrorCode != 0:
        raise ValueError("OutgoingCallTest error ")

def IncomingCallTest(client : CtlClient):
    newCallId = secrets.randbelow(0x10000)
    newCallSerial = secrets.randbelow(0x10000)
    newIncomingCallRequest = IncomingCallRequest(CallId=newCallId, CallSerialNumber=newCallSerial)
    client.CtlSendMsg(newIncomingCallRequest)
    IncomingCallReply_raw = client.CtlRecvMsg()
    newIncomingCallReply = IncomingCallReply(packetBytes=IncomingCallReply_raw)
    
    if newIncomingCallReply.ResultCode != 1 or newIncomingCallReply.ErrorCode != 0:
        raise ValueError("newIncomingCallRequest/Reply error ")

    newIncomingCallConnected = IncomingCallConnected(newIncomingCallReply.CallId, 64, newIncomingCallReply.PacketRecvWindowSize, newIncomingCallReply.PacketTransitDelay)
    client.CtlSendMsg(newIncomingCallConnected)

def CallClearRequestTest(client : CtlClient):
    newCallClearRequest = CallClearRequest()
    client.CtlSendMsg(newCallClearRequest)

def CallDisconnectNotifyTest(client : CtlClient):
    newCallDisconnectNotify = CallDisconnectNotify()
    client.CtlSendMsg(newCallDisconnectNotify)

def WANErrorNotifyTest(client : CtlClient):
    newWANErrorNotify = WANErrorNotify()
    client.CtlSendMsg(newWANErrorNotify)

def SetLinkInfoTest(client : CtlClient):
    newSetLinkInfo = SetLinkInfo()
    client.CtlSendMsg(newSetLinkInfo)


# def poke_server():

#     try:
#         print("[+] Pokeing the target....")
#         poke_client = CtlClient(TEST_SERVER)
#         poke_client.CtlConnect(timeout=1)
#         print("[-] Its alive!?")
    
#     except Exception as e:
#         print("[+] Yep, its dead")


def test():
    client = startControlSession()
    # echoTest(client)
    # OutgoingCallTest(client)
    # IncomingCallTest(client)
    # CallClearRequestTest(client) # 진입 X, PNS to PAC
    # CallDisconnectNotifyTest(client) # CtlpEngine의 분기까지 진입하나 CallEventCallDisconnectNotify 함수 진입 불가
    # WANErrorNotifyTest(client) # CtlpEngine 분기까지 진입
    # SetLinkInfoTest(client) # 진입 X, PNS to PAC
    stopControlSession(client)

def main():
    global TEST_SERVER
    global CTL_PORT

    parser = argparse.ArgumentParser(description="this is simple PPTP_Fuzzer")
    parser.add_argument('--ip', type=str,required=True,dest="ip_address",help="IP address of the target server")
    parser.add_argument('--port', type=int, default=CTL_PORT,dest="ctl_port", help="Port of the PPTP CTL TCP socket, should remain as {} in most cases.".format(CTL_PORT))

    args = parser.parse_args()

    TEST_SERVER = args.ip_address
    CTL_PORT = args.ctl_port

    continue_to_trigger = input("[?] Start Test? [y/n]: ")

    if continue_to_trigger.lower() == "y":
        test()
    else:
        print("[+] GoodBye!")

if __name__ == '__main__':
    main()

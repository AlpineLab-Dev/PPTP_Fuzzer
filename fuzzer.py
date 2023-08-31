import socket
import select
import argparse
import random
import threading
import logging
import uuid

from packets import *
from utils import *

logging.basicConfig(level=logging.INFO)

CTL_PORT = 1723
TEST_SERVER = ""

payload = list()


class CtlClient:
    def __init__(self, serverIp, serverPort=CTL_PORT):
        self.IP = serverIp
        self.Port = serverPort

        self.Socket = None
        self.IsConnected = False

    def CtlCloseConn(self):
        self.Socket.close()

    def CtlSendMsg(self, CtlMessage, multiplier=1):
        global payload

        if not self.IsConnected:
            raise RuntimeError("Attempted to send Ctl data on unconnected client")

        ctlmsgbuf: bytes = CtlMessage.build() * multiplier

        payload.append(ctlmsgbuf)

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

            while len(chunk) == 1024:
                chunk = self.Socket.recv(1024)
                chunks.append(chunk)

        return b"".join(chunks)

    def CtlConnect(self, timeout=None):
        # Connect to the Ctl server
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
    initializeCtlResponse = StartControlConnectionReply(
        packetBytes=StartControlReply_raw
    )

    if initializeCtlResponse.ErrorCode != 0 or initializeCtlResponse.ResultCode != 1:
        logging.error("startControlSession error")
        return None
    return pocClient


def stopControlSession(client: CtlClient):
    initializeCtlConnection = StopControlConnectionRequest()
    client.CtlSendMsg(initializeCtlConnection)
    StopControlReply_raw = client.CtlRecvMsg()
    initializeCtlResponse = StopControlConnectionReply(packetBytes=StopControlReply_raw)
    if initializeCtlResponse.ErrorCode != 0 or initializeCtlResponse.ResultCode != 1:
        logging.error("stopControlSession error")


def echoTest(client: CtlClient, mutate_level: int = 0):
    EchoRequestMsg = EchoRequest()
    match mutate_level:
        case 0:
            client.CtlSendMsg(EchoRequestMsg)
        case 1:
            EchoRequestMsg.Identifier = rand_u16()
            client.CtlSendMsg(EchoRequestMsg)
        case 2:
            # TODO: Full random
            client.CtlSendMsg(EchoRequestMsg)
        case 3:
            client.CtlSendMsg(EchoRequestMsg, random.randint(2, 5))
    client.CtlRecvMsg()


def OutgoingCallTest(client: CtlClient, mutate_level: int = 0):
    newOutgoingCallRequest = OutgoingCallRequest()
    match mutate_level:
        case 0:
            client.CtlSendMsg(newOutgoingCallRequest)
        case 1:
            newOutgoingCallRequest.CallID = rand_u16()
            newOutgoingCallRequest.CallSerialNumber = rand_u16()
            newOutgoingCallRequest.MinimumBPS = rand_u32()
            newOutgoingCallRequest.MaximumBPS = rand_u32()
            newOutgoingCallRequest.BearerType = rand_u32()
            newOutgoingCallRequest.FramingType = rand_u32()
            newOutgoingCallRequest.WindowSize = rand_u16()
            newOutgoingCallRequest.PPD = rand_u16()
            newOutgoingCallRequest.PhoneNumberLength = rand_u16()
            newOutgoingCallRequest.Reserved1 = rand_u16()
            newOutgoingCallRequest.PhoneNumber = rand_octet(64)
            newOutgoingCallRequest.Subaddress = rand_octet(64)
            client.CtlSendMsg(newOutgoingCallRequest)
        case 2:
            # TODO: Full random
            client.CtlSendMsg(newOutgoingCallRequest)
        case 3:
            client.CtlSendMsg(newOutgoingCallRequest, random.randint(2, 5))
    client.CtlRecvMsg()


def IncomingCallTest(client: CtlClient, mutate_level: int = 0):
    newCallID = rand_u16()
    newCallSerial = rand_u16()
    newIncomingCallRequest = IncomingCallRequest(
        CallID=newCallID, CallSerialNumber=newCallSerial
    )

    match mutate_level:
        case 0:
            client.CtlSendMsg(newIncomingCallRequest)
        case 1:
            newIncomingCallRequest.CallID = rand_u16()
            newIncomingCallRequest.CallSerialNumber = rand_u16()
            newIncomingCallRequest.CallBearerType = rand_u32()
            newIncomingCallRequest.PhysicalChannelId = rand_u32()
            newIncomingCallRequest.DialedNumberLength = rand_u16()
            newIncomingCallRequest.DialingNumberLength = rand_u16()
            newIncomingCallRequest.DialedNumber = rand_octet(64)
            newIncomingCallRequest.DialingNumber = rand_octet(64)
            newIncomingCallRequest.Subaddress = rand_octet(64)
            client.CtlSendMsg(newIncomingCallRequest)
        case 2:
            # TODO: Full random
            client.CtlSendMsg(newIncomingCallRequest)
        case 3:
            client.CtlSendMsg(newIncomingCallRequest, random.randint(2, 5))

    try:
        IncomingCallReply_raw = client.CtlRecvMsg()
        newIncomingCallReply = IncomingCallReply(packetBytes=IncomingCallReply_raw)

        newIncomingCallConnected = IncomingCallConnected(
            newIncomingCallReply.CallID,
            64,
            newIncomingCallReply.PacketRecvWindowSize,
            newIncomingCallReply.PacketTransitDelay,
        )
        match mutate_level:
            case 0:
                client.CtlSendMsg(newIncomingCallConnected)
            case 1:
                newIncomingCallConnected.PeerCallID = rand_u16()
                newIncomingCallConnected.Reserved1 = rand_u16()
                newIncomingCallConnected.ConnectSpeed = rand_u32()
                newIncomingCallConnected.PacketRecvWindowSize = rand_u16()
                newIncomingCallConnected.PacketTransmitDelay = rand_u16()
                newIncomingCallConnected.FramingType = rand_u32()
                client.CtlSendMsg(newIncomingCallConnected)
            case 2:
                # TODO: Full random
                client.CtlSendMsg(newIncomingCallConnected)
            case 3:
                client.CtlSendMsg(newIncomingCallConnected, random.randint(2, 5))
        client.CtlRecvMsg()
    except Exception:
        pass


def CallClearRequestTest(client: CtlClient, mutate_level: int = 0):
    newCallClearRequest = CallClearRequest()

    match mutate_level:
        case 0:
            client.CtlSendMsg(newCallClearRequest)
        case 1:
            newCallClearRequest.CallID = rand_u16()
            newCallClearRequest.reserved1 = rand_u16()
            client.CtlSendMsg(newCallClearRequest)
        case 2:
            # TODO: Full random
            client.CtlSendMsg(newCallClearRequest)
        case 3:
            client.CtlSendMsg(newCallClearRequest, random.randint(2, 5))
    client.CtlRecvMsg()


def CallDisconnectNotifyTest(client: CtlClient, mutate_level: int = 0):
    newCallDisconnectNotify = CallDisconnectNotify()

    match mutate_level:
        case 0:
            client.CtlSendMsg(newCallDisconnectNotify)
        case 1:
            newCallDisconnectNotify.CallID = rand_u16()
            newCallDisconnectNotify.ResultCode = rand_u8()
            newCallDisconnectNotify.ErrorCode = rand_u8()
            newCallDisconnectNotify.CauseCode = rand_u16()
            newCallDisconnectNotify.Reserved1 = rand_u16()
            newCallDisconnectNotify.CallStatistics = rand_octet(128)
            client.CtlSendMsg(newCallDisconnectNotify)
        case 2:
            # TODO: Full random
            client.CtlSendMsg(newCallDisconnectNotify)
        case 3:
            client.CtlSendMsg(newCallDisconnectNotify, random.randint(2, 5))
    client.CtlRecvMsg()


def WANErrorNotifyTest(client: CtlClient, mutate_level: int = 0):
    newWANErrorNotify = WANErrorNotify()

    match mutate_level:
        case 0:
            client.CtlSendMsg(newWANErrorNotify)
        case 1:
            newWANErrorNotify.PeersCallID = rand_u16()
            newWANErrorNotify.Reserved1 = rand_u16()
            newWANErrorNotify.CRCErrors = rand_u32()
            newWANErrorNotify.FramingErrors = rand_u32()
            newWANErrorNotify.HardwareOverruns = rand_u32()
            newWANErrorNotify.BufferOverruns = rand_u32()
            newWANErrorNotify.TimeOutOverruns = rand_u32()
            newWANErrorNotify.AlignmentOverruns = rand_u32()
            client.CtlSendMsg(newWANErrorNotify)
        case 2:
            # TODO: Full random
            client.CtlSendMsg(newWANErrorNotify)
        case 3:
            client.CtlSendMsg(newWANErrorNotify, random.randint(2, 5))
    client.CtlRecvMsg()


def SetLinkInfoTest(client: CtlClient, mutate_level: int = 0):
    newSetLinkInfo = SetLinkInfo()

    match mutate_level:
        case 0:
            client.CtlSendMsg(newSetLinkInfo)
        case 1:
            newSetLinkInfo.PeersCallID = rand_u16()
            newSetLinkInfo.Reserved1 = rand_u16()
            newSetLinkInfo.SendACCM = rand_u32()
            newSetLinkInfo.ReceiveACCM = rand_u32()
            client.CtlSendMsg(newSetLinkInfo)
        case 2:
            # TODO: Full random
            client.CtlSendMsg(newSetLinkInfo)
        case 3:
            client.CtlSendMsg(newSetLinkInfo, random.randint(2, 5))
    client.CtlRecvMsg()


def do_stuff():
    client = startControlSession()

    if client is None:
        return

    for _ in range(random.randint(1, 5)):
        match random.randint(0, 6):
            case 0:
                echoTest(client, random.randint(0, 3))
            case 1:
                OutgoingCallTest(client, random.randint(0, 3))
            case 2:
                IncomingCallTest(client, random.randint(0, 3))
            case 3:
                # 진입 X, PNS to PAC
                CallClearRequestTest(client, random.randint(0, 3))
            case 4:
                # CtlpEngine의 분기까지 진입하나
                # CallEventCallDisconnectNotify 함수 진입 불가
                CallDisconnectNotifyTest(client, random.randint(0, 3))
            case 5:
                # CtlpEngine 분기까지 진입
                WANErrorNotifyTest(client, random.randint(0, 3))
            case 6:
                # 진입 X, PNS to PAC
                SetLinkInfoTest(client, random.randint(0, 3))

    stopControlSession(client)


def main():
    global TEST_SERVER
    global CTL_PORT
    global payload

    parser = argparse.ArgumentParser(description="this is simple PPTP_Fuzzer")
    parser.add_argument(
        "--ip",
        type=str,
        required=True,
        dest="ip_address",
        help="IP address of the target server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=CTL_PORT,
        dest="ctl_port",
        help=f"Port of the PPTP CTL TCP socket, should remain as {CTL_PORT} in most cases.",
    )

    args = parser.parse_args()

    TEST_SERVER = args.ip_address
    CTL_PORT = args.ctl_port

    while True:
        thread_num = random.randint(1, 5)
        thread_list = list()
        for _ in range(thread_num):
            th = threading.Thread(target=do_stuff)
            th.start()
            thread_list.append(th)

        for th in thread_list:
            th.join()

        try:
            logging.info("Health check...")
            poke_client = CtlClient(TEST_SERVER)
            poke_client.CtlConnect(timeout=1)
            logging.info("Server is still healty...")
        except Exception:
            logging.warning("Server is dead!")
            with open(f"{str(uuid.uuid4())}.log", "wb") as f:
                f.write(b"\n".join(payload))
                payload.clear()


if __name__ == "__main__":
    main()

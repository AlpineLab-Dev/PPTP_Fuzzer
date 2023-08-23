import struct

# CTL Message Types
#   Control Connection Management
gStartControlConnectionRequest  = 1
gStartControlConnectionReply  = 2
gStopControlConnectionRequest  = 3
gStopControlConnectionReply  = 4
gEchoRequest  = 5
gEchoReply  = 6

#   Call Management
gOutgoingCallRequest = 7
gOutgoingCallReply = 8
gIncomingCallRequest  = 9
gIncomingCallReply  = 10
gIncomingCallConnected  = 11
gCallClearRequest = 12
gCallDisconnectNotify = 13

#   Error Reporting
gWANErrorNotify = 14

#   PPP Session Control
gSetLinkInfo = 15

# Framing Capabillities
gAsynchronousFraming = 0x1
gSynchronousFraming = 0x2

# Bearer Capabillities
gAnalogAccessSupported = 0x1
gDigitalAccessSupported = 0x2

class ControlMessage():
    SIZE = 0xC # 12 byte header
    def __init__(self, messageType, messageLength, setSize=False, packetBytes=None):
        if packetBytes:
            self.MessageLength = 0
            self.PptpMessageType = 0
            #Magic number
            self.CtlMagic = 0
            self.CtlMessageType = 0
            self.Reserved0 = 0
            self.SetSize = 0
            self.__fromBytes(packetBytes)
        else:
            self.MessageLength = messageLength
            self.PptpMessageType = 0x1
            #Magic number
            self.CtlMagic = 0x1A2B3C4D
            self.CtlMessageType = messageType 
            self.Reserved0 = 0
            self.SetSize = setSize

    def build(self):
        buffer = b""
        if self.SetSize:
            # Use the preconfigured set size for this packet
            self.MessageLength = self.__SIZE
        buffer += struct.pack(">H", self.MessageLength)
        buffer += struct.pack(">H", self.PptpMessageType)
        buffer += struct.pack(">I", self.CtlMagic)
        buffer += struct.pack(">H", self.CtlMessageType)
        buffer += struct.pack(">H", self.Reserved0)
        return buffer
    
    def __fromBytes(self, bytebuffer):
        header = struct.unpack_from(">HHIHH", bytebuffer, 0)
        self.MessageLength = header[0]
        self.PptpMessageType = header[1]
        self.CtlMagic = header[2]
        self.CtlMessageType = header[3]
        self.Reserved0 = header[4]

class StartControlConnectionRequest(ControlMessage):
    SIZE = 0x90
    def __init__(self, framing=gAsynchronousFraming, bearer=gAnalogAccessSupported, maxChannels=0x0, firmwareRevision=0x0, hostName=b"A" * 64, vendorString=b"B" * 64):
        
        super().__init__(gStartControlConnectionRequest, ControlMessage.SIZE + StartControlConnectionRequest.SIZE)
        self.protocolVersion = 0x100       
        self.Reserved1 = 0
        self.FramingCapabilities = framing
        self.BearerCapabilities = bearer
        self.MaxChannels = maxChannels
        self.FirmwareRevision = firmwareRevision
        self.HostName = hostName # 64 byte host name string 
        self.VendorString = vendorString # 64 byte vendor string
        
    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.protocolVersion)
        buffer += struct.pack(">H", self.Reserved1)
        buffer += struct.pack(">I", self.FramingCapabilities) 
        buffer += struct.pack(">I", self.BearerCapabilities)
        buffer += struct.pack(">H", self.MaxChannels)
        buffer += struct.pack(">H", self.FirmwareRevision)
        buffer += self.HostName
        buffer += self.VendorString

        return header + buffer

class StartControlConnectionReply(ControlMessage):
    SIZE = 0x90
    def __init__(self, framing=gAsynchronousFraming, bearer=gAnalogAccessSupported, maxChannels=0x0, firmwareRevision=0x0, hostName=b"A" * 64, vendorString=b"B" * 64, resultCode=0, errorCode=0, packetBytes=None):
        
        super().__init__(gStartControlConnectionReply, ControlMessage.SIZE + StartControlConnectionReply.SIZE, packetBytes=packetBytes)
        if packetBytes:
            self.protocolVersion = 0       
            self.ResultCode = 0
            self.ErrorCode = 0
            self.FramingCapabilities = 0
            self.BearerCapabilities = 0
            self.MaxChannels = 0
            self.FirmwareRevision = 0
            self.HostName = 0 # 64 byte host name string 
            self.VendorString = 0 # 64 byte vendor string
            self.__fromBytes(packetBytes)
        else:
            self.protocolVersion = 0x100       
            self.ResultCode = resultCode
            self.ErrorCode = errorCode
            self.FramingCapabilities = framing
            self.BearerCapabilities = bearer
            self.MaxChannels = maxChannels
            self.FirmwareRevision = firmwareRevision
            self.HostName = hostName # 64 byte host name string 
            self.VendorString = vendorString # 64 byte vendor string
        
    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.protocolVersion)
        buffer += struct.pack(">B", self.ResultCode)
        buffer += struct.pack(">B", self.ErrorCode)
        buffer += struct.pack(">I", self.FramingCapabilities) 
        buffer += struct.pack(">I", self.BearerCapabilities)
        buffer += struct.pack(">H", self.MaxChannels)
        buffer += struct.pack(">H", self.FirmwareRevision)
        buffer += self.HostName
        buffer += self.VendorString
        return header + buffer
    
    def __fromBytes(self, bytebuffer):
        items = struct.unpack_from(">HBBIIHH", bytebuffer, ControlMessage.SIZE)
        self.protocolVersion = items[0]
        self.ResultCode = items[1]
        self.ErrorCode = items[2]
        self.FramingCapabilities = items[3]
        self.BearerCapabilities = items[4]
        self.MaxChannels = items[5]
        self.FirmwareRevision = items[6]

class StopControlConnectionRequest(ControlMessage):
    SIZE = 0x4
    def __init__(self):
        super().__init__(gStopControlConnectionRequest, ControlMessage.SIZE + StopControlConnectionRequest.SIZE)
        # Reason
        #   1 (None) - General request to clear control connection
        #   2 (Stop-Protocol) - Can't support peer's version of the protocol
        #   3 (Stop-Local-Shutdown) - Requester is being shut down
        self.Reason = 0        
        self.Reserved1 = 0 # Reserved1,2 MUST BE 0
        self.Reserved2 = 0
        
    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">B", self.Reason)
        buffer += struct.pack(">B", self.Reserved1)
        buffer += struct.pack(">H", self.Reserved2) 
        return header + buffer
    
class StopControlConnectionReply(ControlMessage):
    SIZE = 0x4
    def __init__(self, ResultCode = 0, ErrorCode = 0, packetBytes=None):
        super().__init__(gStopControlConnectionReply, ControlMessage.SIZE + StopControlConnectionReply.SIZE)
        # Reason
        #   1 (None) - General request to clear control connection
        #   2 (Stop-Protocol) - Can't support peer's version of the protocol
        #   3 (Stop-Local-Shutdown) - Requester is being shut down
        if packetBytes:
            self.ResultCode = 0        
            self.ErrorCode = 0
            self.__fromBytes(packetBytes)
        else:
            self.ResultCode = ResultCode
            self.ErrorCode = ErrorCode
        self.Reserved1 = 0
        
    def build(self):
        buffer = b""
        header = super().build()
        # ResultCode
        # 1 (OK)
        # 2 (General Error)
        buffer += struct.pack(">B", self.ResultCode)
        buffer += struct.pack(">B", self.ErrorCode)
        buffer += struct.pack(">H", self.Reserved1) 
        return header + buffer
    
    def __fromBytes(self, bytebuffer):
        items = struct.unpack_from(">BBH", bytebuffer, ControlMessage.SIZE)
        self.ResultCode = items[0]
        self.ErrorCode = items[1]
 
    
class EchoRequest(ControlMessage):
    SIZE = 0x4
    def __init__(self):
        super().__init__(gEchoRequest, ControlMessage.SIZE + EchoRequest.SIZE)
        # set by the sender
        self.Identifier = 0x41414141
        
    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">I", self.Identifier)
        return header + buffer
    
class EchoReply(ControlMessage):
    SIZE = 0x8
    def __init__(self, Identifier = 0, ResultCode = 0, ErrorCode = 0, packetBytes = None):
        super().__init__(gEchoReply, ControlMessage.SIZE + EchoReply.SIZE)
        # set by the sender
        if packetBytes:
            self.Identifier = 0
            self.ResultCode = 0        
            self.ErrorCode = 0
            self.__fromBytes(packetBytes)
        else:
            self.Identifier = Identifier
            self.ResultCode = ResultCode
            self.ErrorCode = ErrorCode

        self.Reserved1 = 0 # Reserved1 MUST BE 0
        
    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">I", self.Identifier)
        buffer += struct.pack(">B", self.ResultCode)
        buffer += struct.pack(">B", self.ErrorCode)
        buffer += struct.pack(">H", self.Reserved1) 
        return header + buffer
    
    def __fromBytes(self, bytebuffer):
        items = struct.unpack_from(">IBBH", bytebuffer, ControlMessage.SIZE)
        self.Identifier = items[0]
        self.ResultCode = items[1]
        self.ErrorCode = items[2]

class OutgoingCallRequest(ControlMessage):
    SIZE = 0xA0
    def __init__(self):
        super().__init__(gOutgoingCallRequest, OutgoingCallRequest.SIZE + ControlMessage.SIZE)
        self.CallId = 2337
        self.CallSerialNumber = 2338
        self.minimumBPS = 64
        self.maximumBPS = 128
        self.bearerType = 3 # [1, 2, 3]
        self.framingType = 3 # [1, 2, 3]
        self.windowSize = 1024
        self.PPD = 64
        self.PhoneNumberLength = 64
        self.Reserved1 = 0
        self.PhoneNumber = b'C' * 64
        self.Subaddress = b'D' * 64

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.CallId)
        buffer += struct.pack(">H", self.CallSerialNumber)
        buffer += struct.pack(">I", self.minimumBPS)
        buffer += struct.pack(">I", self.maximumBPS)
        buffer += struct.pack(">I", self.bearerType)
        buffer += struct.pack(">I", self.framingType)
        buffer += struct.pack(">H", self.windowSize)
        buffer += struct.pack(">H", self.PPD)
        buffer += struct.pack(">H", self.PhoneNumberLength)
        buffer += struct.pack(">H", self.Reserved1)
        buffer += self.PhoneNumber
        buffer += self.Subaddress
        return header + buffer

class OutgoingCallReply(ControlMessage):
    SIZE = 0x14
    def __init__(self, CallID = 0, PeersCallID = 0, ResultCode = 0, ErrorCode = 0, CauseCode = 0, ConnectSpeed = 0, WindowSize = 0, PPD = 0, PCID = 0, packetBytes = None):
        super().__init__(gOutgoingCallReply, OutgoingCallReply.SIZE + ControlMessage.SIZE)
        if packetBytes:
            self.CallId = 0
            self.PeersCallID = 0
            self.ResultCode = 0
            self.ErrorCode = 0
            self.CauseCode = 0
            self.ConnectSpeed = 0
            self.WindowSize = 0
            self.PPD = 0
            self.PCID = 0
            self.fromBytes(packetBytes)
        else:
            self.CallId = CallID
            self.PeersCallID = PeersCallID
            self.ResultCode = ResultCode
            self.ErrorCode = ErrorCode
            self.CauseCode = CauseCode
            self.ConnectSpeed = ConnectSpeed
            self.WindowSize = WindowSize
            self.PPD = PPD
            self.PCID = PCID

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.CallId)
        buffer += struct.pack(">H", self.PeersCallID)
        buffer += struct.pack(">B", self.ResultCode)
        buffer += struct.pack(">B", self.ErrorCode)
        buffer += struct.pack(">H", self.CauseCode)
        buffer += struct.pack(">I", self.ConnectSpeed)
        buffer += struct.pack(">H", self.WindowSize)
        buffer += struct.pack(">H", self.PPD)
        buffer += struct.pack(">I", self.PCID)
        return header + buffer
    
    def fromBytes(self, bytebuffer):
        items = struct.unpack_from(">HHBBHIHHI", bytebuffer, ControlMessage.SIZE)
        self.CallId = items[0]
        self.PeersCallID = items[1]
        self.ResultCode = items[2]
        self.ErrorCode = items[3]
        self.CauseCode = items[4]
        self.ConnectSpeed = items[5]
        self.WindowSize = items[6]
        self.PPD = items[7]
        self.PCID = items[8]

class IncomingCallRequest(ControlMessage):
    SIZE = 0xD0
    def __init__(self,CallId=1337, CallSerialNumber=1338, CallBearerType=gAnalogAccessSupported, PhysicalChannelId=0, DialedNumberLength=64, DialingNumberLength=64,DialedNumber=64 *b"A", DialingNumber = 64 * b"B", Subaddress= 64 * b"C"):
        super().__init__(gIncomingCallRequest, IncomingCallRequest.SIZE + ControlMessage.SIZE)
        self.CallId = CallId
        self.CallSerialNumber = CallSerialNumber
        self.CallBearerType = CallBearerType
        self.PhysicalChannelId = PhysicalChannelId
        self.DialedNumberLength = DialedNumberLength
        self.DialingNumberLength = DialingNumberLength
        self.DialedNumber = DialedNumber
        self.DialingNumber = DialingNumber
        self.Subaddress = Subaddress

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.CallId)
        buffer += struct.pack(">H", self.CallSerialNumber)
        buffer += struct.pack(">I", self.CallBearerType)
        buffer += struct.pack(">I", self.PhysicalChannelId)
        buffer += struct.pack(">H", self.DialedNumberLength)
        buffer += struct.pack(">H", self.DialingNumberLength)
        buffer += self.DialedNumber
        buffer += self.DialingNumber
        buffer += self.Subaddress
        return header + buffer

class IncomingCallReply(ControlMessage):
    SIZE = 0xC
    def __init__(self,CallId=0x1337, PeersCallId=0x1338, ResultCode=1, ErrorCode=0, PacketRecvWindowSize=64, PacketTransitDelay=32, packetBytes=None):
        super().__init__(gIncomingCallReply, IncomingCallReply.SIZE + ControlMessage.SIZE, packetBytes=packetBytes)
        if packetBytes:
            self.CallId = 0
            self.PeersCallId = 0
            self.ResultCode = 0
            self.ErrorCode = 0
            self.PacketRecvWindowSize = 0,
            self.PacketTransitDelay = 0
            self.Reserved1 = 0
            self.fromBytes(packetBytes)
        else:
            self.CallId = CallId
            self.PeersCallId = PeersCallId
            self.ResultCode = ResultCode
            self.ErrorCode = ErrorCode
            self.PacketRecvWindowSize = PacketRecvWindowSize,
            self.PacketTransitDelay = PacketTransitDelay
            self.Reserved1 = 0

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.CallId)
        buffer += struct.pack(">H", self.PeersCallId)
        buffer += struct.pack(">B", self.ResultCode)
        buffer += struct.pack(">B", self.ErrorCode)
        buffer += struct.pack(">H", self.PacketRecvWindowSize)
        buffer += struct.pack(">H", self.PacketTransitDelay)
        buffer += struct.pack(">H", self.Reserved1)
        return header + buffer
        
    def fromBytes(self, bytebuffer):
        items = struct.unpack_from(">HHBBHHH", bytebuffer, ControlMessage.SIZE)
        self.CallId = items[0]
        self.PeersCallId = items[1]
        self.ResultCode = items[2]
        self.ErrorCode = items[3]
        self.PacketRecvWindowSize = items[4]
        self.PacketTransitDelay = items[5]
        self.Reserved1 = items[6]

class IncomingCallConnected(ControlMessage):
    SIZE = 0x10
    def __init__(self,PeerCallId=1337, ConnectSpeed=1, PacketRecvWindowsSize=64, PacketTransmitDelay=0, FramingType = gAsynchronousFraming, packetBytes=None):
        super().__init__(gIncomingCallConnected, IncomingCallConnected.SIZE + ControlMessage.SIZE, packetBytes=packetBytes)
        
        if packetBytes:
            pass
        else:
            self.PeerCallId = PeerCallId
            self.Reserved1 = 0
            self.ConnectSpeed = ConnectSpeed
            self.PacketRecvWindowSize = PacketRecvWindowsSize
            self.PacketTransmitDelay = PacketTransmitDelay
            self.FramingType = FramingType
    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.PeerCallId)
        buffer += struct.pack(">H", self.Reserved1)
        buffer += struct.pack(">I", self.ConnectSpeed)
        buffer += struct.pack(">H", self.PacketRecvWindowSize)
        buffer += struct.pack(">H", self.PacketTransmitDelay)
        buffer += struct.pack(">I", self.FramingType)

        return header + buffer

class CallClearRequest(ControlMessage):
    SIZE = 0x4
    def __init__(self, packetBytes = None, callid = 1337):
        super().__init__(gCallClearRequest, CallClearRequest.SIZE + ControlMessage.SIZE)
        if packetBytes:
            self.callid = 0
            self.reserved1 = 0
            self.fromBytes()
        else:
            self.callid = callid
            self.reserved1 = 0

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.callid)
        buffer += struct.pack(">H", self.reserved1)
        return header + buffer
    
    def fromBytes(self, bytebuffer):
        items = struct.unpack_from(">H", bytebuffer, ControlMessage.SIZE)
        self.callid = items[0]
    
class CallDisconnectNotify(ControlMessage):
    SIZE = 0x88
    def __init__(self):
        super().__init__(gCallDisconnectNotify, CallDisconnectNotify.SIZE + ControlMessage.SIZE)
        self.callid = 1337
        self.ResultCode = 0 # [1, 2, 3, 4]
        self.ErrorCode = 0
        self.CauseCode = 0
        self.Reserved1 = 1
        self.CallStatistics = b"A" * 128

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.callid)
        buffer += struct.pack(">B", self.ResultCode)
        buffer += struct.pack(">B", self.ErrorCode)
        buffer += struct.pack(">H", self.CauseCode)
        buffer += struct.pack(">H", self.Reserved1)
        buffer += self.CallStatistics
        return header + buffer

class WANErrorNotify(ControlMessage):
    SIZE = 0x1c
    def __init__(self):
        super().__init__(gWANErrorNotify, WANErrorNotify.SIZE + ControlMessage.SIZE)
        self.PeersCallID = 1337
        self.Reserved1 = 0 # [1, 2, 3, 4]
        self.CRCErrors = 1024
        self.FramingErrors = 1024
        self.HardwareOverruns = 1024
        self.BufferOverruns = 1024
        self.TimeOutOverruns = 32
        self.AlignmentOverruns = 64

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.PeersCallID)
        buffer += struct.pack(">H", self.Reserved1)
        buffer += struct.pack(">I", self.CRCErrors)
        buffer += struct.pack(">I", self.FramingErrors)
        buffer += struct.pack(">I", self.HardwareOverruns)
        buffer += struct.pack(">I", self.BufferOverruns)
        buffer += struct.pack(">I", self.TimeOutOverruns)
        buffer += struct.pack(">I", self.AlignmentOverruns)
        return header + buffer

class SetLinkInfo(ControlMessage):
    SIZE = 0xc
    def __init__(self, PeersCallID = 1337,SendACCM = 0XFFFFFFFF, ReceiveACCM = 0XFFFFFFFF, packetBytes = None):
        super().__init__(gSetLinkInfo, SetLinkInfo.SIZE + ControlMessage.SIZE)
        if packetBytes:
            self.PeersCallID = 0
            self.Reserved1 = 0 # [1, 2, 3, 4]
            self.SendACCM = 0
            self.ReceiveACCM = 0
            self.fromBytes()

        else:
            self.PeersCallID = PeersCallID
            self.Reserved1 = 0 # [1, 2, 3, 4]
            self.SendACCM = SendACCM
            self.ReceiveACCM = ReceiveACCM

    def build(self):
        buffer = b""
        header = super().build()
        buffer += struct.pack(">H", self.PeersCallID)
        buffer += struct.pack(">H", self.Reserved1)
        buffer += struct.pack(">I", self.SendACCM)
        buffer += struct.pack(">I", self.ReceiveACCM)
        return header + buffer
    
    def fromBytes(self, bytebuffer):
        items = struct.unpack_from(">HHII", bytebuffer, ControlMessage.SIZE)
        self.PeersCallID = items[0]
        self.SendACCM = items[2]
        self.ReceiveACCM = items[3]
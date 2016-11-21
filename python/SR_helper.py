import sys
import pprint
from packet import Packet

PAYLOAD_MAX_SIZE = 1013      # bytes

# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = 5


def prepare_SR(peer_ip, server_port, payload):

    # encode before | after we split

    packets = {}
    seq_num = 0

    with open("temp.bin", "wb") as f:
        f.write(bytes(payload, "utf-8"))

    with open("temp.bin", "rb") as f:
        payload = f.read(PAYLOAD_MAX_SIZE)

        while payload != b"":

            p = Packet(packet_type=DATA,
                       seq_num=seq_num,
                       peer_ip_addr=peer_ip,
                       peer_port=server_port,
                       payload=payload)
        
            packets[seq_num] = p
            seq_num += 1
            payload = f.read(PAYLOAD_MAX_SIZE)

    print ("HTTP request|response broken into 1013-byte Packets[]")
    for k,v in packets.items():
        print (k, ":", sys.getsizeof(v), " bytes")
        pprint.pprint(vars(v))


    return packets


def SR_to_appmessage(packets):

    # get Packet[] array from SR then package together into original form
    # as HTTP request | response

    http_message = ""

    # we assume all of them have the same host:port
    
    # pprint.pprint(packets[0])
    # print(packets[0].payload)
    # print(type(packets))
    # print(type(packets[0]))
    # print(packets[0].payload.decode("utf-8"))
    peer_ip = packets[0].peer_ip_addr
    server_port = packets[0].peer_port

    # with open("temp.bin", "rb"):
    for p in packets:
        http_message += p.payload.decode("utf-8")
         

    print("HTTP message assembled from SR:")
    print(http_message)


    return http_message, peer_ip, server_port


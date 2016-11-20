import time
from packet import Packet


# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = 5


# [0,1,2,3,4,5,6,7,8]

"""
p = Packet(packet_type=1,
                   seq_num=initial_seq_num,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg.encode("utf-8"))

"""




def sr_receiver(conn):


	packets_received = 0
	expected_packets = 8

	# assume receiver knows that 
	# seq_num range is [0,1,2,3,4,5,6,7]

	buffer = []

	window_size = 4				# static for now
	start_counter = 0

	# init. range [0,1,2,3]
	window_size_range = list(range(start_counter, start_counter+window_size))

	# keep receiving until all packets received and delivered to upper layer
	while (packets_received < expected_packets):

		# check for incoming packets
		response, sender = conn.recvfrom(1024)
		packet = Packet.from_bytes(response)

		# get seq_num
		p_seq_num = packet.seq_num

		# check if seq_num within range
		if p_seq_num in window_size_range:
			

		packet_payload = packet.payload.decode("utf-8")
		
			





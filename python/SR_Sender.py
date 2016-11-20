import time
import json
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


def sr_sender(packets_to_send, router_addr, router_port, server_addr, server_port, conn):

	# packets_to_send is final, it is a representation of HTTP request/response
	# assume it is a list
	# packets_to_send = [p0,p1,p2]
	# assume seq_num is in range [0,1,2,3,4,5,6,7]

	# k = 3
	# 2^k - 1

	window_size = 4				# static for now
	start_counter = 0
	timeout = 5


	packets_success_ctr = 0
	num_packets_to_send = len(packets_to_send)


	# init. range [0,1,2,3]
	window_size_range = list(range(start_counter, start_counter+window_size))


	# start_time = time.time()
	# # your code
	# elapsed_time = time.time() - start_time


	# for each packet make a data_structure like this
	# seq | sent | acked | timer | timedout

	packets = []

	for p in packets_to_send:
		dict1 = {}
		# dict1['seq'] = p.seq_num

		p_seq_num = p.seq_num
		dict1['packet'] = p
		dict1['sent'] = False
		dict1['acked'] = False
		dict1['timer'] = time.time()  # this effectively starts timer for this one
		dict1['timed_out'] = False

		# packets.append(dict1)
		packets[p_seq_num] = dict1

	# packets_sent_unacked = []
	# packets_sent_acked = []

	# keep sending until all packets are sent successfully
	while (packets_success_ctr < num_packets_to_send):
		# p_seq_num = p.seq_num        # for now we assume our start_counter corresponds with packet's seq_num

		# start_timer (packets_to_send[start_counter])

		# [0,1,2,4]
		for j in window_size_range:
			# if  packets[j]['seq'] in window_size_range:

			send_packet = packets[j]['packet']

			# only send if this one is un-acked, and not sent yet or have to be re-sent due to timeout
			if packets[j]['acked'] == False :

				if packets[j]['sent'] == False:
					#send packet
			        conn.sendto(send_packet.to_bytes(), (router_addr, router_port))
			    elif packets[j]['sent'] == True and packets[j]['timed_out'] == True:
					#send packet
			        conn.sendto(send_packet.to_bytes(), (router_addr, router_port))

			        # reset Timer
			        packets[j]['timed_out'] = False
			        packets[j]['timer'] = time.time()

		        packets[start_counter]['sent'] = True
		        # packets_sent_unacked.append(start_counter)

	    # check for acks
	    response, sender = conn.recvfrom(1024)
	    ack_packet = Packet.from_bytes(response)
	    ack_payload = ack_packet.payload.decode("utf-8")
        # get ack from payload
        dict_payload = json.loads(ack_payload)
        ack = dict_payload['ack']


        # check if ack in the window range
        if ack in window_size_range:
        	# if ack is the first in window, i.e. 0 in [0,1,2,3]
        	if ack == start_counter:
        		packets[start_counter]['acked'] = True
        		packets_success_ctr += 1
        		# packets_sent_acked.append(start_counter)

        		# slide window
        		start_counter = (start_counter + 1 ) % window_size
        		window_size_range = list(range(start_counter, start_counter+window_size))

        	else:
        		# we don't move window, but we mark these packets as acked
        		packets[start_counter]['acked'] = True

        # ack will be dropped otherwise

        # check for time-outs
		for _p in packets:
			if _p['acked'] == False and _p['sent'] == True:
				elapsed_time = time.time() - packets[start_counter]['timer']

				if elapsed_time >= timeout:
					_p['timed_out'] = False
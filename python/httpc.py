
# input HTTP request parameters
# output Packet[] array to be sent to SR_Sender

#HTTPC stuff                 # parse command-line arguments
# from HttpClientLib import * 
import sys                          # used to exit 
import os.path                      # used to create file

from urllib.parse import urlparse       # parse URL                               
import email                # used in parsing HTTP response headers
from io import StringIO     # used in conjunction with email
import pprint               # used in printing Python dictionary and list objects



commands = ['GET', 'POST', 'HEAD']
CRLF = "\r\n\r\n"
CR = "\r\n"
version = 'HTTP/1.0'

HOST = "localhost"
custom_user_agent = 'COMP-445-HTTP/1.0'
############


import argparse

def decode_args(args, extra_params):

	if args.command:
	    command = args.command
	    if command.upper() in commands:   # if command is POST|GET
	        if len(args.command_args) > 0:     # get URL from command_args ...
	            URL = args.command_args[0]
	        elif len(extra_params) > 0:                   # or from extra params
	            URL = extra_params[0]
	        else:
	            print("URL required")
	            sys.exit()
	    elif command.lower() == 'help':
	        if len(args.command_args) > 0:
	            helpcommand = args.command_args[0]
	        else:
	            helpcommand = ''
	    else:
	        print("unknown command: " + command)
	        sys.exit()


	    if command.upper() == 'POST':
	        if not args.data and not args.file:
	            print("error: one of the arguments -d/--data -f/--file is required") 
	            sys.exit()

	    if command.upper() == 'GET':
	        if args.data or args.file:
	            print("error: cannot use GET with -d or -f")
	            sys.exit()


	verbosity = args.verbose

	headers = []


	# process headers in -h k:v [-h k:v]
	for kv_pair in args.headers:
	    k,v = kv_pair.split(':')
	    if k != None and v != None:
	        headers.append(kv_pair)
	    #print(k)
	    #print(v)

	if args.data:
	    data = args.data   # TODO: perform checking here if needed
	else:
	    data = None

	if args.file:
	    file = args.file   # TODO: perform checking here if full path is entered, and other file scenarios

	    file_path = os.path.join(os.getcwd(),str(file))   # form path: current working dir + file path
	    # print(file_path)
	    if os.path.isfile(file_path):
	        pass
	    else:
	        print("file doesn't exist")
	        sys.exit()
	else:
	    file = None

	if args.output:
	    output_file = args.output           
	                                                    
	else:
	    output_file = None

	if command and URL:
	    command = command.upper()
	    if command in commands:
	    	return command, URL, headers, data, file

	    else:
	    	print("UNKNOWN COMMAND")
	    	return None

	    	# PROCESS(command, URL, headers, data, file, version, 80)
	    	# no URL

	    	# command, headers, data, file


	


def construct_http_request(command, url, headers, data, file):



	url = urlparse(url)
	query = url.query    # eg. id=1&name=Lenny
	path = url.path

	if path == "":
	    path = "/"
	if len(query) > 0:    # append query to path if exists
	    path = path + '?' + query



	# formulate request based on submitted paramaters
	json_data = False

	# if FILE option, get contents
	file_contents = ''
	if file:
	        # read contents of the file
	    with open(file, 'r') as file_read:
	        for line in file_read:
	            file_contents += line
	    # print(file_contents)

	# other headers to add
	headers.append('Host: ' + HOST)
	headers.append('User-Agent: ' + custom_user_agent)
	headers.append('Accept: ' + "*/*")


	# add Content-Length header if it's POST
	if command == 'POST' and (data or file):
	    if data:
	        headers.append('Content-Length:' + str(len(data)))
	    if file:
	        headers.append('Content-Length:' + str(len(file_contents)))

	params_headers_string = ''
	if len(headers) > 0:
	    params_headers_string += CR
	    for h in headers:
	        if 'json' in h:
	            json_data = True
	        if 'urlencoded' in h:
	            file_data = True
	        params_headers_string += (h + CR)


	# append data or file to the request
	if data:
	    if len(data) > 0:
	        params_headers_string += (CR + data)

	if file:
	    params_headers_string += (CR + file_contents)


	# send request, encoding it in utf-8


	return  "%s %s %s %s%s" % (command, path,  version, params_headers_string, CRLF)

	# s.send(bytes("%s %s %s %s%s" %
	#              (command, path,  version, params_headers_string, CRLF), "utf-8"))
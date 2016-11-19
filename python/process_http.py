"""
process_http.py

HTTP Server Library

"""

import urllib.parse 
import pprint
import email                # used in parsing HTTP response headers
from io import StringIO     # used in conjunction with email
import json 
from datetime import datetime 				# used to get current time-date
from babel.dates import format_datetime		# used to format time-date into HTTP header date
import sys, os

response_type = 'json'   # 'json' | 'html'

# ******* BONUS ************ #
# modify Content-type and Content-Disposition based on the type of requested file
# e.g. if file.mp3 then set Content-type to Audio, etc
# ***************************
image = ('.jpg', '.jpeg', '.png', '.gif', '.ico')
video = ('.mpg', '.mpeg', '.flv', '.avi', '.mp4', '.webm', '.mkv', '.3gp', '.ogv')
audio = ('.mp3','.wav','.flac', '.mp3', '.wmv', '.ogg')
application = ('.exe', '.zip', '.tar', '.xz')


"""
get_command_details

input: data, verbosity
output: request dictionary containing command, url_str, path, args, request_headers_dict, request_body

"""
def get_command_details(data, verbose):

	'''
	HTTP request from client looks like this

	GET /get?id=1&name&lenny HTTP/1.1
	Host: localhost:8081
	User-Agent: curl/7.49.0
	Accept: */*

	1. get first line as the command
	2. rest are headers
	'''

	try:
		# sepearte into [GET /get?id=1&name&lenny HTTP/1.1] and rest of headers 		
		request_line, headers_all = data.split('\r\n', 1)  			
		# create dictonary from headers e.g. {"Host":"localhost:8081"}
		headers_list = email.message_from_file(StringIO(headers_all))
		request_headers_dict = dict(headers_list.items())
		# print("###")
		# print(request_line)
		# print("###")
		request_line_split = request_line.split()       # [GET /get?id=1&name&lenny HTTP/1.1]
		command = request_line_split[0]					# GET
		url_str = request_line_split[1]						# /get?id=1&name&lenny
		version = request_line_split[2]					# HTTP/1.1	
		
		# print("command:" + command)
		# print("url:" + url)
		# print("version: " + version)

		# get body of request (usually data) seperated from headers by \r\n\r\n
		_, request_body = data.split('\r\n\r\n', 1)

	except:
		print("cannot recognize HTTP request from client")
		return None

	'''
	urlparse looks like this

	request: curl "http://localhost:8083/get?id=1&name=lenny"
	ParseResult(scheme='', netloc='', path='/get', params='', query='id=1&name=lenny', fragment='')
	'''
	url = urllib.parse.urlparse(url_str)
	# print("### >>Request URL properties:")
	# pprint.pprint(url)
	# print("###")

	if url.scheme == "":
		scheme = 'http://'
	if url.path == "":
		path = "/"
	if len(url.netloc) > 0:
	    host = url.netloc
	path = url.path
	args = url.query

	if verbose and len(args) > 0:
		print("Arguments: " + args)

	# collect request info into a dictionary, then return
	request = {}
	request['command'] = command
	request['url_str'] = url_str
	request['path'] = path
	request['args'] = args
	request['headers'] = request_headers_dict
	request['body'] = request_body

	return request


def prepare_json(response_body):
	### print(response_body['title'])
	### print(response_body['message'])
	json_str = response_body['title'] + '\r\n' + response_body['message'] + '\r\n' 
	if response_body['files']:
		json_str += str(response_body['files'])	
	if response_body['lines']:
		json_str += str(response_body['lines'])	

	return json_str


def prepare_html(response_body):

	message = response_body['message'].replace('\n', '<br/>')

	html = "<!DOCTYPE html><html><head><title>" + response_body['title'] + \
			"</title></head><body>"
	html += "<h2>" + response_body['title'] + "</h2>"
	html += "<p>" + message + "</p>"
	if response_body['files']:
		html += "<table border='1'>"
		for file in response_body['files']:
			html +=    "<tr>"
			html +=        "<td>" + file + "</td>"
			html +=    "</tr>"
		html +=  "</table>"
	elif response_body['lines']:
		html += "<p>"
		for line in response_body['lines']:
			html +=   line + "<br/>"
		html +=  "</p>"
	html += \
"""
</body>
"""
	return html


"""
prepare_http_response

input: request details, connection addr and port, response body and verbosity level
output: based on Accept header of request, prepares HTTP response to be JSON/HTML, etc

"""
def prepare_http_response(request, addr, port, file_response_body, verbose):

	if port != 80:
		addr = addr + ':' + str(port)

	command = request['command']
	url_str = request['url_str']
	path = request['path']
	args = request['args']
	request_headers_dict =  request['headers']

	# check if Accept header of request is HTML / JSON otherwise
	# browser: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
	# httpc /curl :  "*/*""

	if request_headers_dict['Accept']:
		if 'html' in request_headers_dict['Accept']:
			response_type = 'html'
		else:
			response_type = 'json'

	################ HTTP response body #########################

	# formulate HTTP response body in a dictionary
	HTTP_response_body = {}

	# add arguments/query
	if args:
		# parse 'id=1&name=lenny' ->  {'id': '1', 'name': 'lenny'}
		args_dict = dict(urllib.parse.parse_qsl(args))
		HTTP_response_body["args"] = args_dict

	# add all request headers that needs to be in the response body
	# first we just get some from the request itself, like Host, Accept, User Agent
	if len(request_headers_dict) > 0:
		HTTP_response_body["headers"] = request_headers_dict				# assuming it is in the right format

	# add origin and url
	HTTP_response_body["origin"] = addr					# e.g. 127.0.0.1
	HTTP_response_body["url"] = addr + url_str  		# e.g. 127.0.0.1/get?id=1&name&lenny

	# print("###")
	# pprint.pprint(HTTP_response_body)
	# print("###")

	message_body = ""




	requested_file = file_response_body['requested_file']

	############# modify body if regular HTTP request or file server request #####
	# prepare response body (JSON, HTML, plain text) along the way

	# if non-text file, add Content-type header as the file-type
	if requested_file and file_response_body['file_type'] == 'non-text':

		# get plain file extension to attach to content-type
		file_ext = os.path.splitext(requested_file)[1].replace('.','')

		if requested_file.lower().endswith(image):
			content_type = 'image/' + file_ext
			# content_disposition = 'attachment; filename="' + os.path.basename(requested_file) + '"'
		elif requested_file.lower().endswith(audio):
			content_type = 'audio/' + file_ext
		elif requested_file.lower().endswith(video):
			content_type = 'video/' + file_ext
		elif requested_file.lower().endswith(application):
			content_type = 'application/' + file_ext
		else:			# if remains unknown, the recipient should treat it as type app/octet-stream
			content_type = 'application/octet-stream'

		content_length = os.path.getsize(requested_file)
		message_body = prepare_json(file_response_body)   # we should only try to display files on the terminal (not on browsers)

	# requested file is regular text file
	else:

		if file_response_body != None and response_type == 'html':
			message_body = prepare_html(file_response_body)
			content_type = "text/html; charset=utf-8"
		elif file_response_body != None and response_type == 'json':
			HTTP_response_body["data"] = prepare_json(file_response_body)
			message_body = json.dumps(HTTP_response_body, indent=4, sort_keys=True)
			content_type = "application/json"
		else:  # no response body, this could be a simple server.py call
			# convert dictionary to standard JSON string, with proper whitespace and sorted
			message_body = json.dumps(HTTP_response_body, indent=4, sort_keys=True)
			content_type = "application/json"
	
	# get length of response body for Content-Length
	content_length = len(message_body) 

	####### ERROR HANDLING ############
	try: 
		error = file_response_body['error']
	except:
		error = -1

	if error == 404:
		status = "HTTP/1.0 404 NOT FOUND"
	elif error == 403:
		status = "HTTP/1.0 403 FORBIDDEN"
	elif error == 400:
		status = "HTTP/1.0 400 BAD REQUEST"
	else:								# all good, no error
		status = 'HTTP/1.0 200 OK'

	if verbose:
		print("Status: " + status)

	####################### HTTP Response Headers ##################
	# get date
	now = datetime.utcnow()
	format = 'EEE, dd LLL yyyy hh:mm:ss'			# Format: Date: Sat, 22 Oct 2016 18:59:02 GMT
	datetime_str =  format_datetime(now, format, locale='en') + ' GMT'	

	HTTP_headers = []
	HTTP_headers.append(status)
	HTTP_headers.append('Server: COMP-445-Server')
	HTTP_headers.append('Date: ' + datetime_str)								
	HTTP_headers.append('Content-Type: ' + content_type)
	HTTP_headers.append('Content-Length: ' + str(content_length))
	HTTP_headers.append('Connection: close')					# non-persistent connection for HTTP 1.0
	# Access-Control-Allow-Origin: *							# we don't allow CORS for simple requests, see README
	# Access-Control-Allow-Credentials: true

	HTTP_headers_str = ''
	for h in HTTP_headers:
		HTTP_headers_str += '\r\n' + h

	response_str = HTTP_headers_str  + "\r\n\r\n" + message_body  + "\r\n"

	# print("###")
	# print(response_str)
	# print("###")
	return response_str


"""
process

used by simple HTTP Server apps (server.py)
"""

def process(data, addr, port):
	# decode data

	request = get_command_details(data)
	response = prepare_http_response(request, addr, port, None)
	return response

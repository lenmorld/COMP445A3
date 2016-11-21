"""
process http_file

HTTP File Server Library that uses the HTTP Server library (process_http)

used for processing requests involve in a file server
used by httpfs

relies on process_http on building responses

processReq takes the request from httpfs
 performs file manipulation and security checks
 produces info directory contents list/ file contents / error messages
 then calls process_http to package this info into an http response
"""

import process_http
import os
import sys
import threading

root_dir = os.getcwd()
# dir_path  = os.path.dirname(os.path.realpath(__file__))   # same thing as os.getcwd()
security = True
working_dir = 'data'   # even though default dir (./) is chosen at server run, 
					   # 'data' will be the 'file server working directory'

### security ####
forbidden_dirs = ['secret', 'old', '__pycache__', '.git']			# add here all forbidden dirs other than root
# formulate path for each forbidden dir
forbidden_dir_paths = [os.path.join(os.sep, root_dir, f) for f in forbidden_dirs]
# add root to forbidden dir
forbidden_dir_paths.append(root_dir)

# see dirs that are not forbidden
not_forbidden_paths = [f for f in os.listdir(os.getcwd()) if ( os.path.isdir(f) and (f not in forbidden_dirs) )]


"""
decode_non_text

decodes non-text files such as image, audio, binary, etc

"""
def decode_non_text(fileName, lock):
	with lock:
		with open(fileName, mode='rb') as file:    # read part as binary
		    fileContent = file.read()

	# print(fileContent)
	return fileContent


"""
process_Req

input:
- data: full unparsed HTTP request
- addr: client IP address
- port: port that the server is running
- directory: working dir of file server, root (./) if not selected
- isVerb: verbosity on/off

output:
- http_response in proper format
"""
def process_Req(data, addr, port, directory, isVerb):
	
	verbose = isVerb
	directory = os.path.join(os.sep, root_dir , directory)
	global lock 
	lock = threading.Lock()
	access_allowed = True
	found = True
	dir_found = True
	request = process_http.get_command_details(data, verbose)

	if request == None:
		print("### ...listening at port " + str(port) +"....")
		return None

	reqType = request['command']
	path = request['path']			# /foo , /foo/foo
	request_body = request['body']

	if verbose:
		print("Operation: " + reqType)
		print("URL requested: " + path)
	# print("### working dir: " + directory)
	if path in ['/', '\\']:
		full_file_path = os.path.join(os.sep, directory, '')		# -> /data/
	else:
		if path[0] == '/':
			path = path[1:]		# remove / that causes bug in joining paths
		full_file_path = os.path.join(os.sep, directory, path)
	# print("### full file path: " + full_file_path)

	# get filename from given path, #e.g. /abc.txt   -> abc.txt, /data/ -> data
	fileName = os.path.basename(full_file_path)			# get file
	# get directory from given path, #e.g. /foo/bar/fi -> bar, /foo/bar/ -> bar 
	directory = os.path.dirname(full_file_path)		    # get dir

	# print("### path is " + path)
	# print("### request is " + reqType)
	# print("### server directory : " + directory)
	# print("### fileName is " + fileName)

	# initialize response body components
	response_body = {}
	response_body['lines'] = None
	response_body['files'] = None
	response_body['title'] = ""
	response_body['message'] = ""
	response_body['error'] = -1
	response_body['requested_file'] = None
	response_body['file_type'] = 'text'

	######### SECURITY HARDENING ################
	# this applies mainly if default directory is chosen when running the server
	# and when a file/dir is accessed in the root dir
	# 'data' will always be the working directory if not selected
	#    e.g.  localhost:8081/httpfs.py   should be forbidden
	#          localhost:8081/			  should be forbidden
	#          localhost:8081/data/abc.txt should be allowed
	#############################################

	### print(full_file_path)


	# if GET and request URL is not found
	if (not os.path.isfile(full_file_path) and not os.path.isdir(full_file_path) and (reqType == "GET"))  :
		response_body['title'] = "404 Not Found"
		response_body['message'] = "Server did not find the requested URL"
		response_body['error'] = 404	
		found = False

	# if POST and directory to post does not exist
	if reqType == 'POST' and not os.path.isdir(directory) :
		response_body['title'] = "404 Not Found"
		response_body['message'] = "Server did not find the requested directory for the POST request"
		response_body['error'] = 404	
		dir_found = False


	# if security ON, restrict read access to dirs in [not_forbidden_paths]
	if security:
		# print("### Directory requested: " + directory)
		if verbose:
			if os.path.basename(directory) ==  os.path.basename(os.getcwd()): # if root requested, print / not the dir name
				print("Directory requested: " + "/") 
			else:
				print("Directory requested: " + os.path.basename(directory))

		# if directory in forbidden_dir_paths:	     # if requested dir is in forbidden paths
		### FORBIDDEN_PATHS
		# modified: allow dir listing but not file access (for forbidden_fir_paths)
		# if given file is in a requested dir that belongs to forbidden paths
		# or trying to POST in a forbidden_path
		if (directory in forbidden_dir_paths) and (os.path.isfile(full_file_path)  or (reqType == 'POST')    ):	     
			response_body['title'] = "403 Forbidden"
			response_body['message'] = "The server cannot fulfill the request for security reasons." + \
									   "\nTry other directories "
			response_body['files'] = not_forbidden_paths
			response_body['error'] = 403
			access_allowed = False

	if(reqType == "GET") and access_allowed and found :
		if len(fileName) == 0:		# GET /
			fileNames = []
			# print("### in get and filename dir" + directory)
			files = [f for f in os.listdir(directory)] 
			for f in files:
			    fileNames.append(f)
			# print("###")
			# print(fileNames)
			# print("###")
			response_body['title'] = "Files found"
			response_body['message'] = "Files inside directory:"
			response_body['files'] = fileNames
		elif  len(fileName) > 1:	# GET /foo
			actualFileName = fileName
			actualFileName = directory + "/" + actualFileName
			if verbose:
				print("Filename requested: " + os.path.basename(actualFileName) )
			if(os.path.isfile(actualFileName)):			# check if file exist
				response_body['message'] = "Contents of " + os.path.basename(actualFileName) 
				try:
					# only do this if file can be read line by line (text file)
					# dont do this for image/audio/exe
					lines = []
					with lock:
						with open(actualFileName, "r") as ins:                       
						    for line in ins:
						        lines.append(line)
					response_body['lines'] = lines
					response_body['message'] = "Contents of " + os.path.basename(actualFileName) 

				except UnicodeDecodeError:
					response_body['message'] = 'Media/application file'
					response_body['lines'] = decode_non_text(actualFileName, lock)
					response_body['file_type'] = 'non-text'					

				response_body['title'] = "Requested file found"
				response_body['requested_file'] = actualFileName      # *** BONUS *** include filename for further processing                                     
			else:									    # file doesn't exist
				if verbose:	
					print("File does not exist ")
				response_body['title'] = "404 Not Found"
				response_body['message'] = "Server did not find the requested file/URL"
				response_body['error'] = 404

	elif access_allowed and reqType == 'POST' and dir_found:		# POST /bar
		if  len(fileName) > 1:
			# first check if filename is on directory
			actualFileName = directory + "/" + fileName
			if verbose:
				print("Filename to write: " + os.path.basename(actualFileName))
			if not(os.path.isfile(actualFileName)):
				if verbose:
					print("File doesn't exist in server... Creating file")
				response_body['title'] = "Creating file"
				response_body['message'] = "File doesn't exist in server... Creating file"
			else:
				if verbose:
					print("File exists in server... Overwriting file")
				response_body['title'] = "Overwriting file"
				response_body['message'] = "File exists in server... Overwriting file"

			# eitherway, mode 'w' in python would create/overwrite
			# print(actualFileName)

			try:	# if text
				with open(actualFileName, "w") as out:
					# print(request_body)
					out.write(request_body)
			except: # if non-text
				with open(actualFileName, "wb") as out:
					out.write(request_body)				

			# if there, overwrite with data
			# if not, create new file
			# either way write data  which would be at the body of the request
			# print(request_body)

	elif(reqType != "GET" and reqType != "POST"):
		if verbose:
			print("Error: must be either GET or POST request")
		response_body['title'] = "400 Bad Request"
		response_body['message'] = "The request could not be understood by the server"
		response_body['error'] = 400

	# prepare http response
	http_response = process_http.prepare_http_response(request, addr, port, response_body, verbose)

	return http_response

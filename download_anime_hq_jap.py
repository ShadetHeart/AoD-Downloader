import requests
import os
import re

def download(url,title,episode):

	#check if already downloaded
	if(os.path.exists(title+".mkv")):
		return

	#variables
	num = 0 #counter variable
	num_max = 0 #number of chunks to download

	#create chunklist url
	urlpoint1 = url.find("media")
	urlpoint2 = url.find("=_")
	key = url[(urlpoint1+6):urlpoint2]
	chunklist = url[:urlpoint1]+"chunklist_"+key+"=.m3u8"

	#download and write chunklist
	with open("chunklist.m3u8", "wb") as file:
		response = requests.get(chunklist)
		file.write(response.content)
		
	#read number of chunks from chunklist
	with open("chunklist.m3u8", "r") as file:
		lines = file.read().splitlines()
		last_chunk = lines[-2]
		tmp = last_chunk.find("=_")
		num_max = int(last_chunk[(tmp+2):-3])

	#download video code	
	while(True):
		#calculate percent
		percent = (num+1)/(num_max+1)*100
		percent = format(percent, ".2f")
		
		#generate filename
		filename = str(num)+".ts"
		
		#create url
		replace = url.find("=_")
		url = url[:replace]+"=_"+filename
		
		#download and write file:
		with open(filename, "wb") as file:
			response = requests.get(url)
			file.write(response.content)
		
		#check if file is empty and abort
		fileinfo = os.stat(filename)
		if(fileinfo.st_size == 0):
			os.remove(filename)
			break
			
		os.system('cls')
		print("Downloading Episode " + str(counter) + ":")
		print("Downloaded chunk " + str(num+1) + " of " +  str(num_max+1) + " (" + percent + "%)")
			
		#increase counter
		num = num + 1

	print("Merging chunks")

	#create chunklist
	with open("chunklist.txt", "w") as file:
		for i in range(num_max+1):
			filename = str(i)+".ts"
			file.write("file " + filename + "\n")

	#merge to video
	print("ffmpeg -loglevel panic -f concat -i chunklist.txt -c copy " + title + ".mkv")
	os.system("ffmpeg -loglevel panic -f concat -i chunklist.txt -c copy " + title + ".mkv")

	print("Cleanup")
	#cleanup
	for i in range(num_max+1):
		filename = str(i)+".ts"
		os.remove(filename)
	os.remove("chunklist.m3u8")
	os.remove("chunklist.txt")
		
	print("Done")

os.system('cls')
	
#asking for login info
username = input("Enter username: ")
password = input("Enter password: ")
username = username.encode('utf-8')
password = password.encode('utf-8')

#get anime url
print()
anime = input("Enter anime url: ")

#create session cookies
url = "https://www.anime-on-demand.de/users/sign_in"

session = requests.Session()

response = session.get(url)
response = response.text

#create login auth token
token_start = response.find('name="authenticity_token" value="')+33
token = response[token_start:]
token_end = token.find('"')
token = token[:token_end]

#login
login = {"utf8":"&#x2713;","user[login]":username,"user[password]":password,"user[remember_me]":"0","authenticity_token":token}
response = session.post(url,data=login)

response = session.get(anime)
response = response.text

#get csrf token
csrf_token_start = response.find("csrf-token=")+21
csrf_token = response[csrf_token_start:]
csrf_token_end = csrf_token.find('"')
csrf_token = csrf_token[:csrf_token_end]

#get playlist url
playlist_start = response.find("mit Untertiteln starten")+40
playlist_url = response[playlist_start:]
playlist_end = playlist_url.find('"')
playlist_url = "https://www.anime-on-demand.de" + playlist_url[:playlist_end]

#download playlist info
session.headers.update({"X-CSRF-Token":csrf_token,"Accept-Encoding":"gzip, deflate, br","Accept-Language":"de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7","User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36","Accept":"application/json, text/javascript, */*; q=0.01","Referer":anime,"X-Requested-With":"XMLHttpRequest","Connection":"keep-alive"})
response = session.get(playlist_url)
episode_list = response.text

#download info for every episode
counter = 1
while(episode_list.find("title") != -1):

	#get episode chunklist sources url
	episode_list = episode_list[(episode_list.find("file")+7):]
	episode_url = episode_list[:episode_list.find('"')]
	episode_url = episode_url.replace("\\u0026","&")

	#get episode title
	episode_list = episode_list[(episode_list.find("title")+8):]
	episode_title = episode_list[:episode_list.find('"')]
	episode_title = episode_title.replace(" ", "_")
	
	#get highest quality episode chunklist
	episode_chunklist_url = session.get(episode_url)
	episode_chunklist_url = episode_chunklist_url.text
	episode_chunklist_url = episode_chunklist_url[(episode_chunklist_url.find("chunklist")):(episode_chunklist_url.find("=.m3u8")+6)]
	episode_chunklist_url = episode_url[:(episode_url.find('.smil')+5)]+"/"+episode_chunklist_url
	
	#get first chunk of chunklist and pass to download function
	episode_chunklist = session.get(episode_chunklist_url)
	episode_chunklist = episode_chunklist.text
	episode_chunk0_url = re.search('media.*.ts', episode_chunklist)
	episode_chunk0_url = episode_url[:(episode_url.find('.smil')+5)]+"/"+episode_chunk0_url.group()
	
	download(episode_chunk0_url,episode_title,counter)
	counter = counter+1


#!/usr/bin/python3

import requests
import os
import re
import shutil

if os.name == "nt":
	os.system('cls')
else:
	os.system('clear')
	
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
episode_counter = 1
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
	episode_chunklist_url = episode_chunklist_url[(episode_chunklist_url.find("CODECS=")+31):(episode_chunklist_url.find("Id=")+23)]
	episode_chunklist_url = episode_url[:(episode_url.find('index.m3u8'))]+"/" + episode_chunklist_url
	
	#get chunklist
	episode_chunklist = session.get(episode_chunklist_url)
	episode_chunklist = episode_chunklist.text
	
	#clean chunklist
	chunks = re.findall("..\/..\/..\/.*", episode_chunklist)

	episode_chunklist = ""
	for line in chunks:
		episode_chunklist = episode_chunklist + (episode_url[:(episode_url.find('index.m3u8'))] + line[8:]) + "\n"

	#check if episode is already downloaded
	if(os.path.exists(episode_title + ".mkv")):
		continue
	
	#download episode
	downloaded_chunks = 0
	download_percentage = 0
	    
	#create tmp directory for chunks
	if(not os.path.exists("tmp")):
		os.mkdir("tmp")
		
	for url in episode_chunklist.splitlines():
		#download chunk
		with open("tmp/" + str(downloaded_chunks) + ".ts", "wb") as file:
			response = requests.get(url)
			file.write(response.content)
			
		downloaded_chunks = downloaded_chunks + 1
		download_percentage = (downloaded_chunks)/(len(chunks))*100
		download_percentage = format(download_percentage, ".2f")
		
		if os.name == "nt":
			os.system('cls')
		else:
			os.system('clear')
			
		print("downloading episode " + str(episode_counter))
		print(download_percentage)
		
	#create chunklist for ffmpeg
	with open("tmp/chunklist", "w") as file:
		for i in range(0,int(len(chunks))):
			file.write("file '" + str(i) + ".ts'" + "\n")
			
	#merge to video
	print("creating video")
	os.system('ffmpeg -f "concat" -i "tmp/chunklist" -c copy "' + episode_title + '.mkv"')
	
	#cleanup
	shutil.rmtree("tmp")

	episode_counter = episode_counter + 1
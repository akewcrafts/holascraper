from filecmp import clear_cache
import json
import sys
import os
import codecs
from weakref import proxy
import requests
import ssl
import time
import sys
import json
import urllib.request
import mysql.connector
import requests

ssl._create_default_https_context = ssl._create_unverified_context

from requests import get
from time import sleep
from src import config
from pathlib import Path
from random import randint
from instagram_private_api import Client as AppClient
from instagram_private_api import ClientCookieExpiredError, ClientLoginRequiredError, ClientError, ClientThrottledError, ClientConnectionError

class Holascraper:
    api = None
    user_id = None
    target_id = None
    is_private = True
    following = False
    target = ""
    initiator = "holascraper.com"
    writeFile = True
    output_dir = "output"
    current_user = ""
    web_user = ""
    host = "https://instagram.com/"
    profile_url = "/?__a=1"

    # Testing Module

    def __init__(self, target, user, is_cli, clear_cookies):
        
        self.checkConnection()
            
        accounts = config.random_account()
        selectAccount = randint(0,len(accounts))
        u = accounts[selectAccount]['username_ig']
        p = accounts[selectAccount]['password_ig']
        self.web_user = user
        self.clear_cookies(clear_cookies)
        self.cli_mode = is_cli
        self.login(u, p)
        self.current_user = u                                
        self.setTarget(target)
      

    def clear_cookies(self,clear_cookies):
        if clear_cookies:
            self.clear_cache()
    
    def get_data_following(self):
        return True

    def getAccess(self,code):
        
        ip = get('https://api.ipify.org').text
        getAccess = requests.post("https://holascraper.com/old/getToken", data={'code': code, 'ip': ip})
    
        if getAccess:
            return True
        else:
            return False
    
    def sendBasic(self,id,username,fullname,source,next_max_id):
        
        res = config.insertFollowers(id,username,fullname,self.target,source,next_max_id,self.web_user)
            
        return res
    
    def checkTarget(self,start=0,next=5):
        
        res = config.check_target(self.target,start,next)

        return res

    def updateStatus(self):
        requests.post("https://holascraper.com/old/status_completed", data= {'target':str(self.target),'initiator':str(self.initiator)})
        return True

    def countTarget(self):
        res = config.target_counter(self.target)
        return res
        
    def updateData(self,id):
        config.update_data(id,self.target)

    def updateData2(self,id,target):
        config.update_data(id,target)
    
    def getAll(self):
        res = config.get_all_uncollected()
        return res

    def collectData(self):
          
        counted_target = int(self.countTarget())

        x = 0
        
        wave = (counted_target/250)+1
        
        start = 0
        next = 250
        
        followers = []
        followers = self.extract_target(start,next)
        
        while x < wave:
            
            followers = self.extract_target(start,next)
            start = start+next
            next = next+250
            x = x+1
        
            if x%3 == 0:
                sleep(3)

            print("\n\nplease wait.. \n")
            print("Collecting data.. \n \n")
            
            request_times = 0
            data_collected = 0
            
            for resultz in followers:
                time.sleep(1)   
                endpoint = 'users/{user_id!s}/full_detail_info'.format(**{'user_id': resultz['id']})
                request_times += 1
              
                if request_times % 5 == 0:
                    sys.stdout.write(" \n Too many request, please wait 10 Seconds\n")
                    sys.stdout.flush()
                    sleep(10)

                try:

                    content = self.api._call_api(endpoint)
                
                    result = content['user_detail']['user']
                    sys.stdout.write("\r collecting data from ")
                    print(str(result['username']))

                    self.updateData(result['pk'])

                    if 'contact_phone_number' in result and result['contact_phone_number']:

                        if self.sendDeep(result['username'],result['full_name'],result['category'],str(result['contact_phone_number']),result['public_email'],resultz['source'],self.target) == "oke":
                            
                            data_collected += 1
                            sys.stdout.write(" \n\r%i data being collected\n" % data_collected)
                            sys.stdout.flush()
                            
                    else:
                        
                        print(" Skipped! ")
                        print(" phone number not found!\n")      

                except urllib.error.HTTPError as e:

                    pass

                except ClientConnectionError as e:
                
                    print("Wopps! The connection has been lost.\n")
                    print("Checking the connection..\n")
                    print("Reconnecting...\n")

                    if self.reconnect():

                        print("|__#CONNECTED!\n")
                        print("Continue!\n")

                        pass

                    else : 

                        self.reconnect()

                    pass                   
                
                except ClientThrottledError as e:

                    print("HUGE REQUEST WAS DETECTED BY INSTAGRAM!\n")
                    print("Don't be panic, our script still running.. \n\n")

                    print("\n*** Switching...\n")

                    f = open("src/settings.json",'w')
                    f.write("{}")
                    self.switching()
                    pass
                
                except ClientError as e:
                    
                    try:

                        if e == 'Not Found':
                            pass
                        else:
                            print(e)
                            pass

                        if 'challenge' in json.loads(e.error_response):
                            
                            # error = json.loads(e.error_response)
                            
                            # print("Please follow this link to complete the challenge: " + error['challenge']['url'])
                            print("\n*** Switching...\n")

                            # answer = input("Have been solved ? y/n : ")

                            # if answer == 'y':
                            f = open("src/settings.json",'w')
                            f.write("{}")
                            self.switching()                             
                            pass
                    
                    except:

                        pass
            
        print(" \n\n|")
        print(" |__# MISSION ACOMPLISHED! Please check result at https://holascraper.com\n")
    
    def challengeAnswer(self):
         
        answer = input("\n to continue the process please solve the challenge first? yes/no : ") 
         
        if answer == "yes":
            return True 
        elif answer == "no": 
            return False 
        else: 
            return False

    def sendDeep(self,username,fullname,category,phone,email,source,target):
        
        res = config.insert_data(username,fullname,phone,email,category,source,target) 
        return res

    
    # def auth(self):
        
    #     sleep(0.5)
    #     print("\n[::akewcrafts.com] ==> Connecting to the server \n")
    #     sleep(0.5)
    #     print("[::akewcrafts.com] ==> ")
    #     print("Authenticating ... \n\n")
    #     sleep(1)
    #     print("[::akewcrafts.com] ==> ")
    #     print("Authenticated! \n\n")

    #     return True
    

        
    def checkConnection(self):
    
        timeout = 5

        print("\nChecking for connection... ")

        try:
            request = requests.get(self.host, timeout=timeout)
            print("OK! \n")
        except (requests.ConnectionError, requests.Timeout) as exception:
            print("DISCONNECTED! \n")
            sys.exit(1)
            
    def user_agent(self):
        
        with open('src/user-agent.txt') as ua:
            lines = ua.readlines()
        
        return lines[randint(0,len(lines))]
  
        
    def reconnect(self):
        
        timeout = 3
        
        try:
            requests.get(self.host, timeout=timeout)
            return True
        except (requests.ConnectionError, requests.Timeout) as exception:
            return False
    
    def bypass(self,cu):
    
        self.checkConnection()
        
        c = config.getBypass(cu)
        u = c['username']
        p = c['password']
        
        if self.login(u, p):
            return True
        
        return False
        
    def total_following(self):
        endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
        content = self.api._call_api(endpoint)
        data = content['user_detail']['user']
        return int(data['following_count'])
    
    def total_follower(self):
        endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
        content = self.api._call_api(endpoint)
        data = content['user_detail']['user']
        return int(data['follower_count'])
                
    def setTarget(self, target):
        self.target = target
        user = self.get_user(target)
        self.target_id = user['id']
        self.is_private = user['is_private']
    
    def setDelay(self):
        delay = randint(5,int(self.req_delay))
        return int(delay)

    def get_user(self, username):
        
        try:
            content = self.api.username_info(username)
            
            user = dict()
            user['id'] = content['user']['pk']
            user['is_private'] = content['user']['is_private']

            return user
        
        except ClientError as e:
            print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
            error = json.loads(e.error_response)
            if 'message' in error:
                print(error['message'])
            if 'error_title' in error:
                print(error['error_title'])
            if 'challenge' in error:
                print("Please follow this link to complete the challenge: " + error['challenge']['url'])    
            sys.exit(2)
    
    def login(self, u, p):
        
        # ubah save & load dari DB
        try:
            
            settings_file = "src/settings.json"
            if not os.path.isfile(settings_file):
                # settings file does not exist
                print(f'Unable to find file: {settings_file!s}')

                # login new
                self.api = AppClient(auto_patch=True, authenticate=True, username=u, password=p,
                                     on_login=lambda x: self.onlogin_callback(x, settings_file))

            else:
                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook=self.from_json)
                # print('Reusing settings: {0!s}'.format(settings_file))

                # reuse auth settings
                self.api = AppClient(
                    username=u, password=p,
                    settings=cached_settings,
                    on_login=lambda x: self.onlogin_callback(x, settings_file))
                
                self.current_user = u
                
        except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
            print(f'ClientCookieExpiredError/ClientLoginRequiredError: {e!s}')

            # Login expired
            # Do relogin but use default ua, keys and such
            self.api = AppClient(auto_patch=True, authenticate=True, username=u, password=p,
                                 on_login=lambda x: self.onlogin_callback(x, settings_file))
            pass

        except ClientError as e:
            
            print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
            error = json.loads(e.error_response)
            print(error['message'])
            print(": ")
            print(e.msg)
            print("\n")
            
            self.clear_cache
            
            if 'challenge' in error:
                print("Please follow this link to complete the challenge: " + error['challenge']['url'])

            self.switching()

    def to_json(self, python_object):
        if isinstance(python_object, bytes):
            return {'__class__': 'bytes',
                    '__value__': codecs.encode(python_object, 'base64').decode()}

        raise TypeError(repr(python_object) + ' is not JSON serializable')

    def from_json(self, json_object):
        if '__class__' in json_object and json_object['__class__'] == 'bytes':
            return codecs.decode(json_object['__value__'].encode(), 'base64')
        return json_object

    def onlogin_callback(self, api, new_settings_file):
        cache_settings = api.settings
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default=self.to_json)
            # print('SAVED: {0!s}'.format(new_settings_file))

    def check_following(self):
        if str(self.target_id) == self.api.authenticated_user_id:
            return True
        endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
        return self.api._call_api(endpoint)['user_detail']['user']['friendship_status']['following']

    def check_private_profile(self):
        
        if self.is_private and not self.following:
            print("We can't collect data from private account, but \n")
            self.api.friendships_create(self.target_id)
            return True
        
        return False
    
    def is_complete(self):
        res = config.is_complete(self.target)
        return res

    def extract_target(self,start,next):
        
        followers = self.checkTarget(start,next)
        
        if self.checkTarget(start, next) == "nope":
            print("Target doesn't exists in our database \n")
            print("try this arguments : python3 hs.py <target_username> -c catchfwers \n\n")
            exit()
            
        sys.stdout.write("\r%i followers loaded" % len(followers))
        sys.stdout.flush()
            
        return followers

    def updateWave(self,wave):

        config.update_wave(self.target,wave)
    
    def getWave(self):
        res = config.get_wave(self.target)
        return res

    

    def catch_followers(self):
        
        if self.check_private_profile():
            return

        if self.is_complete():
            print('\nAll public account of followers target already collected!\n')
            exit(0)
        
        rank_token = AppClient.generate_uuid()
        data = self.api.user_followers(str(self.target_id), rank_token=rank_token)
        request_times = 1
        counter = 0

        next_max_id = self.getWave() # Ambil wave terakhir 
        
        # JIka nilai wave 0 , aplikasi akan collect followers si target dari awal
        try:

            if next_max_id == 0 or next_max_id == '0' or next_max_id == '':
                
                
                    for user in data["users"]:
                    
                            #private account akan diabaikan
    
                            if user['is_private'] == False: 
                                
                                if self.sendBasic(user['pk'],user['username'],user['full_name'],'followers') == 'oke':
                                    counter+=1    
                                    sys.stdout.write("\rCatched %i followers" % counter)
                                    sys.stdout.flush()
                   
            else:
            
                counter = self.countTarget()
                print("Continue from last activity...\n\n")

                # jika nilai wave bukan 0 maka counter akan dimulai dari total angka target yang berhasil di collect terakhir kali
            
            while next_max_id:
            
                self.updateWave(next_max_id) 
                
                if request_times%10 == 0:
                    
                    time.sleep(30) # setiap 5x hit API , aplikasi akan delay selama 10 menit untuk menghindari challenge

                results = self.api.user_followers(str(self.target_id), rank_token=rank_token, max_id=next_max_id)
                
                request_times += 1
                    
                for user in results["users"]:
                    
                    if user['is_private'] == False:

                        sleep(0.1)
                        
                        if self.sendBasic(user['pk'],user['username'],user['full_name'],'followers') == 'oke':
                            counter+=1    
                            sys.stdout.write("\rCatched %i followers" % counter)
                            sys.stdout.flush()
                    
                        if counter%100 == 0:
                            sleep(25)

                self.updateWave(next_max_id) 
                next_max_id = results.get('next_max_id')
                print(next_max_id)

            self.updateStatus()
            print('\nAll public account of followers target has been collected!')
        
        except urllib.error.HTTPError as e:
            pass

        except ClientConnectionError as e:
        
            print("Wopps! The connection has been lost.\n")
            print("Checking the connection..\n")
            print("Reconnecting...\n")
            if self.reconnect():
                print("|__#CONNECTED!\n")
                print("Continue!\n")
                pass
            else : 
                self.reconnect()
            pass                   
        
        except ClientThrottledError as e:
            
            print("HUGE REQUEST WAS DETECTED BY INSTAGRAM!\n")
            print("Please wait for 2 hours\n")
            print("Don't be panic, our script still running.. \n\n")
            time.sleep(14400)

            pass
        
        except ClientError as e:
            
            try:
                if e == 'Not Found':
                    pass
                
               
                if 'challenge' in json.loads(e.error_response):
                    
                    error = json.loads(e.error_response)
                    
                    print("Please follow this link to complete the challenge: " + error['challenge']['url'])
                    print("\n*** then enter \"yes\" if the challenge has been solved.\n")
                    if self.challengeAnswer == True:
                        
                        f = open("src/settings.json",'w')
                        f.write("{}")
                        c = config.account_init()
                        u = c['username']
                        p = c['password']
                        self.login(u, p)                                
                        pass
                    
                    else:
                        self.challengeAnswer
            except:
                pass
            
    def catch_followings(self):
        
        if self.check_private_profile():
            return
        
        if self.check_completed == 1:
            print('\nAll public account of following target has been collected!\n')
            print("next: try to get email and phone number.")
        
        rank_token = AppClient.generate_uuid()
        data = self.api.user_followings(str(self.target_id), rank_token=rank_token)
        request_times = 1
        counter = 0
        
        try: 

            next_max_id = data['next_max_id']
           

        except:

            print("Please choose the target who has more than 100 following!\n")
            exit(0)

        next_max_id = self.getWave() # Ambil wave terakhir 
        self.updateWave(next_max_id) 
        # JIka nilai wave 0 , aplikasi akan collect followers si target dari awal

        if next_max_id == 0 or next_max_id == '0' or next_max_id == '':

            for user in data["users"]:
                
                #private account akan diabaikan
                
                if user['is_private'] == False: 

                    sleep(0.25)

                    if self.sendBasic(user['pk'],user['username'],user['full_name'],str(self.target),str(self.initiator)) == 'oke':
                        counter+=1    

                        sys.stdout.write("\rWave %i successfully catched!" % counter)
                        sys.stdout.flush()
        else:

            counter = self.countTarget()
            print("Continue from last activity...\n\n")

            # jika nilai wave bukan 0 maka counter akan dimulai dari total angka target yang berhasil di collect terakhir kali

        while next_max_id:
        
            # if request_times%3 == 0:
                
            #     time.sleep(300) # setiap 5x hit API , aplikasi akan delay selama 10 menit untuk menghindari challenge

            results = self.api.user_following(str(self.target_id), rank_token=rank_token, max_id=next_max_id)
            
            request_times += 1
                
            for user in results["users"]:
                
                if user['is_private'] == False:
                    
                    sleep(0.3)
                    
                    if self.sendBasic(user['pk'],user['username'],user['full_name'],str(self.target),'following') == 'oke':
                        counter+=1    
                    
                        sys.stdout.write("\rwave %i successfully catched!" % counter)
                        sys.stdout.flush()
                
            self.updateWave(next_max_id) 
            next_max_id = results.get('next_max_id')
        
        self.updateStatus()
        print('\nAll public account of followers target has been collected!')
        
                        
    def get_data_followers(self):
                
            if self.check_private_profile():
                return
            
            self.catch_followers()
            
            print("\n\nplease wait.. \n")
            
            sleep(72)
            
            self.collectData()

    def clear_cache(self):
        
        try:
            f = open("src/settings.json",'w')
            f.write("{}")
            print("Cache Cleared.\n")
            
        except FileNotFoundError:
            print("Settings.json don't exist.\n")
            
        finally:
            f.close()

    def collectAll(self):

        followers = self.getAll()
        request_times = 0
        data_collected = 0

        for resultz in followers:
                
                endpoint = 'users/{user_id!s}/full_detail_info'.format(**{'user_id': str(resultz['instagram_id'])})
                print(resultz['instagram_username'])
                request_times += 1
              
                if request_times % 25 == 0:
                    sys.stdout.write(" \n Too many request, please wait 3 minutes\n")
                    sys.stdout.flush()
                    sleep(30)

                try:
                    self.updateData2(resultz['instagram_id'],resultz['from_target'])
                    sleep(0.5)
                    content = self.api._call_api(endpoint,version='v2')
                    result = content['user_detail']['user']

                    sys.stdout.write("\r collecting data from ")
                    print(str(result['username']))

                    if 'contact_phone_number' in result and result['contact_phone_number']:

                        if self.sendDeep(result['username'],result['full_name'],result['category'],str(result['contact_phone_number']),result['public_email'],resultz['source'],resultz['from_target']) == "oke":
                            
                            data_collected += 1
                            sys.stdout.write(" \n\r%i data being collected\n" % data_collected)
                            sys.stdout.flush()
                            
                    else:
                        
                        print(" Skipped! ")
                        print(" phone number not found!\n")      

                except urllib.error.HTTPError as e:
                    print(e)
                    pass

                except ClientConnectionError as e:
                
                    print("Wopps! The connection has been lost.\n")
                    print("Checking the connection..\n")
                    print("Reconnecting...\n")

                    if self.reconnect():
                        request_times -= 1
                        print("|__#CONNECTED!\n")
                        print("Continue!\n")

                        pass

                    else : 

                        self.reconnect()
                        request_times -= 1

                    pass                   
                
                except ClientThrottledError as e:

                    self.switching()
                    pass

                except ClientError as e:
                    
                    try:

                        if e == 'Not Found':
                            pass
                        else:
                            pass

                        if 'challenge' in json.loads(e.error_response):
                            
                            self.switching()

                    except:

                        pass
            
        print(" \n\n|")
        print(" |__# MISSION ACOMPLISHED! Please check result at https://akewcrafts.com/holascraper\n")

    def switching(self):
        accounts = config.random_account()
        selectAccount = randint(0,len(accounts))
        u = accounts[selectAccount]['username_ig']
        p = accounts[selectAccount]['password_ig']
        self.clear_cache()
        self.login(u,p)

    def test(self):
        return config.random_proxy()

from filecmp import clear_cache
from socket import *
import json
import sys
import os
import codecs
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
from instagram_private_api import ClientCookieExpiredError, ClientLoginRequiredError, ClientError, ClientThrottledError
from instagram_private_api import ClientConnectionError, ClientChallengeRequiredError, ClientCheckpointRequiredError, ClientSentryBlockError 

class Holascraper:

    api = None
    user_id = None
    target_id = None
    is_private = True
    following = False
    writeFile = True
    initiator = "holascraper.com"
    output_dir = "output"
    target = ""
    current_user = ""
    web_user = ""
    host = "https://instagram.com/"

    def __init__(self, target, user, is_cli, clear_cookies):
        
        self.checkConnection()
        accounts = config.random_account()
        selectAccount = randint(0,len(accounts)-1)
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

    def sendBasic(self,id,username,fullname,source,next_max_id):
        res = config.insertFollowers(id,username,fullname,self.target,source,next_max_id,self.web_user)
        return res
    
    def checkTarget(self,start=0,next=5):
        res = config.check_target(self.target,start,next,self.web_user)
        return res

    def updateStatus(self):
        res = config.update_status(self.target,self.web_user)
        return res

    def countTarget(self):
        res = config.target_counter(self.target,self.web_user)
        return res
        
    def updateData(self,id):
        config.update_data(id,self.target,self.web_user)
    
    def getAll(self):
        res = config.get_all_uncollected(self.web_user)
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

            print("\n\nplease wait.. \n")
            print("Collecting data.. \n \n")
            
            request_times = 0
            data_collected = 0
            
            for follower in followers:
                
                sleep(0.5)

                endpoint = 'users/{user_id!s}/full_detail_info'.format(**{'user_id': follower['id']})
                
                request_times += 1
              
                if request_times % 2 == 0:
                    sys.stdout.flush()
                    sleep(4)

                try:

                    content = self.api._call_api(endpoint)
                
                    result = content['user_detail']['user']
                    sys.stdout.write("\r collecting data from ")
                    print(str(result['username']))

                    self.updateData(result['pk'])

                    if 'contact_phone_number' in result and result['contact_phone_number']:

                        if self.sendDeep(result['username'],result['full_name'],result['category'],str(result['contact_phone_number']),result['public_email'],follower['source'],self.target) == "oke":
                            
                            data_collected += 1
                            sys.stdout.write(" \n\r%i data being collected\n" % data_collected)
                            sys.stdout.flush()
                            
                    else:
                        pass      

                except ClientChallengeRequiredError as e:
                    print('IG detects suspicious activity from our account\n')
                    pass

                except urllib.error.HTTPError as e:
                    pass
                
                except ClientConnectionError as e:
                    pass

                except ClientSentryBlockError as e:
                    print("IG has flagged our account for spam or abusive behavior\n")
                    pass 
                
                except ClientCheckpointRequiredError as e:
                    print("Wopps! The connection has been lost.\n")
                    print("Reconnecting...\n")

                    if self.reconnect():
                        print("===# CONNECTED!\n")
                        pass

                    else : 

                        self.reconnect()

                    pass                   
                
                except ClientThrottledError as e:
                    print("HUGE REQUEST WAS DETECTED BY INSTAGRAM!")
                    print("\n*** Switching...\n")

                    if self.switching():
                    
                        pass

                    else:
                        self.switching()

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

                            self.switching()                             
                            pass
                    
                    except:

                        pass
                
                except timeout:
                    print("Request timeout\n")
                    sleep(30)
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
        res = config.insert_data(username,fullname,phone,email,category,source,target,self.web_user) 
        return res
        
    def checkConnection(self):    
        timeout = 5

        print("\nChecking for connection... ")

        try:
            request = requests.get(self.host, timeout=timeout)
            print("OK! \n")
        except (requests.ConnectionError, requests.Timeout) as exception:
            print("DISCONNECTED! \n")
            sys.exit(1)
            
    def reconnect(self):
        
        timeout = 3
        
        try:
            requests.get(self.host, timeout=timeout)
            return True
        except (requests.ConnectionError, requests.Timeout) as exception:
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
                self.switching()
                # print("Please follow this link to complete the challenge: " + error['challenge']['url'])


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
        res = config.is_complete(self.target,self.web_user)
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
        config.update_wave(self.target,wave,self.web_user)
    
    def getWave(self):
        res = config.get_wave(self.target,self.web_user)
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
        
        if next_max_id == 0 or next_max_id == '0' or next_max_id == '':
            
            for user in data["users"]:
            
                    #private account akan diabaikan
                    if user['is_private'] == False: 
                        
                        if self.sendBasic(user['pk'],user['username'],user['full_name'],'followers',next_max_id) == 'oke':
                            counter+=1    
                            sys.stdout.write("\rCatched %i followers" % counter)
                            sys.stdout.flush()

            next_max_id = data.get('next_max_id')
            # print(next_max_id)
            self.updateWave(next_max_id) 
            pass

        else:
            # next_max_id = data.get(next_max_id)
            counter = self.countTarget()
            print("Continue from last activity...\n\n")
            # jika nilai wave bukan 0 maka counter akan dimulai dari total angka target yang berhasil di collect terakhir kali
            

            while next_max_id:
                
                if request_times%5 == 0:
                    
                    time.sleep(30) # setiap 5x hit API , aplikasi akan delay selama 10 menit untuk menghindari challenge
                
                try:

                    results = self.api.user_followers(str(self.target_id), rank_token=rank_token, max_id=next_max_id)

                    request_times += 1

                    for user in results["users"]:

                        if user['is_private'] == False:

                            if self.sendBasic(user['pk'],user['username'],user['full_name'],'followers',next_max_id) == 'oke':
                                counter+=1    
                                sys.stdout.write("\rCatched %i followers" % counter)
                                sys.stdout.flush()

                    next_max_id = results.get('next_max_id')
                    self.updateWave(next_max_id) 

                except timeout:
                    print("Request timeout, retry on next 30 seconds \n")
                    sleep(30)
                    pass
                
                except urllib.error.HTTPError as e:
                    pass
                
                except ClientConnectionError as e:
                
                    print("Wopps! The connection has been lost.\n")
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

                except ClientBadRequestError as e:
                    pass
                
                except ClientError as e:

                    try:
                        if e == 'Bad Request':
                            self.switching()
                            pass

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

            self.updateStatus()
            print('\nAll public account of followers target has been catched!')


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

        for follower in followers:
                
                endpoint = 'users/{user_id!s}/full_detail_info'.format(**{'user_id': str(follower['instagram_id'])})
                print(follower['instagram_username'])
                request_times += 1
              
                if request_times % 25 == 0:
                    sys.stdout.write(" \n Too many request, please wait 3 minutes\n")
                    sys.stdout.flush()
                    sleep(30)

                try:
                    self.updateData(follower['instagram_id'],follower['from_target'])
                    sleep(0.5)
                    content = self.api._call_api(endpoint,version='v2')
                    result = content['user_detail']['user']

                    sys.stdout.write("\r collecting data from ")
                    print(str(result['username']))

                    if 'contact_phone_number' in result and result['contact_phone_number']:

                        if self.sendDeep(result['username'],result['full_name'],result['category'],str(result['contact_phone_number']),result['public_email'],follower['source'],follower['from_target']) == "oke":
                            
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
        selectAccount = randint(0,len(accounts)-1)
        u = accounts[selectAccount]['username_ig']
        p = accounts[selectAccount]['password_ig']
        self.clear_cache()
        self.login(u,p)

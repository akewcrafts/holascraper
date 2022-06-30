from random import randint
from urllib import response
import mysql.connector
import json
from pprint import pprint
import smtplib,ssl
import requests


# Connect to db server

cnx = mysql.connector.connect(
host="HOST",
port=3306,
user="USERNAME",
password="PASSWORD",
database="DB")   

cur = cnx.cursor(dictionary=True,buffered=True)


def account_init():
    cur.execute("SELECT username,password FROM ig_account WHERE status = 1 LIMIT 1,1")
    myresult = cur.fetchall()[0]
    return myresult

def random_account():
    cur.execute("SELECT username_ig,password_ig FROM accounts")
    myresult = cur.fetchall()
    return myresult

def banned_account(username):
    update_sql = f"UPDATE accounts SET is_banned = 1 WHERE username_ig='{username}'"
    cur.execute(update_sql)
    cnx.commit()
    
def insertFollowers(instagram_id,instagram_username,instagram_fullname,from_target,source,next_max_id,user):

    sql = "INSERT INTO instagram_data (instagram_id, instagram_username, instagram_fullname, is_collected, from_target, source, wave_id, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = (instagram_id, instagram_username, instagram_fullname, '0', from_target, source, next_max_id, user)
    try:
        cur.execute(sql, val)
        cnx.commit()
        return "oke"

    except mysql.connector.Error as err:
        
        print("Something went wrong: {}".format(err))

def insertFollowersBatch(data):

    sql = "INSERT IGNORE INTO instagram_data (instagram_id, instagram_username, instagram_fullname, is_collected, from_target, source) VALUES (%s, %s, %s, %s, %s, %s)"
    # val = (instagram_id, instagram_username, instagram_fullname, '0', from_target, source)
    try:
        cur.executemany(sql, data)
        cnx.commit()
    
        return "oke"
         
    except mysql.connector.Error as err:
        
        print("Something went wrong: {}".format(err))


def is_complete(target,user_id):

    sql = f"SELECT is_completed FROM target WHERE target_username ='{target}' AND user_id={user_id}" 
    
    try:
        cur.execute(sql)

        res = cur.fetchall()[0]

        return res['is_completed']

    except:

        return False

def get_wave(target,user):

    sql = f"SELECT last_max_id FROM target WHERE target_username = '{target}' AND is_completed = 0 AND user_id={user}"
    
    cur.execute(sql)
    
    if cur.rowcount > 0:

        res = cur.fetchall()[0]
        return res['last_max_id']
    
    else:

        return '0'


def get_all_uncollected(user_id):

    sql = f"SELECT instagram_id,instagram_username,source,from_target FROM instagram_data WHERE is_collected = 0 AND user_id ={user_id}"
    
    cur.execute(sql)   
    if cur.rowcount > 0:

        res = cur.fetchall()
        return res
    
    else:
        
        return '0'

def target_counter(target,user_id):
    
    sql = f"SELECT COUNT(instagram_id) as total_target FROM instagram_data WHERE from_target='{target}' AND is_collected = 0 AND user_id={user_id}"
    cur.execute(sql)
    res = cur.fetchall()[0]

    return res['total_target']
    
def update_wave(target,last_max_id,user_id):

    # query get target username
    select_sql = f"SELECT target_username FROM target WHERE target_username='{target}' AND user_id={user_id}"

    # query update last_max_id
    update_sql = f"UPDATE target SET last_max_id ='{last_max_id}' WHERE target_username='{target}' AND user_id={user_id}"
    
    # execute query get target username
    cur.execute(select_sql)
    
    # check target doesn't exist
    if cur.rowcount == 0:
        
        # insert new target data
        
        insert_sql = "INSERT INTO target (target_username,last_max_id,user_id) VALUES (%s,%s,%s)"
        val = (target,last_max_id,user_id)
        
        cur.execute(insert_sql,val)
        cnx.commit()
        
    else:
        # target already exist, update last_max_id
        cur.execute(update_sql)
        cnx.commit()
        

def update_status(target,user_id):
    update_sql = f"UPDATE target SET is_completed = 1 WHERE target_username='{target}' AND user_id={user_id}"
    cur.execute(update_sql)
    cnx.commit()

def check_target(target,start,limit,user_id):

    sql = f"SELECT instagram_id,source FROM instagram_data WHERE from_target='{target}' AND user_id={user_id} AND is_collected = 0 LIMIT {start},{limit}"
    
    try:

        cur.execute(sql)
        rows = list(cur.fetchall())
        
        res = []

        for row in rows:
            
            u = {
                'id':row['instagram_id'],
                'source':row['source']
            }

            res.append(u)
        
        return res
    
    except:

        return 'nope'
    
def insert_data(username,fullname,phone,email,category,source,target,user_id):
    sql = "INSERT INTO collected_data (username,fullname,phone,email,category,source,from_target,user_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
    val = (username,fullname,phone,email,category,source,target,user_id)
    
    try:
        cur.execute(sql, val)
        cnx.commit()

        return 'oke'
    
    except:
    
        return 'nope'

def update_data(id,target,user_id):
    sql = f"UPDATE instagram_data SET is_collected = 1 WHERE instagram_id='{id}' AND from_target='{target}' AND user_id={user_id}"
    cur.execute(sql)
    cnx.commit()

#!/usr/bin/env python

from src.MainClass import Holascraper
import argparse


import signal
import logging
import sys


sys.tracebacklimit = 5
logging.INFO

is_windows = False

try:
    import gnureadline  
except: 
    is_windows = True
    import pyreadline


def cmdlist():
    print("cache\t\t")
    print("Clear cache of the tool")
    print("fwersdata\t")
    print("Get data of follower")   
    print("fwingdata\t")
    print("Get data of users following")   


def signal_handler(sig, frame):
    print("\nGoodbye!\n")
    sys.exit(0)

def completer(text, state):

    options = [i for i in commands if i.startswith(text)]

    if state < len(options):

        return options[state]

    else:

        return None

def _quit():
    
    print("Goodbye!\n")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

if is_windows:
    pyreadline.Readline().parse_and_bind("tab: complete")
    pyreadline.Readline().set_completer(completer)
else:
    gnureadline.parse_and_bind("tab: complete")
    gnureadline.set_completer(completer)

parser = argparse.ArgumentParser(description='Holascraper is a tool to collect basic personal information of instagram\'s user such as username,email and phonenumber '
                                             'to perform analysis and generate sales leads for the company')
parser.add_argument('id', type=str, help='target username')
parser.add_argument('user', type=str, help='executor')
parser.add_argument('-C','--cookies', help='clear\'s previous cookies', action="store_true")
parser.add_argument('-c', '--command', help='run in single command mode & execute provided command', action='store')
parser.add_argument('-o', '--output', help='where to store photos', action='store')

args = parser.parse_args()

api = Holascraper(args.id, args.user, args.command, args.cookies)

commands = {
    
    'list':             cmdlist,
    'help':             cmdlist,
    'quit':             _quit,
    'exit':             _quit,
    'cache':            api.clear_cache,
    'fwingdata':      api.get_data_following,
    'fwersdata':      api.get_data_followers,
    'catchfwers':      api.catch_followers,
    'collectdata':      api.collectData,
    'catchfwings':      api.catch_followers,
    'collectall':api.collectAll
    
}


signal.signal(signal.SIGINT, signal_handler)

if is_windows:
    pyreadline.Readline().parse_and_bind("tab: complete")
    pyreadline.Readline().set_completer(completer)
else:
    gnureadline.parse_and_bind("tab: complete")
    gnureadline.set_completer(completer)

while True:
    if args.command:
        cmd = args.command
        _cmd = commands.get(args.command)
    else:
        signal.signal(signal.SIGINT, signal_handler)
        if is_windows:
            pyreadline.Readline().parse_and_bind("tab: complete")
            pyreadline.Readline().set_completer(completer)
        else:
            gnureadline.parse_and_bind("tab: complete")
            gnureadline.set_completer(completer)
        print("\nRun a command: ")
        cmd = input()

        _cmd = commands.get(cmd)

    if _cmd:
        _cmd()
    elif cmd == "JSON=y":
        api.set_json_dump(True)
    elif cmd == "JSON=n":
        api.set_json_dump(False)
    elif cmd == "":
        print("")
    else:
        print("Unknown command\n")
    if args.command:
        break

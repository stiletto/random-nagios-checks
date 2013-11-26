#!/usr/bin/env python2
# coding: utf-8

import argparse, socket, struct, sys, traceback, json
from minecraft_query import MinecraftQuery

parser = argparse.ArgumentParser('Check minecraft server status')

parser.add_argument('-H','--host', help='Server IP or hostname', required=True)
parser.add_argument('-p', '--port', help='Server port', type=int, default=25565)
parser.add_argument('-w', '--warning', help='Player count warning threshold (fraction of max players, 0.0-1.0)', type=float, default=0.75)
parser.add_argument('-c', '--critical', help='Player count critical threshold (fraction of max players, 0.0-1.0)', type=float, default=0.99)
parser.add_argument("-r", "--retries", type=int, default=3, help='retry query at most this number of times [3]')
parser.add_argument("-t", "--timeout", type=int, default=3, help='retry timeout in seconds [10]')

args = parser.parse_args()

def assertcrit(cond, text):
    if not cond:
        exit('CRITICAL',text)

def exit(state, text):
    print '%s - %s' % (state, text)
    sys.exit({ 'OK': 0, 'WARNING': 1, 'CRITICAL': 2}.get(state, 3))

try:
    query = MinecraftQuery(args.host, args.port,
                           timeout=args.timeout,
                           retries=args.retries)
    server_data = query.get_rules()
except socket.error as e:
    exit('CRITICAL', 'Socket error: '+e.message)

try:
    version = server_data['version']
    motd = server_data['motd']
    players = server_data['numplayers']
    playermax = server_data['maxplayers']
except:
    exit('CRITICAL', 'Invalid data')

state = 'OK'
playerfraction = players*1.0/playermax
if playerfraction >= args.critical:
    state = 'CRITICAL'
elif playerfraction >= args.warning:
    state = 'WARNING'
exit(state, '[%d/%d] %s %s' % (players, playermax, version, motd))

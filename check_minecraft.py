#!/usr/bin/env python2
# coding: utf-8
#import time
#st = time.time()
#print time.time()-st,'begin'
import argparse, socket, struct, sys, traceback
#print time.time()-st,'import'

parser = argparse.ArgumentParser('Check minecraft server status')

parser.add_argument('-H','--host', help='Server IP or hostname', required=True)
parser.add_argument('-p', '--port', help='Server port', type=int, default=25565)
parser.add_argument('-s', '--version', help='Minecraft Protocol version', choices=['beta','1.4','1.6'], default='1.6')
parser.add_argument('-w', '--warning', help='Player count warning threshold (fraction of max players, 0.0-1.0)', type=float, default=0.75)
parser.add_argument('-c', '--critical', help='Player count critical threshold (fraction of max players, 0.0-1.0)', type=float, default=0.99)

args = parser.parse_args()
#print time.time()-st,'pa'
def assertcrit(cond, text):
    if not cond:
        exit('CRITICAL',text)

def exit(state, text):
    print '%s - %s' % (state, text)
    sys.exit({ 'OK': 0, 'WARNING': 1, 'CRITICAL': 2}.get(state, 3))

soc = socket.socket()
try:
    soc.connect((args.host,args.port))
    #print time.time()-st,'connect'

    sf = soc.makefile()

    if args.version in ('1.6', '1.4'):
        payload = struct.pack('>BHsI', 73, len(args.host), args.host.encode('utf-16be'), args.port)

        plugname = u"MC|PingHost"
        packet = struct.pack('>BBBHsHs', 0xFE, 0x01, 0xFA,
                                         len(plugname), plugname.encode('utf-16be'),
                                         len(payload), payload)
        sf.write(packet)
        sf.flush()
        #print time.time()-st,'write'
        bys = []
        while True:
            s = sf.read()
            if s=='': break
            bys.append(s)
        #print time.time()-st,'read'
        bys = ''.join(bys)
        assertcrit(len(bys) > 3, 'Response packet is truncated')
        kick, paylen = struct.unpack('>BH',bys[:3])
        payload = bys[3:]
        assertcrit(kick == 0xFF, 'Protocol mismatch. Not a kick packet')
        try:
            payload = payload.decode('utf-16be')
        except UnicodeDecodeError, e:
            exit('CRITICAL', 'Couldn\'t decode payload %s: %s' % (repr(payload),str(e)))
        assertcrit(len(payload) == paylen, 'Protocol mismatch. Wrong length')

        if args.version == '1.6':
            payload = payload.split(u'§')
            assertcrit(len(payload) == 3, 'Protocol mismatch. Wrong number of fields in payload. %s' % (repr(payload)))
            version, motd, players, playermax = '1.6.x', payload[0], int(payload[1]), int(payload[2])
        else:
            payload = payload.split('\x00')
            assertcrit(len(payload) == 6, 'Protocol mismatch. Wrong number of fields in payload. %s' % (repr(payload)))
            version, motd, players, playermax = payload[2], payload[3], int(payload[4]), int(payload[5])
        #print time.time()-st,'parse'

        state = 'OK'
        playerfraction = players*1.0/playermax
        if playerfraction >= args.critical:
            state = 'CRITICAL'
        elif playerfraction >= args.warning:
            state = 'WARNING'
        exit(state, '[%d/%d] %s %s' % (players, playermax, version, motd))
except socket.error, e:
    exit('CRITICAL', str(e))

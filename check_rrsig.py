#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import datetime, sys, time
import dns.resolver
import dns.rdataclass
import dns.rdatatype
import dns.flags
from optparse import OptionParser

if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    optp.add_option("-d", "--domain", dest="domain",
                    help="domain")
    optp.add_option("-s", "--server", dest="server",
                    help="domain")
    optp.add_option("-w", "--warn", dest="warn",
                    help="warn N days before expiration")
    optp.add_option("-c", "--crit", dest="crit",
                    help="critical N days before expiration")

    opts, args = optp.parse_args()

    resolver = dns.resolver.Resolver()
    #resolver.use_edns(0,dns.flags.DO,4096)

    if opts.server:
        resolver.nameservers = ([opts.server])

    try:
        answer = resolver.query(opts.domain, 'RRSIG', raise_on_no_answer=False)
    except Exception as e:
        print "CRITICAL. %s %s" % (opts.domain, e.__class__.__name__)
        sys.exit(2)
    response = answer.response
    now = time.time()
    gotrec = False
    rem = 2**32
    rs = [0, 'OK']
    for rdata in response.answer:
        for item in rdata.items:
            gotrec = True
            rem = min(rem,(item.expiration-now)/86400)
    if not gotrec:
        print "CRITICAL. %s no response." % (opts.domain, )
        sys.exit(2)
    if rem < int(opts.crit or '0'):
        rs = [2,'CRITICAL']
    elif rem < int(opts.warn or '0'):
        rs = [1,'WARNING']
    if rem > 0:
        print "%s. %s RRSIG is expiring in %d days." % (rs[1],opts.domain,rem)
    else:
        print "%s. %s RRSIG expired %d days ago." % (rs[1],opts.domain,-rem)
    sys.exit(rs[0])

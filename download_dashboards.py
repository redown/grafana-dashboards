#!/usr/bin/env python
"""
list or download grafana dashboards as local files
this can be used to backup dashboards or stage for source control

For information on grafana: http://www.grafana.com

Copyright 2015-2016 Richard.Elling@RichardElling.com

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import sys
import urllib2
import json
from argparse import ArgumentParser
from base64 import b64encode

parser = ArgumentParser(
    description='Upload previously downloaded JSON dashboards into grafana')
parser.add_argument('--hostname', action='store', default='localhost',
                    help='grafana hostname (default=localhost)')
parser.add_argument('--port', action='store', default=3000,
                    help='TCP port number (default=3000)')
parser.add_argument('--username', action='store', default='admin',
                    help='grafana username (default=admin)')
parser.add_argument('--password', action='store', default='admin',
                    help='USERNAME\'s password (default=admin)')
parser.add_argument('--key', action='store',
                    help='API key (supersedes username/password)')
parser.add_argument('--list', action='store_true',
                    help='list available dashboards, but do not download')
parser.add_argument('--debug', action='store_true',
                    help='show debugging information')

options = parser.parse_args()

# setup urllib2 for getting
if options.debug:
    opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
else:
    opener = urllib2.build_opener()

if options.key:
    opener.addheaders = [('Authorization', 'Bearer {}'.format(options.key))]
else:
    basic_auth_string = b64encode(
        '{}:{}'.format(options.username, options.password))
    opener.addheaders = [
        ('Authorization', 'Basic {}'.format(basic_auth_string))]
urllib2.install_opener(opener)

# get list of available dashboards
url = 'http://{}:{}/api/search'.format(options.hostname, options.port)
try:
    req = urllib2.Request(url)
    res = opener.open(req)
except urllib2.URLError as exc:
    print 'error: cannot open URL {}: {}'.format(url, exc)
    sys.exit(1)

try:
    dashboard_list = json.loads(res.read())
except Exception as exc:
    print('error: list results: {}'.format(exc))
    sys.exit(1)

fmt = '{:40s} {}'
print(fmt.format('filename', 'title'))
for dashboard in dashboard_list:
    filename = dashboard.get('uri', '').split('/')[-1] + '.json'
    print(fmt.format(filename, dashboard.get('title', '-')))
    if not options.list and filename:
        try:
            url = 'http://{}:{}/api/dashboards/{}'.format(options.hostname,
                                                          options.port,
                                                          dashboard.get('uri'))
            req = urllib2.Request(url)
            res = opener.open(req)
        except urllib2.URLError as exc:
            print('error: cannot read dashboard URL {}: {}'.format(url, exc))
            continue
        dashboard_contents = res.read()
        # noinspection PyBroadException
        try:
            with open(filename, 'w') as f:
                f.write(dashboard_contents)
        except Exception:
            print('error: cannot read dashboard: {}'.format(filename))

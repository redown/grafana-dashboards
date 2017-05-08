#!/usr/bin/env python
"""
upload one or more downloaded grafana dashboards as a new dashboard

For information on grafana: http://www.grafana.com

Copyright 2015-2017 Richard.Elling@RichardElling.com

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
parser.add_argument('--overwrite', action='store_true',
                    help='overwrite an existing dashboard of the same name')
parser.add_argument('--debug', action='store_true',
                    help='show debugging information')
parser.add_argument('files', nargs='+', action='store',
                    help='JSON files for grafana dashboards')

options = parser.parse_args()

# setup urllib2 for posting
url = 'http://{}:{}/api/dashboards/db'.format(options.hostname, options.port)
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

for dashboard_file in options.files:
    if options.debug:
        print 'uploading filename: {}'.format(dashboard_file)
    try:
        with open(dashboard_file, 'r') as f:
            file_json = json.load(f)
    except IOError as exc:
        print 'error: cannot read file {}: {}'.format(dashboard_file, exc)
        continue
    except ValueError as exc:
        print 'error: cannot decode JSON from file {}: {}'.format(
            dashboard_file, exc)
        continue

    # to upload in grafana as a new dashboard, the id should be null
    if 'id' not in file_json:
        print 'error: file {} does not contain a dashboard id'
        continue
    file_json['id'] = None

    to_upload = {'dashboard': file_json, 'overwrite': options.overwrite}
    if options.debug:
        print 'json to upload = {}'.format(json.dumps(to_upload, indent=4))

    # post to grafana
    try:
        # res = opener.open(url, json.dumps(to_upload))
        req = urllib2.Request(url, data=json.dumps(to_upload),
                              headers={'Content-Type': 'application/json'})
        res = opener.open(req)
    except urllib2.URLError as exc:
        print 'error: cannot open URL {}: {}'.format(url, exc)
        continue

    if options.debug:
        print 'response = {}'.format(res.read())

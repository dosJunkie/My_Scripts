import threading
import time
import json
import urllib.request
from typing import List
from datetime import datetime
from http.client import HTTPResponse


class Splunk:
def __init__(self, url: str, token: str, host: str, source: str, source_type: str) -> None:
# Adding this check because the urlopen allows for files to be passed opening a potential vulnerability
if url.startswith('https'):
self.url = url
self.token = token
self.host = host
self.source = source
self.source_type = source_type
self.headers = {'Authorization': f"Splunk {self.token}"}
else:
return

def _threaded_send(self, payloads, source: str = None, time_key: str = None, time_format: str = None):
"""
Helper function for sending payloads using threading.

:param payloads: list of payloads
:param source: Splunk source
:param time_key: define the dict key where the event time is defined
:param time_format: define the time format
"""

for payload in payloads:
self.send(payload=payload, source=source, time_key=time_key, time_format=time_format)

def _build_post_data(self, payload: dict, time_key: str = None, time_format: str = None) -> dict:
"""
Builds POST data for the payload provided, adding time, host, source etc.

:param payload: dict payload
:param time_key: define the dict key where the event time is defined
:param time_format: define the time format
:return: dict
"""

if time_key is not None and time_format is not None:
raw_date = str(payload[time_key])
if raw_date.endswith("Z"):
raw_date = raw_date[:-1]
raw_date += "UTC"

event_time = datetime.strptime(raw_date, time_format).timestamp()
else:
event_time = time.time()

post_data = {
"time": event_time,
"host": self.host,
"source": self.source,
"sourcetype": self.source_type,
"event": payload
}
return post_data

def send(self, payload: dict, source: str = None, time_key: str = None, time_format: str = None) -> HTTPResponse:
"""
Sends a payload.

:param payload: dict payload
:param source: Splunk source (default = self.source)
:param time_key: define the dict key where the event time is defined
:param time_format: define the time format
:return: HTTPResponse
"""

if source is not None:
self.source = source

data = json.dumps(self._build_post_data(payload=payload, time_key=time_key, time_format=time_format)).encode('utf8')
request = urllib.request.Request(method='POST', url=self.url, data=data, headers=self.headers)
# Marking the following line to be ignored by Bandit since a check is put on the object construction
response = urllib.request.urlopen(request) # nosec
return response

def bulk_send(self, payloads: List[dict], source: str, workers: int = 5, time_key: str = None, time_format: str = None) -> None:
"""
Sends a list of payloads using threading.

:param payloads: list of dicts, each dict is a payload
:param source: Splunk source, required to avoid race condition with self.source
:param workers: number of worker threads
:param time_key: define the dict key where the event time is defined
:param time_format: define the time format
"""

jobs = []
chuncks = [payloads[i:i + workers] for i in range(0, len(payloads), workers)]
for chunck in chuncks:
jobs.append(threading.Thread(target=self._threaded_send, args=(chunck, source, time_key, time_format)))
for job in jobs:
job.start()
for job in jobs:
job.join()


class Elastic:
def __init__(self) -> None:
raise NotImplementedError(f"HEC collector not implemented for '{self.__name__}'.")

import json
import time

import numpy
import requests

with open("get_request_rtx_3080.json", "r") as in_:
    get_request = json.load(in_)

with open("post_request_rtx_3080.json", "r") as in_:
    post_request = json.load(in_)

s = requests.Session()
s.get(get_request["url"], headers=get_request["headers"])


for _ in range(1):
    r = s.post(
        post_request["url"], headers=post_request["headers"], data=post_request["data"]
    )
    print(r.status_code)
    time.sleep(numpy.random.uniform(5, 10))

with open("<retailer_a>.html", "w") as out:
    out.write(r.text)

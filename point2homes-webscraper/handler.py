import json
import os

def handler(event, context):
    print(json.dumps(event))
    print(os.environ.get('ENV'))
    return dict(status=200, body=json.dumps(event))

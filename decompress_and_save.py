import gzip
import json
import sys

def load_compressed_json(filename):
    with gzip.GzipFile(filename, 'rb') as f:
        json_bytes = f.read()
    json_str = json_bytes.decode('utf-8')  # Convert bytes to string
    return json.loads(json_str)

parsed_dict = load_compressed_json(sys.argv[1])

with open(sys.argv[2], "w") as f:
    json.dump(parsed_dict, f)
import subprocess
import re


# Runs arp -a and returns the IP address of the first entry
def get_ip():
    arp_res = subprocess.check_output(["arp", "-a"]).decode("utf-8")
    return re.search(r"192\.168\.\d+\.111", arp_res).group(0)[:-3] + "221"

print(get_ip())

from get_ip import get_ip
from paramiko import SSHClient
from scp import SCPClient
import datetime
import os


# Get Raspberry Pi's IP address
ip = get_ip()

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.connect(ip, username='ubuntu', password='abc123!')

# SCPCLient takes a paramiko transport as an argument
scp = SCPClient(ssh.get_transport())

stdin, stdout, stderr = ssh.exec_command("ls test_data")

files = stdout.read().decode('utf-8').split('\n')

for file in files:
    if file.endswith(".txt"):
        timestamp = file[:-4]
        time = datetime.datetime.fromtimestamp(float(timestamp)/1e9)
        directory = f"{time.year}-{time.month}-{time.day}"
        file_name = f"{time.hour}-{time.minute}-{time.second}.txt"
        if not os.path.isdir(f"./data/{directory}"):
            os.mkdir(f"./data/{directory}")
        if os.path.isfile(f"./data/{directory}/{file_name}"):
            continue
        scp.get("/home/ubuntu/test_data/" + file, f"./data/{directory}/{file_name}")

scp.close()
ssh.close()
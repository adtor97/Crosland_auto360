# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 01:22:42 2021

@author: Usuario
"""
#%%
import paramiko
host = "192.1.1.108"
port = 21
transport = paramiko.Transport((host, port)) 
password = "Domi$$2021"
username = "dominum"
transport.connect(username = username, password = password)
sftp = paramiko.SFTPClient.from_transport(transport)
filepath = '/var/www/crosland/crosland_app/static/files_to_download/Dashboard_360.pbix'
localpath = 'C:\\Users\\Usuario\\Documents\\Freelos\\Crosland\\Crosland_auto360\\static\\files_to_download\\Dashboard_360.pbix'
sftp.put(localpath, filepath)
sftp.close()
transport.close()
#%%
import paramiko
from scp import SCPClient

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

filepath = '/var/www/crosland/crosland_app/static/files_to_download/Dashboard_360.pbix'
localpath = 'C:\\Users\\Usuario\\Documents\\Freelos\\Crosland\\Crosland_auto360\\static\\files_to_download\\Dashboard_360.pbix'
ssh = createSSHClient(host, port, username, password)
scp = SCPClient(ssh.get_transport())
scp.put(localpath, filepath)
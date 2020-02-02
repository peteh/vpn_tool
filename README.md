# vpn_tool
Tool to add openvpn files from NordVPN to Linux Network Manager. It also allows to benchmark different servers by cycling through all nordvpn servers and downloading a 10mb file. 

## Usage
vpn.py import

Imports all .ovpn in the current directory where the script resides. It will ask for username and password and add it to network manager. It will not add duplicate entries. 

vpn.py clear

Deletes all nordvpn servers from network manager

vpn.py benchmark

Cycles through all nordvpn entries and downloads a 10mb with each. At the end it prints a list of the max average speed of each server. 

## Motivation
This tool allows to find the fastest server at the time of testing. 

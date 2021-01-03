#!/bin/python3
import argparse
import getpass
import os
import re
import requests
import subprocess
from urllib.parse import urlparse

__version__ = '1.1.0'
PATH = './'
RESTRICTED_PAGE = 'https://support.nordvpn.com/Restricted-countries/1391702632/Connecting-from-countries-with-internet-restrictions-on-Windows.htm'
ALL_PAGE = 'https://nordvpn.com/ovpn/'

def runProcess(command):
    # Invoke the command and pass its output streams to the completedProc object
    # run()'s return value is an object with information about the completed process. 
    completedProc = subprocess.run(command, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Print the exit code.
    #print("returned with exit code: %d" % (completedProc.returncode))
    return completedProc

def connectionExists(connection):
    completedProcess = runProcess(["nmcli", "-f", "GENERAL.STATE", "con", "show", connection])
    return completedProcess.returncode != 10

def importConnection(connectionFile):
    print("Importing Profile: '%s'" % (connectionFile))
    runProcess(["nmcli", "connection", "import", "type", "openvpn", "file", connectionFile])

def setUserAndPass(connection, user, password):
    print("Setting user name and password for %s" % (connection))
    runProcess(["nmcli", "connection", "modify", 
                connection, 
                "+vpn.data", "username=%s" % (user),
                "+vpn.secrets", "password=%s" % (password)])
    
def getConnections(filter=None):
    completedProcess = runProcess(["nmcli", "connection", "show"])
    output = completedProcess.stdout
    lines = output.splitlines()
    nameLen = lines[0].find('UUID')
    connections = []
    for line in lines[1:]:
        connection = line[:nameLen].strip()
        if filter is None or connection.find(filter) != -1:
            connections.append(connection)
    return sorted(connections)

def deleteConnection(connection):
    print("Deleting: %s" % (connection))
    runProcess(["nmcli", "connection", "delete", connection])
    
def deleteConnections(connections):
    for connection in connections: 
        deleteConnection(connection)
        
def importNewProfiles(searchPath):
    connectionFiles = [f for f in os.listdir(searchPath) if os.path.isfile(os.path.join(searchPath, f)) and f.endswith('.ovpn')]

    if len(connectionFiles) == 0:
        print("No files found to import")
        return
    
    vpnUsername = input("Enter your vpn username: ")
    vpnPassword = getpass.getpass("Enter your vpn password: ")
    
    for connectionFile in connectionFiles: 
        print(connectionFile)
        connection = connectionFile[:-5]
        print(connection)
        if connectionExists(connection):
            print("Connection '%s' exists - skipping" % (connection))
            continue

        importConnection(connectionFile)
        setUserAndPass(connection, vpnUsername, vpnPassword)

def downloadBenchmarkFile():
    import requests
    import time
    import sys
    start = time.time()
    print("Starting Benchmark")
    
    timeout = 60
    #remoteFile = "http://87.76.21.20/test.zip" # amsterdam
    remoteFile = "http://fra36-speedtest-1.tele2.net/10MB.zip" # tele2 frankfurt
    
    try: 
        # get file size: 
        resGet = requests.get(remoteFile,stream=True)
        fileSize = int(resGet.headers['Content-length']) # output 121291539
        local_filename = "tmp.dat"
        # NOTE the stream=True parameter below
        timedOut = False
        with requests.get(remoteFile, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=81920): 
                if chunk: # filter out keep-alive new chunks
                    #f.write(chunk)
                    #print(len(chunk))
                    # if time takes more than a minute we cancel
                    current = time.time()
                    if current - start > timeout:
                        timedOut = True
                        break
                    sys.stdout.write("-")
                    sys.stdout.flush()
                    # f.flush()
        print("")
        if timedOut: 
            # TODO: make this handling better
            print("Timeout: Benchmark exceeded %fs" % (timeout))
            return -1
        end = time.time()
        totalTime = end - start
        kbS = fileSize / totalTime / 1024.
        print("Finished Benchmark: %.3fs %.3fkb/s" % (totalTime, kbS))
        return kbS
    # catch keyboard and raise again to allow termination
    except KeyboardInterrupt:
        raise
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return -1

def connectConnection(connection):
    print("Trying to connect: %s" % (connection))
    completedProcess = runProcess(["nmcli", "con", "up", "id", connection])
    # returns true if connection was successful
    return completedProcess.returncode == 0

def disconnectConnection(connection):
    print("Trying to disconnect: %s" % (connection))
    completedProcess = runProcess(["nmcli", "con", "down", "id", connection])
    # returns true if connection was successful
    return completedProcess.returncode == 0

def benchmarkConnections(filter):
    benchmarkResults = []
    for connection in getConnections(filter):
        kbS = benchmarkConnection(connection)
        benchmarkResults.append([connection, kbS])
    
    for benchmarkResult in benchmarkResults:
        connection = benchmarkResult[0]
        kbS = benchmarkResult[1]
        print("%s: %.3fkb/s" % (connection, kbS))
    
def benchmarkConnection(connection):
    if not connectConnection(connection):
        return -1
    time = downloadBenchmarkFile()
    disconnectConnection(connection)
    return time


def downloadFile(path, url):
    print('Downloading file: ' + url)
    parsed = urlparse(url)
    fileName = os.path.basename(parsed.path)
    
    targetFile = path + fileName
    if os.path.exists(targetFile):
        print('File ' + fileName + ' already exists')
        return
    r = requests.get(url)
    with open(targetFile, 'wb') as f:
        f.write(r.content)
    print('Finished download: ' + fileName)

def downloadFromPage(path, pageUrl):
    page = requests.get(pageUrl)
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', page.text)
    for url in urls:
        if url.endswith('.ovpn') and 'udp' in url:
            downloadFile(path, url)


def clear_cmd(args):
    deleteConnections(getConnections("nordvpn.com"))

def benchmark_cmd(args):
    benchmarkConnections("nordvpn")

def dl_all_cmd(args):
    downloadFromPage(PATH, ALL_PAGE)

def dl_restricted_cmd(args):
    downloadFromPage(PATH, RESTRICTED_PAGE)
    
def import_cmd(args):
    importNewProfiles(PATH)
    
if __name__ == '__main__':
    print("NORDVPN Helper Tool " + __version__)
    # main parser
    parser = argparse.ArgumentParser(description='NordVPN Tooling')
    subparsers = parser.add_subparsers()

    # clear vpns
    clear_parser = subparsers.add_parser('clear')
    clear_parser.set_defaults(dispatch=clear_cmd)
    
    # add new vpns from the local path
    import_parser = subparsers.add_parser('import')
    import_parser.set_defaults(dispatch=import_cmd)
    
    # benchmark existing vpns
    benchmark_parser = subparsers.add_parser('benchmark')
    benchmark_parser.set_defaults(dispatch=benchmark_cmd)
    
        # clear vpns
    clear_parser = subparsers.add_parser('downloadrestricted')
    clear_parser.set_defaults(dispatch=dl_restricted_cmd)
    
    # add new vpns from the local path
    import_parser = subparsers.add_parser('downloadall')
    import_parser.set_defaults(dispatch=dl_all_cmd)
    
    args = parser.parse_args()
    if 'dispatch' in args:
        cmd = args.dispatch
        del args.dispatch
        cmd(args)
    else:
        parser.print_usage()

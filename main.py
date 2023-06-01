import select
import socket
import subprocess
import time
import yaml
import threading
import os
import signal
import psutil
import subprocess
from multiprocessing import Process

def getConfig():
    with open('config.yml') as f:
        config = yaml.safe_load(f)

    host = config['host']
    timeout = config['timeout']
    ports = config['ports']
    path = config['path']

    config = [host, ports, timeout,path]
    return config

def knockPort(addr, port):
    signal = 0
    cont = True
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((addr, port))
    except socket.error as e:
        print(e)
    sock.listen(1)
    print("Monitoring port: ", port,addr)

    while cont:
        listo_lectura, _, _ = select.select([sock], [], [], 2)

        if listo_lectura:
            conexion, direccion = sock.accept()
            print("Request from:", direccion)
            conexion.close()
            sock.close()
            cont = False
            signal = 1

    return signal


def runScript(path):
    global pid
    path = path
    result = subprocess.Popen(["bash", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid = result.pid
    ouput, err = result.communicate()
    if result.returncode == 0:
        print(ouput)
    else:
        print(err)

def listenKey(config):
    addr = config[0]
    ports = config[1]
    timeout = config[2]
    path = config[3]
    pidScritp = 0
    while True:
        next = 0
        initTime = time.time()
        finaltime = initTime + timeout
        for port in ports:
            if knockPort(addr, port) == 1 and time.time() < finaltime:
                next = next + 1
            else:
                break
        if next == len(ports):
            if pidScritp != 0:
                os.kill(pidScritp, signal.SIGKILL)
            else:
                thread_runScript = Process(target=runScript, args=(path,))
                thread_runScript.start()
                pidP = psutil.Process().pid
                process = psutil.Process(pidP)
                childrenProcess = process.children()
                pidScritp = childrenProcess[0].pid
                print(pidScritp)
                print(pidP)

if __name__ == "__main__":
    config = getConfig()
    listenKey(config)
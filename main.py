import select
import socket
import time
import yaml
import psutil
import subprocess
import os
import sys

STERMINAL = "sudo"
SERVICE = "service"


def getConfig(Path):
    with open(Path) as f:
        readConfig = yaml.safe_load(f)

    host = readConfig['host']
    timeout = readConfig['timeout']
    ports = readConfig['ports']
    ordenType = readConfig['orden-type']
    orden = readConfig['orden']
    loadConfig = [host, ports, timeout, ordenType, orden]
    return loadConfig


def getArgument():
    argument = 0
    if len(sys.argv) > 1:
        argument = sys.argv[1]
    else:
        argument = 'config.yml'
    return argument


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
    print("Monitoring port: ", port, addr)

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


def serviceCommand(process, toggle):
    vsftp = subprocess.Popen([STERMINAL, SERVICE, process, toggle], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err, stdo = vsftp.communicate()
    if vsftp.returncode == 0:
        print("Done")
    else:
        print(err.decode())


def processVerification(processName):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == processName:
            return True

    return False


def check_iptables_rule(rule):
    check = False
    command = f"sudo iptables -C {rule}"
    exit_code = os.system(command)
    if exit_code == 0:
        check = True
    return check


def listenKey(config):
    addr = config[0]
    ports = config[1]
    timeout = config[2]
    ordenType = config[3]
    orden = config[4]

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
            if ordenType == "service":
                if processVerification(orden[0]):
                    serviceCommand(orden[0], orden[2])
                else:
                    serviceCommand(orden[0], orden[1])
            if ordenType == "iptables":
                rule = str(orden[0]) + " -p " + str(orden[1]) + " --dport " + str(orden[2]) + " -j " + str(orden[3])
                if check_iptables_rule(rule):
                    os.system(STERMINAL + " iptables " + " -D " + rule)
                else:
                    os.system(STERMINAL + " iptables " + " -A " + rule)
            if ordenType == "command":
                os.system(orden[0] + " &")


if __name__ == "__main__":
    config = getConfig(getArgument())
    listenKey(config)

#!/bin/python3
import select
import socket
import time
import yaml
import psutil
import subprocess
import os
import sys
import logging
import getpass
import signal

SUDO = "sudo"
SERVICE = "service"
LOGGER = logging.getLogger(__name__)
USERNAME = getpass.getuser()


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
    if len(sys.argv) > 1:
        argument = sys.argv[1]
    else:
        argument = 'config.yml'
    return argument


def checkFile(path):
    if os.path.exists(path):
        pathExist = True
    else:
        pathExist = False

    return pathExist


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
    while cont:
        listo_lectura, _, _ = select.select([sock], [], [], 2)

        if listo_lectura:
            conexion, direccion = sock.accept()
            LOGGER.info('Monitoring port: %s - Address: %s - Request from: %s', port, addr, direccion,
                        extra={'username': USERNAME})
            conexion.close()
            sock.close()
            cont = False
            signal = 1

    return signal


def serviceCommand(process, toggle):
    execProcess = subprocess.Popen([SUDO, SERVICE, process, toggle], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    err, stdo = execProcess.communicate()
    if execProcess.returncode == 0:
        LOGGER.info('Service: %s - Accion: % ', process, toggle, extra={'username': USERNAME})
    else:
        messageError = err.decode().strip() if err else "UKNOWM ERROR"
        LOGGER.error(messageError, extra={'username': USERNAME})


def processVerification(processName):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == processName:
            return True
    return False


def check_iptables_rule(rule):
    check = False
    command = f"sudo iptables -C {rule}"
    result = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        check = True
    return check


def checkTime(addr, ports, timeout):
    cheak = False
    nextPort = 0
    initTime = time.time()
    finaltime = initTime + timeout
    for port in ports:
        if knockPort(addr, port) == 1 and time.time() < finaltime:
            nextPort = nextPort + 1
        else:
            break
    if nextPort == len(ports):
        cheak = True
    return cheak


def listenKey(configFile):
    addr = configFile[0]
    ports = configFile[1]
    timeout = configFile[2]
    ordenType = configFile[3]
    orden = configFile[4]

    while True:
        if checkTime(addr, ports, timeout):
            if ordenType == "service":
                if processVerification(orden[0]):
                    serviceCommand(orden[0], orden[2])
                else:
                    serviceCommand(orden[0], orden[1])
            if ordenType == "iptables":
                rule = str(orden[0]) + " -p " + str(orden[1]) + " --dport " + str(orden[2]) + " -j " + str(orden[3])
                if check_iptables_rule(rule):
                    os.system(SUDO + " iptables " + " -D " + rule)
                    LOGGER.info('IPTABLE rule DELETE: %s', rule, extra={'username': USERNAME})
                else:
                    os.system(SUDO + " iptables " + " -A " + rule)
                    LOGGER.info('IPTABLE rule ADD: %s', rule, extra={'username': USERNAME})
            if ordenType == "command":
                os.system(orden[0] + " &")
                LOGGER.info('Command: %s', orden[0], extra={'username': USERNAME})


def checkPathLog():
    pathlog = '/var/log/knockport/knockport.log'
    if not os.path.exists(pathlog):
        with open(pathlog, 'w'):
            pass
    return pathlog


def setup_Logs():
    pathLog = checkPathLog()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(pathLog)
    format_str = '%(asctime)s %(username)s %(levelname)s: %(message)s'
    formatter = logging.Formatter(format_str)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def stopScript(signal, frame):
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, stopScript)
    while True:
        try:
            setup_Logs()
            if checkFile(getArgument()):
                config = getConfig(getArgument())
                listenKey(config)
            else:
                LOGGER.error("NO PRIVIGELES OR CONFIGURE FILE NOT EXIST", extra={'username': USERNAME})
                break
        except KeyboardInterrupt:
            stopScript(None, None)

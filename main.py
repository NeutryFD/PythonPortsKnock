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


STERMINAL = "sudo"
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
            LOGGER.info('Monitoring port: %s - Address: %s - Request from: %s', port, addr, direccion, extra={'username': USERNAME})
            conexion.close()
            sock.close()
            cont = False
            signal = 1

    return signal


def serviceCommand(process, toggle):
    execProcess = subprocess.Popen([STERMINAL, SERVICE, process, toggle], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
    exit_code = os.system(command)
    if exit_code == 0:
        check = True
    return check


def cheakTime(addr, ports, timeout):
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
        if cheakTime(addr, ports, timeout):
            if ordenType == "service":
                if processVerification(orden[0]):
                    serviceCommand(orden[0], orden[2])
                else:
                    serviceCommand(orden[0], orden[1])
            if ordenType == "iptables":
                rule = str(orden[0]) + " -p " + str(orden[1]) + " --dport " + str(orden[2]) + " -j " + str(orden[3])
                LOGGER.info('IPTABLE rule: %s', rule)
                if check_iptables_rule(rule):
                    os.system(STERMINAL + " iptables " + " -D " + rule)
                else:
                    os.system(STERMINAL + " iptables " + " -A " + rule)
            if ordenType == "command":
                os.system(orden[0] + " &")
                LOGGER.info('Command: %s', orden[0], extra={'username': USERNAME})


def setup_Logs():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('logging.log')
    format_str = '%(asctime)s %(username)s %(levelname)s: %(message)s'
    formatter = logging.Formatter(format_str)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


if __name__ == "__main__":
    setup_Logs()
    config = getConfig(getArgument())
    listenKey(config)

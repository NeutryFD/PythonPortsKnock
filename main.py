import select
import socket
import time
import yaml
import psutil
import subprocess

def getConfig():
    with open('config.yml') as f:
        config = yaml.safe_load(f)

    host = config['host']
    timeout = config['timeout']
    ports = config['ports']
    process = config['process']

    config = [host, ports, timeout,process]
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

def vsftpinit(process, toggle):
    vsftp = subprocess.Popen(["sudo", "service", process, toggle], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err, stdo = vsftp.communicate()
    if vsftp.returncode == 0:
        print("Done")
    else:
        print(err.decode())


def verificar_vsftpd_en_ejecucion():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'vsftpd':
            return True

    return False

def listenKey(config):
    addr = config[0]
    ports = config[1]
    timeout = config[2]
    processName = config[3]
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
            if verificar_vsftpd_en_ejecucion():
                vsftpinit(processName, "stop")
            else:
                vsftpinit(processName, "start")


if __name__ == "__main__":
    config = getConfig()
    listenKey(config)
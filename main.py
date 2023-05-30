import select
import socket
import subprocess
import time
import yaml
import threading

TERMINATE = threading.Event()
thread_runScript = None
def getConfig():
    with open('config.yml') as f:
        config = yaml.safe_load(f)

    host = config['host']
    timeout = config['timeout']
    ports = config['ports']

    config = [host, ports, timeout]
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


def runScript():
    while not TERMINATE.is_set():
        path = "/home/neutry/Desktop/GG"
        result = subprocess.run(["bash", path], capture_output=True)
        if result.returncode == 0:
            print(result.stdout.decode())
        else:
            print("error")


def listenKey(config):
    addr = config[0]
    ports = config[1]
    timeout = config[2]

    is_running = False
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
            if is_running and thread_runScript is not None and thread_runScript.is_alive():
                TERMINATE.set()
                thread_runScript.join()
                TERMINATE.clear()

            if not is_running:
                TERMINATE.clear()
                thread_runScript = threading.Thread(target=runScript)
                thread_runScript.start()
                is_running = True


if __name__ == "__main__":
    config = getConfig()
    listenKey(config)
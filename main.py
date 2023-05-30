import select
import socket
import subprocess
import glob
import time


def knockPort(port):
    signal = 0
    cont = True
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.setblocking(0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('0.0.0.0', port))
    except socket.error as e:
        print(e)
    sock.listen(1)
    print("Monitoring port: ", port)

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
    path = "/home/neutry/Desktop/GG"

    result = subprocess.run(["bash", path], capture_output=True)

    if result.returncode == 0:
        print(result.stdout.decode())
    else:
        print("error")

def listenKey():
    while True:
        if knockPort(2525) == 1:
            initTime = time.time()
            finalTime = initTime + 10
            if knockPort(4040) == 1 and time.time() < finalTime:
                if knockPort(2325) == 1 and time.time() < finalTime:
                    runScript()

if __name__ == "__main__":
    listenKey()
import os
import pty
import time
import fcntl

pid, fd = pty.fork()
if pid == 0:
    os.execlp("bash", "bash")
else:
    time.sleep(1)
    os.write(fd, b"echo hello\r")
    time.sleep(1)
    
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    try:
        data = os.read(fd, 1024)
        print("Data:", data)
    except Exception as e:
        print("Error:", e)

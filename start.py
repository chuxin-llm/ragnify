

import os, sys
import time

sys.path.append(os.getcwd())
log_dir = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(log_dir): os.mkdir(log_dir)

import subprocess
from rag.common.utils import settings
from rag.common.utils import logger


SUCCESS_FLAG = "Application startup complete"
ERROR_FLAG = "Fail to start application"


def main():
    ########################################################
    # 启动Api Server
    ########################################################
    cmd = ["python", "server/main.py", "--create_tables"]
    t1 = time.time()
    p_load_api_server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while p_load_api_server.poll() is None:
        line = p_load_api_server.stdout.readline().decode('utf-8')
        if SUCCESS_FLAG in line:
            logger.info(f"Starting Api Server cost {time.time() - t1} seconds")
            break
        elif ERROR_FLAG in line:
            raise RuntimeError("Fail to start Api Server")

    # ########################################################
    # # 启动WebUI
    # ########################################################
    cmd = ["streamlit", "run",
           "server/web_app.py",
           "--server.port", str(settings.server.web_server_port)]

    subprocess.run(cmd)


if __name__ == "__main__":

    main()






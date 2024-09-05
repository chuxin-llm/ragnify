
import os, sys
sys.path.append(os.getcwd())
import argparse

log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

from server.api import run_api
from rag.common.utils import logger
from rag.common.configuration import settings
from rag.connector.database.base import create_tables


def get_parser():
    parser = argparse.ArgumentParser(prog='RAG-API-Server',
                                     description='')
    parser.add_argument("--host", type=str, default=settings.server.api_server_host)
    parser.add_argument("--port", type=int, default=settings.server.api_server_port)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    parser.add_argument("--create_tables", action='store_true', default=False)
    return parser.parse_args()


def main():
    args = get_parser()

    if args.create_tables:
        create_tables()

    logger.info("=========================Starting Service=========================")

    try:
        run_api(host=args.host,
                port=args.port,
                ssl_keyfile=args.ssl_keyfile,
                ssl_certfile=args.ssl_certfile)
    except Exception as e:
        logger.error("Api Server 启动失败：", e)
        sys.stderr.write("Fail to start application")


if __name__ == "__main__":
    main()



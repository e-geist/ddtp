import logging

from dotenv import load_dotenv, find_dotenv


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
load_dotenv(find_dotenv())

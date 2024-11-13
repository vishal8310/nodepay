import os
import time
import requests
import multiprocessing
from termcolor import colored
import pyfiglet
import inquirer
from datetime import datetime

def read_lines(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

class Config:
    def __init__(self):
        self.base_url = 'https://nodepay.org'
        self.ping_url = 'http://54.255.192.166/api/network/ping'
        self.retry_interval = 30
        self.session_url = 'http://18.136.143.169/api/auth/session'

class Logger:
    @staticmethod
    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def info(message, data=None):
        timestamp = Logger.get_timestamp()
        info_message = f"[{timestamp}] [INFO] {message}: {data}" if data else f"[{timestamp}] [INFO] {message}"
        print(colored(info_message, 'green'))

    @staticmethod
    def success(message, token):
        timestamp = Logger.get_timestamp()
        # Updated success message in English without token details and no emojis
        print(colored(f"[{timestamp}] Ping sent successfully to the server!", 'green'))
        print(colored(f"[{timestamp}] Ping was sent successfully and executed smoothly.", 'cyan'))

    @staticmethod
    def error(message, data=None):
        timestamp = Logger.get_timestamp()
        error_message = f"[{timestamp}] [ERROR] {message}: {data}" if data else f"[{timestamp}] [ERROR] {message}"
        print(colored(error_message, 'red'))

class Bot:
    def __init__(self, config, logger, proxy=None):
        self.config = config
        self.logger = logger
        self.proxy = proxy

    def connect(self, token):
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
            account_info = self.get_session(token, user_agent)
            self.logger.info("Connected to session successfully", {'status': 'success'})

            while True:
                try:
                    self.send_ping(account_info, token, user_agent)
                except Exception as error:
                    self.logger.error("Ping error", str(error))
                time.sleep(self.config.retry_interval)
        except Exception as error:
            self.logger.error("Connection error", str(error))

    def get_session(self, token, user_agent):
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }
        response = requests.post(self.config.session_url, headers=headers, proxies=self.proxy) if self.proxy else requests.post(self.config.session_url, headers=headers)
        return response.json()['data']

    def send_ping(self, account_info, token, user_agent):
        ping_data = {
            'id': account_info.get('uid', 'Unknown'),
            'browser_id': account_info.get('browser_id', 'random_browser_id'),
            'timestamp': int(time.time()),
            'version': '2.2.7'
        }
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }
        response = requests.post(self.config.ping_url, json=ping_data, headers=headers, proxies=self.proxy) if self.proxy else requests.post(self.config.ping_url, json=ping_data, headers=headers)
        if response.status_code == 200:
            self.logger.success("Ping sent", token)

def display_welcome():
    ascii_art = pyfiglet.figlet_format("Nodepay Bot")
    print(colored(ascii_art, 'yellow'))
    print(colored("========================================", 'cyan'))
    print(colored("=        Welcome to MiweAirdrop        =", 'cyan'))
    print(colored("=       Automated & Powerful Bot       =", 'cyan'))
    print(colored("========================================", 'cyan'))

def ask_proxy_mode():
    questions = [
        inquirer.List('proxy_mode',
                      message="Do you want to use a proxy?",
                      choices=['No Proxy', 'Use Proxy'],
                      default='No Proxy',
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer['proxy_mode']

def configure_proxy(proxy_line):
    proxy = proxy_line.split(':')
    if len(proxy) == 4:
        host, port, username, password = proxy
        return {
            'http': f'http://{username}:{password}@{host}:{port}',
            'https': f'http://{username}:{password}@{host}:{port}'
        }
    return None

def run_bot_for_token(token, config, logger, proxy=None):
    bot = Bot(config, logger, proxy)
    bot.connect(token)

def main():
    display_welcome()

    # Check if token file exists and is not empty
    if not os.path.exists('token.txt') or os.stat('token.txt').st_size == 0:
        print(colored("[ERROR] Token file not found or is empty!", 'red'))
        return

    tokens = read_lines('token.txt')
    config = Config()
    logger = Logger()

    proxy_mode = ask_proxy_mode()

    proxies = read_lines('proxy.txt') if proxy_mode == 'Use Proxy' else []
    processes = []

    for i, token in enumerate(tokens):
        proxy = configure_proxy(proxies[i % len(proxies)]) if proxies else None
        if proxy:
            logger.info(f"Using proxy for token {i + 1}", proxy)

        process = multiprocessing.Process(target=run_bot_for_token, args=(token, config, logger, proxy))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

if __name__ == '__main__':
    main()

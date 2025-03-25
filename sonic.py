import time
import requests
from web3 import Web3
import random

# Настройки для сети Sonic
chain_id = 146
rpc_url = "https://rpc.soniclabs.com"  # Замените на актуальный RPC URL
web3 = Web3(Web3.HTTPProvider(rpc_url))

PENDLE_API_URL = "https://api-v2.pendle.finance/core/v1/sdk"  # URL API Pendle

# Настройки софта
WALLET_FILE = 'privatekeys.txt'
AMOUNT_IN_S = 1  # Количество SONIC для свапа
SLIPPAGE = 0.01  # Макс. допустимый slippage (1% = 0.01)
GAS_LIMIT = 1500000  # Лимит газа
MAX_FEE_PER_GAS = 110  # Макс. плата за газ (в Gwei)
MAX_PRIORITY_FEE_PER_GAS = 0.000000001  # Приоритетная плата за газ (в Gwei)

# Таймер между аккаунтами (в секундах)
MIN_DELAY = 30
MAX_DELAY = 60

def get_transaction_data(chain_id, market, receiver, slippage, token_in, token_out, amount_in):
    """Получает данные транзакции из API Pendle."""
    url = f"{PENDLE_API_URL}/{chain_id}/markets/{market}/swap"
    params = {
        "receiver": receiver,
        "slippage": slippage,
        "enableAggregator": True,
        "tokenIn": token_in,
        "tokenOut": token_out,
        "amountIn": Web3.to_wei(amount_in, 'ether')
    }
    try:
        response = requests.get(url, params=params, verify=False)
        response.raise_for_status()  # Проверяет, что статус код 200
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None  # Важно возвращать None при ошибке, чтобы скрипт не сломался

def send_transaction(private_key, tx_data):
    """Отправляет транзакцию в сеть."""
    account = web3.eth.account.from_key(private_key)
    address = account.address
    nonce = web3.eth.get_transaction_count(address)

    transaction = {
        "chainId": chain_id,
        "from": address,
        "to": tx_data["tx"]["to"],
        "value": int(tx_data["tx"]["value"]),
        "gas": GAS_LIMIT,
        "maxFeePerGas": int(Web3.to_wei(MAX_FEE_PER_GAS, 'gwei')),
        "maxPriorityFeePerGas": int(Web3.to_wei(MAX_PRIORITY_FEE_PER_GAS, 'gwei')),
        "nonce": nonce,
        "data": tx_data["tx"]["data"]
    }

    try:
        signed_tx = web3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Address: {address} | Transaction sent with hash: {web3.to_hex(tx_hash)}")
    except Exception as e:
        print(f"Error sending transaction from {address}: {str(e)}")

# Пример параметров для API Pendle. ОБЯЗАТЕЛЬНО ПРОВЕРЬТЕ АДРЕСА ДЛЯ СЕТИ Sonic.
market = "0x3f5ea53d1160177445b1898afbb16da111182418"  
token_in = "0x0000000000000000000000000000000000000000"  
token_out = "0x18d2d54f42ba720851bae861b98a0f4b079e6027"

# Чтение приватных ключей
with open(WALLET_FILE, "r") as wallet_file:
    private_keys = [line.strip() for line in wallet_file.readlines()]

for pk in private_keys:
    try:
        account = web3.eth.account.from_key(pk)
        receiver = account.address
        tx_data = get_transaction_data(chain_id, market, receiver, SLIPPAGE, token_in, token_out, AMOUNT_IN_S)

        if tx_data:  # Проверяем, что tx_data не None
            send_transaction(pk, tx_data)
        else:
            print(f"Skipping wallet due to error fetching transaction data.")

        # Добавляем случайную задержку между транзакциями
        delay = random.randint(MIN_DELAY, MAX_DELAY)
        print(f"Waiting {delay} seconds before next transaction...")
        time.sleep(delay)

    except Exception as e:
        print(f"Error processing wallet: {str(e)}")

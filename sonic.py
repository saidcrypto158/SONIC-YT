import time
import requests
from web3 import Web3
import random
from datetime import datetime
import certifi

# Настройки для сети Sonic
chain_id = 146
rpc_url = "https://rpc.soniclabs.com"  # Замените на актуальный RPC URL
web3 = Web3(Web3.HTTPProvider(rpc_url))

PENDLE_API_URL = "https://api-v2.pendle.finance/core/v1/sdk"  # URL API Pendle

# Настройки софта
WALLET_FILE = 'privatekeys.txt'
SLIPPAGE = 0.01  # Макс. допустимый slippage (1% = 0.01)
GAS_LIMIT = 1500000  # Лимит газа
MAX_FEE_PER_GAS = 110  # Макс. плата за газ (в Gwei)
MAX_PRIORITY_FEE_PER_GAS = 0.000000001  # Приоритетная плата за газ (в Gwei)

# Таймер между аккаунтами (в секундах)
MIN_DELAY = 1300
MAX_DELAY = 1700

# Диапазон для случайного количества SONIC
MIN_AMOUNT_IN_S = 1.7
MAX_AMOUNT_IN_S = 1.85

def log_message(message):
    """Выводит сообщение с текущей временной меткой."""
    current_time = datetime.now().strftime("[%H:%M:%S]")
    print(f"{current_time} {message}")

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
        response = requests.get(url, params=params, verify=certifi.where())
        response.raise_for_status()  # Проверяет, что статус код 200
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message(f"Ошибка при запросе к API: {e}")
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
        log_message(f"Адрес: {address} | Транзакция отправлена с хэшем: {web3.to_hex(tx_hash)}")
    except Exception as e:
        log_message(f"Ошибка при отправке транзакции с адреса {address}: {str(e)}")

# Пример параметров для API Pendle. ОБЯЗАТЕЛЬНО ПРОВЕРЬТЕ АДРЕСА ДЛЯ СЕТИ Sonic.
market = "0x3f5ea53d1160177445b1898afbb16da111182418"
token_in = "0x0000000000000000000000000000000000000000"
token_out = "0x18d2d54f42ba720851bae861b98a0f4b079e6027"

# Чтение приватных ключей
with open(WALLET_FILE, "r") as wallet_file:
    private_keys = [line.strip() for line in wallet_file.readlines()]

# Перемешивание списка приватных ключей
random.shuffle(private_keys)

# Определение общего количества аккаунтов
total_accounts = len(private_keys)

# Обработка каждого аккаунта
for index, pk in enumerate(private_keys, start=1):
    try:
        log_message(f"Обработка аккаунта [{index}/{total_accounts}]")

        account = web3.eth.account.from_key(pk)
        receiver = account.address

        # Генерация случайного количества SONIC для свапа
        amount_in_s = random.uniform(MIN_AMOUNT_IN_S, MAX_AMOUNT_IN_S)
        log_message(f"Выбрано случайное количество для свапа: {amount_in_s:.2f} SONIC")

        tx_data = get_transaction_data(chain_id, market, receiver, SLIPPAGE, token_in, token_out, amount_in_s)

        if tx_data:  # Проверяем, что tx_data не None
            send_transaction(pk, tx_data)
        else:
            log_message("Пропуск кошелька из-за ошибки при получении данных транзакции.")

        # Добавляем случайную задержку между транзакциями
        delay = random.randint(MIN_DELAY, MAX_DELAY)
        log_message(f"Ожидание {delay} секунд перед следующей транзакцией...")
        time.sleep(delay)

    except Exception as e:
        log_message(f"Ошибка при обработке кошелька: {str(e)}")

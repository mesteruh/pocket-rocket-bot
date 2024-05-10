## Functionality
| Functional                                                     | Supported |
|----------------------------------------------------------------|:---------:|
| Multithreading                                                 |     ✅     |
| Binding a proxy to a session                                   |     ✅     |

## [Settings](https://github.com/shamhi/TapSwapBot/blob/main/.env-example)
| Setup                   | Description                                                                |
|-------------------------|----------------------------------------------------------------------------|
| **API_ID / API_HASH**   | Platform data from which to launch a Telegram session (stock - Android)    | |
| **USE_PROXY_FROM_FILE** | Whether to use proxy from the `bot/config/proxies.txt` file (True / False) |

## Installation
You can download [**Repository**](https://github.com/shamhi/TapSwapBot) by cloning it to your system and installing the necessary dependencies:
```shell
#Linux
~/blum >>> python3 -m venv venv
~/blum >>> source venv/bin/activate
~/blum >>> pip3 install -r requirements.txt
~/blum >>> cp .env-example .env
~/blum >>> nano .env # Here you must specify your API_ID and API_HASH , the rest is taken by default
~/blum >>> python3 main.py

#Windows
~/blum >>> python -m venv venv
~/blum >>> source venv/Scripts/activate
~/blum >>> pip install -r requirements.txt
~/blum >>> copy .env-example .env
~/blum >>> # Specify your API_ID and API_HASH, the rest is taken by default
~/blum >>> python main.py
```

Also for quick launch you can use arguments, for example:
```shell
~/blum >>> python main.py --action (1/2/3)
# Or
~/blum >>> python main.py -a (1/2/3)

#1 - Create session
#2 - Run clicker
#3 - Run via Telegram
```

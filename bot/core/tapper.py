import asyncio
from time import time
from random import randint
from urllib.parse import unquote

import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestWebView

from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=await self.tg_client.resolve_peer('pocket_rocket_game_bot'),
                bot=await self.tg_client.resolve_peer('pocket_rocket_game_bot'),
                platform='android',
                from_bot_menu=False,
                url='https://rocket.whitechain.io'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(
                    string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str) -> tuple[str, str]:
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/login',
                                              json={"init_data": tg_web_data})
            response.raise_for_status()
            response_json = await response.json()
            balance = response_json['user']['current_points']
            logger.success(f"{self.session_name} | Success login | balance {balance}")

            token = response_json['token']
            refresh_token = response_json['refresh_token']
            refresh_token_expires_at = response_json['refresh_token_expires_at']

            http_client.headers["Authorization"] = f"Bearer {token}"
            headers["Authorization"] = f"Bearer {token}"

            return refresh_token, refresh_token_expires_at
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)

    async def get_user(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(
                url='https://api-game.whitechain.io/api/user')
            response.raise_for_status()
            response_json = await response.json()

            return response_json['user']

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting user info: {error}")
            await asyncio.sleep(delay=3)

    async def send_taps(self, http_client: aiohttp.ClientSession, points: int):
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/claim-points',
                                              json={'points': points})
            response.raise_for_status()

            logger.success(f"{self.session_name} | Successful tapped +{points}")
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while claim points: {error}")
            await asyncio.sleep(delay=3)

    async def apply_turbo(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(
                url='https://api-game.whitechain.io/api/apply-boost/fc5e40ed-c40b-4cfa-9a1a-9a16a5572d84')
            response.raise_for_status()

            logger.success(f"{self.session_name} | Successful apply turbo")
            await asyncio.sleep(delay=5)
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while apply turbo: {error}")
            await asyncio.sleep(delay=3)

    async def level_up_reactor(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(
                url='https://api-game.whitechain.io/api/upgrade-ship/b389de1f-a262-4625-be63-ee2d7f0c3345')
            response.raise_for_status()

            logger.success(f"{self.session_name} | Successful level up reactor")
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while level up reactor: {error}")
            await asyncio.sleep(delay=3)

    async def recovery_energy(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(
                url='https://api-game.whitechain.io/api/apply-boost/d212b229-3fb7-4900-a275-5ae0417e0164')
            response.raise_for_status()

            logger.success(f"{self.session_name} | Successful apply recovery energy")
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while recovery energy: {error}")
            await asyncio.sleep(delay=3)

    async def refresh_token(self, http_client: aiohttp.ClientSession, token: str):
        try:
            response = await http_client.post(
                url='https://api-game.whitechain.io/api/refresh-token', json={'refresh_token': token})
            response.raise_for_status()

            logger.success(f"{self.session_name} | Token successful refreshed")
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while refreshing token: {error}")
            await asyncio.sleep(delay=3)

    async def get_boosts_status(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(
                url='https://api-game.whitechain.io/api/user-boosts-status')
            response.raise_for_status()

            response_json = await response.json()
            turbo, energy = response_json['data']
            has_turbo_boost = turbo['charges_left'] > 0
            has_energy_boost = energy['charges_left'] > 0

            if has_turbo_boost:
                logger.success(f"{self.session_name} | has {turbo['charges_left']} available turbo")
            else:
                logger.warning(f"{self.session_name} | no turbo boosts available")

            if has_energy_boost:
                logger.success(f"{self.session_name} | has {energy['charges_left']} available energy boosts")
            else:
                logger.warning(f"{self.session_name} | no energy boosts available")

            return has_turbo_boost, has_energy_boost

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting boosts status: {error}")
            await asyncio.sleep(delay=3)

    async def update_current_energy(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(
                url='https://api-game.whitechain.io/api/update-current-energy')
            response.raise_for_status()
            response_json = await response.json()

            logger.success(f"{self.session_name} | Successful update current energy")
            return response_json['user']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while update current energy: {error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        refresh_token = ''
        token_expired_time = 0
        refresh_token_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            while True:
                try:
                    if time() >= token_expired_time - 300:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        token, refresh_token_expires_at = await self.login(http_client=http_client,
                                                                           tg_web_data=tg_web_data)
                        refresh_token = token
                        token_expired_time = refresh_token_expires_at
                        refresh_token_time = time()

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    if time() - refresh_token_time > 275:
                        await self.refresh_token(http_client=http_client, token=refresh_token)

                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])
                    data = await self.update_current_energy(http_client=http_client)
                    current_energy = data['current_energy']

                    if current_energy > settings.MIN_AVAILABLE_ENERGY:
                        min, max = settings.RANDOM_TAPS_COUNT
                        max_value = max if current_energy >= max else current_energy

                        points = randint(a=min, b=max_value)
                        await self.send_taps(http_client=http_client, points=points)
                        resp = await self.update_current_energy(http_client=http_client)
                        logger.info(f"{self.session_name} | Balance {resp['current_points']}")

                    # has_turbo_boost, has_energy_boost = await self.get_boosts_status(http_client=http_client)
                    # if has_turbo_boost:
                    #     await self.apply_turbo(http_client=http_client)
                    #     await self.update_current_energy(http_client=http_client)
                    #
                    # if has_energy_boost:
                    #     await self.recovery_energy(http_client=http_client)
                    #     await self.update_current_energy(http_client=http_client)
                    #     await asyncio.sleep(delay=1)

                    if current_energy < settings.MIN_AVAILABLE_ENERGY:
                        logger.info(f"{self.session_name} | Minimum energy reached: {current_energy}")
                        logger.info(f"{self.session_name} | Sleep {settings.SLEEP_BY_MIN_ENERGY}s")

                        await asyncio.sleep(delay=settings.SLEEP_BY_MIN_ENERGY)
                        continue

                    logger.info(f"Sleep {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")

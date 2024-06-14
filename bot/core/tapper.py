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

yellow = "\x1b[33;20m"
green = "\x1b[1;32m"
blue = "\x1b[1;36m"
reset = "\x1b[0m"


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
            user = response_json['user']
            balance = user['current_points']
            total_claimed_points = user['total_claimed_points']

            logger.success(f"{self.session_name} "
                           f"| Success login "
                           f"| Balance: {blue}{balance}{reset} "
                           f"| Total claimed points: {blue}{total_claimed_points}{blue}")

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
            response_json = await response.json()
            current_energy = response_json['user']['current_energy']
            balance = response_json['user']['current_points']

            logger.success(f"{self.session_name} "
                           f"| Successful tapped "
                           f"| Balance: {blue}{balance}{reset} ({green}+{points}{reset}) "
                           f"| Energy: {blue}{current_energy}{reset}")
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while claim points: {error}")
            await asyncio.sleep(delay=3)

    async def apply_turbo(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(
                url='https://api-game.whitechain.io/api/apply-boost/fc5e40ed-c40b-4cfa-9a1a-9a16a5572d84')
            response.raise_for_status()

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

            logger.success(f"{self.session_name} | Successful apply {green}recovery energy{reset}")
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while recovery energy: {error}")
            await asyncio.sleep(delay=3)

    async def refresh_token(self, http_client: aiohttp.ClientSession, token: str):
        try:
            response = await http_client.post(
                url='https://api-game.whitechain.io/api/refresh-token', json={'refresh_token': token})
            response.raise_for_status()
            response_json = await response.json()
            token = response_json['token']

            http_client.headers["Authorization"] = f"Bearer {token}"
            headers["Authorization"] = f"Bearer {token}"
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while refreshing token: {error}")
            await asyncio.sleep(delay=3)

    async def get_turbo_status(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(
                url='https://api-game.whitechain.io/api/user-boosts-status')
            response.raise_for_status()

            response_json = await response.json()
            turbo = response_json['data'][0]
            has_turbo_boost = turbo['charges_left'] > 0
            turbo_charges_left = turbo['charges_left']
            turbo_next_available_at = turbo['next_available_at'] if turbo['next_available_at'] is not None else time() + 7200

            if has_turbo_boost:
                logger.success(f"{self.session_name} "
                               f"| Has {green}{turbo['charges_left']}{reset} available {green}turbo{reset}")
            else:
                logger.warning(
                    f"{self.session_name} "
                    f"| {yellow}No turbo{reset} boosts available. "
                    f"| Left {yellow}{round((turbo_next_available_at - time()) / 60)} min{reset}.")

            return has_turbo_boost, turbo_charges_left, turbo_next_available_at

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting boosts status: {error}")
            await asyncio.sleep(delay=3)

    async def get_energy_status(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-game.whitechain.io/api/user-boosts-status')
            response.raise_for_status()

            response_json = await response.json()
            energy = response_json['data'][1]
            has_energy_boost = energy['charges_left'] > 0
            energy_next_available_at = (
                energy['next_available_at'] if energy['next_available_at'] is not None else time() + 7200)

            if has_energy_boost:
                logger.success(f"{self.session_name} "
                               f"| Has {green}{energy['charges_left']}{reset} available {green}energy{reset} boosts")
            else:
                logger.warning(f"{self.session_name} "
                               f"| {yellow}No energy{reset} boosts available. "
                               f"| Left {yellow}{round((energy_next_available_at - time()) / 60)} min{reset}.")

            return has_energy_boost, energy_next_available_at

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting boosts status: {error}")
            await asyncio.sleep(delay=3)

    async def update_current_energy(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/update-current-energy')
            response.raise_for_status()
            response_json = await response.json()
            return response_json['user']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while update current energy: {error}")
            await asyncio.sleep(delay=3)

    async def get_ship_improvements(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://api-game.whitechain.io/api/user-current-improvements')
            response.raise_for_status()
            response_json = await response.json()

            logger.error(f"{self.session_name} | get_ship_improvements {response_json}")

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting ship improvements: {error}")
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
        revalidate_turbo_time = 0
        revalidate_ship_improvements_time = 0
        revalidate_energy_boost_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)
                await asyncio.sleep(delay=1)

            while True:
                try:
                    if time() >= token_expired_time - 300:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        await asyncio.sleep(delay=1)
                        token, refresh_token_expires_at = await self.login(http_client=http_client,
                                                                           tg_web_data=tg_web_data)
                        refresh_token = token
                        token_expired_time = refresh_token_expires_at
                        refresh_token_time = time()
                        await asyncio.sleep(delay=1)
                        await self.refresh_token(http_client=http_client, token=refresh_token)
                        await asyncio.sleep(delay=1)

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    try:
                        if time() - refresh_token_time > 250:
                            await self.refresh_token(http_client=http_client, token=refresh_token)

                        sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])
                        data = await self.update_current_energy(http_client=http_client)
                        current_energy = data['current_energy']

                        if current_energy > settings.MIN_AVAILABLE_ENERGY:
                            min_value, max_value = settings.RANDOM_TAPS_COUNT
                            points = randint(a=min_value, b=max_value)
                            await self.send_taps(http_client=http_client, points=points)
                            await asyncio.sleep(delay=1)
                            await self.update_current_energy(http_client=http_client)
                    except Exception as error:
                        logger.error(f"{self.session_name} | Unknown error {error}")
                        continue

                    # if time() > revalidate_ship_improvements_time:
                    #     try:
                    #         await self.get_ship_improvements(http_client=http_client)
                    #
                    #     except Exception as error:
                    #         logger.error(f"{self.session_name} | Error while getting ship improvements: {error}")
                    #
                    #     finally:
                    #         revalidate_ship_improvements_time = time() + 60
                    #         logger.info(f"{self.session_name} "
                    #                     f"| Set {yellow}revalidate ship improvements{reset} time to "
                    #                     f"{yellow}{round((time() + 60) / 60)} min{yellow}.")

                    if time() > revalidate_turbo_time:
                        try:
                            has_turbo_boost, turbo_charges_left, turbo_next_available_at = await self.get_turbo_status(
                                http_client=http_client)

                            if has_turbo_boost:
                                for x in range(turbo_charges_left):
                                    await self.apply_turbo(http_client=http_client)
                                    await asyncio.sleep(delay=2)
                                    resp = await self.update_current_energy(http_client=http_client)
                                    logger.success(f"{self.session_name} "
                                                   f"| Successful apply {green}turbo ({1 + x}/{turbo_charges_left}){reset} "
                                                   f"| Balance: {blue}{resp['current_points']}{reset} "
                                                   f"| Sleep {sleep_between_clicks}s.")
                                    await asyncio.sleep(delay=sleep_between_clicks)

                        except Exception as error:
                            logger.error(f"{self.session_name} | Error while applying turbo boost: {error}")

                        finally:
                            revalidate_turbo_time = turbo_next_available_at
                            logger.info(f"{self.session_name} "
                                        f"| Set {yellow}revalidate turbo{reset} time to "
                                        f"{yellow}{round((turbo_next_available_at - time()) / 60)} min{yellow}.")

                    if current_energy < settings.MIN_AVAILABLE_ENERGY:
                        if time() > revalidate_energy_boost_time:
                            try:
                                has_energy_boost, energy_next_available_at = await self.get_energy_status(
                                    http_client=http_client)

                                if has_energy_boost:
                                    await self.recovery_energy(http_client=http_client)
                                    await self.update_current_energy(http_client=http_client)
                                else:
                                    revalidate_energy_boost_time = energy_next_available_at
                                    logger.info(f"{self.session_name} "
                                                f"| Set {yellow}revalidate energy{reset} boost time to "
                                                f"{yellow}{round((energy_next_available_at - time()) / 60)} min{reset}.")
                                    continue

                            except Exception as error:
                                logger.error(f"{self.session_name} | Error while applying energy boost: {error}")

                        else:
                            logger.info(f"{self.session_name} | Minimum energy reached: {current_energy}")
                            logger.info(f"{self.session_name} | Sleep {settings.SLEEP_BY_MIN_ENERGY}s")

                            await asyncio.sleep(delay=settings.SLEEP_BY_MIN_ENERGY)
                            continue

                    logger.info(f"{self.session_name} | Sleep {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")

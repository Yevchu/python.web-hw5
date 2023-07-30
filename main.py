import asyncio
import aiohttp
import aiofile
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
url = f'https://api.privatbank.ua/p24api/exchange_rates?json'
curency_list = ['USD', 'EUR']
dates_list = []

async def log_exchange_command():
    async with aiofile.async_open("exchange_log.txt", mode="a") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"exchange command executed at {timestamp}\n"
        await file.write(log_message)

def unpack_ccry(ccry_dict):
    res = ''
    for key, value in ccry_dict.items():
        res += f'Date: {key},'
        for key_el, val_el in value.items():
            for el in val_el:
                res += f' currency: {key_el} - {el} '
    return res

def parse_args(args):
    try:
        _ = int(args[0])
        for currency in args[1:]:
            curency_list.append(currency)
        return args[0]
    except:
        for currency in args:
            curency_list.append(currency)
        return '0'

def generate_dates(num_days):

    end_date = datetime.now()
    start_date = end_date - timedelta(days=num_days)
    date_range = [start_date + timedelta(days=i) for i in range(num_days + 1)]
    return date_range

async def fetch_currency(session, url):

    async with session.get(url) as response:
        return await response.json()

async def get_exchange(dates):

    async with aiohttp.ClientSession() as session:
        responses = await asyncio.gather(*[fetch_currency(session, f"{url}&date={date}")for date in dates])

    result = {}
    our_curr_dict = {}

    for response in responses:
        if response.get('date') in dates:
            exchange_rate = response.get('exchangeRate')
            for currency in exchange_rate:
                if currency.get('currency') in curency_list:
                    our_curr_dict.update({currency.get('currency'): {f"sale: {float(currency.get('saleRateNB'))}, purchase: {float(currency.get('purchaseRateNB'))}"}})
            result.update({response.get('date'): our_curr_dict})
    return result

async def ccry(date_delta):
    async with aiohttp.ClientSession() as session:
        try:
            date_delta = int(date_delta)
            if date_delta > 10:
                print("Too much days, max is 10days")
            else:
                dates = generate_dates(date_delta)
                for date in dates:
                    dates_list.append(date.strftime("%d.%m.%Y"))

                try:
                    res = await get_exchange(dates_list)
                    return res
                except (aiohttp.ClientError, ValueError) as e:
                    # Обробка помилок мережевих запитів та обробки JSON
                    print(f"Error while fetching data: {e}")
            return
        except ValueError as e:
            return f'Please give me a number! Error:{e}'

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.lower() == 'exchange':
                await log_exchange_command()
                res = unpack_ccry(await ccry(date_delta=0))
                await self.send_to_clients(res)
            await self.send_to_clients(f"{ws.name}: {message}")

async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
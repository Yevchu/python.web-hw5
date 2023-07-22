from datetime import datetime, timedelta
import aiohttp
import asyncio
import sys


url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date=20.07.2023'
curency_list = ['USD', 'EUR']

async def fetch_currency(session, url):
    async with session.get(url) as response:
        return await response.json()

async def get_exchange():
    async with aiohttp.ClientSession() as session:
        responses = await asyncio.gather(fetch_currency(session, url))

    result = {}
    our_curr_dict = {}
    
    for response in responses:
        if response['date'] == '20.07.2023':
            exchange_rate = response.get('exchangeRate')
            for currency in exchange_rate:
                if currency.get('currency') in curency_list:
                    our_curr_dict.update({currency.get('currency'): {f"sale: {float(currency.get('saleRate'))}, purchase: {float(currency.get('purchaseRate'))}"}})
        result = {response.get('date'): our_curr_dict}
    return result

def main():
    loop = asyncio.get_event_loop()
    try:
        res = loop.run_until_complete(get_exchange())
        return res
    except (aiohttp.ClientError, ValueError) as e:
        # Обробка помилок мережевих запитів та обробки JSON
        print(f"Error while fetching data: {e}")
        return

if __name__ == "__main__":
    res = main()
    # date_delta = sys.argv[1]
    print(res)
    
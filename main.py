from datetime import datetime, timedelta
import aiohttp
import asyncio
import sys

url = f'https://api.privatbank.ua/p24api/exchange_rates?json'
curency_list = ['USD', 'EUR']
dates_list = []

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
                    our_curr_dict.update({currency.get('currency'): {f"sale: {float(currency.get('saleRate'))}, purchase: {float(currency.get('purchaseRate'))}"}})
        result.update({response.get('date'): our_curr_dict})
    return result

def main(date_delta):
    loop = asyncio.get_event_loop()
    try:
        date_delta = int(date_delta)
        if date_delta > 10:
            print("Too much days, max is 10days")
        else:
            dates = generate_dates(date_delta)
            for date in dates:
                dates_list.append(date.strftime("%d.%m.%Y"))

            try:
                res = loop.run_until_complete(get_exchange(dates_list))
                return res
            except (aiohttp.ClientError, ValueError) as e:
                # Обробка помилок мережевих запитів та обробки JSON
                print(f"Error while fetching data: {e}")
        return
    except ValueError as e:
        return f'Please give me a number! Error:{e}'
        

if __name__ == "__main__":
    date_delta = sys.argv[1]
    res = main(date_delta)
    print(res)
    
import os
import requests
import json
import pandas as pd
from openai import OpenAI

from constants import DOW_JONES_INDEX_COMPANIES, MODELS
from prompts import FIVE_SCORING
from dotenv import load_dotenv

load_dotenv()

# verify that the environment variables are set
assert os.getenv("FMP_API_KEY") is not None
FMP_API_KEY = os.getenv("FMP_API_KEY")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
assert OPEN_ROUTER_API_KEY is not None

def get_info(dump=True):
    print("Fetching information about companies from the API...")
    output = {}
    for company in DOW_JONES_INDEX_COMPANIES:
        print("fetching data for: ", company["Company"])
        symbol = company["Symbol"]
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url)
        data = response.json()
        output[symbol] = data[0]
    
    # save the data to a file as json
    if dump:
        with open("data/profiles.json", "w") as file:
            json.dump(output, file)
    return output
    
    

def fetch_hist_data():
    # Daily Chart EOD API
    print("Downloading historical data - prices for the companies...")

    # read the profiles.json file
    with open("data/profiles.json", "r") as file:
        profiles = json.load(file)
    


    for company in DOW_JONES_INDEX_COMPANIES:
        print("fetching data for: ", company["Company"])
        # create folder in data with symbol name if it doesn't exist
        symbol = company["Symbol"]
        if not os.path.exists(f"data/{symbol}"):
            os.makedirs(f"data/{symbol}")
        
        # read ipoDate from profiles.json
        ipo_date = profiles[symbol]["ipoDate"]

        # fetch historical data
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={ipo_date}&apikey={FMP_API_KEY}"
        response = requests.get(url)
        data = response.json()
        data = pd.DataFrame(data["historical"])
        data.to_csv(f"data/{symbol}/historical.csv", index=False)

    # fetch spy data
    print("fetching data for: SPY")
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/SPY?from=2000-01-01&apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    data = pd.DataFrame(data["historical"])
    data.to_csv(f"data/SPY.csv", index=False)


def fetch_transcript():

    # read the profiles.json file
    with open("data/profiles.json", "r") as file:
        profiles = json.load(file)

    current_timestamp_year = pd.Timestamp.utcnow().year
    print("Downloading transcripts for the companies...")
    for company in DOW_JONES_INDEX_COMPANIES:
        print("fetching data for: ", company["Company"])
        symbol = company["Symbol"]
        init_year = int(profiles[symbol]["ipoDate"].split("-")[0])

        output = {}
        print("Starting at year: ", init_year)
        while init_year <= current_timestamp_year:
            if init_year % 10 == 0:
                print("...: ", init_year)
            url = f"https://financialmodelingprep.com/api/v4/batch_earning_call_transcript/{symbol}?year={init_year}&apikey={FMP_API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            # if data is [] then continue
            if data:
                # check if it has all 4 quarters
                if len(data) != 4:
                    print("Missing data for year: ", init_year)
                    print("qutarters: ", len(data))
                output[init_year] = data

            init_year += 1
        
        # save the data to a file as json
        with open(f"data/{symbol}/transcripts.json", "w") as file:
            json.dump(output, file)



def fetch_model(model_name, promt_class, retries=3):
    if retries <= 0:
        return None
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPEN_ROUTER_API_KEY,
    )

    completion = client.chat.completions.create(
    model=model_name,
    messages=promt_class.messages(),
    )
    if completion.choices is None:
        return fetch_model(model_name, promt_class, retries=retries-1)
    return completion


def do_predictions_for_company(profile, promt_class):
    symbol = profile["symbol"]
    print("Running predictions for: ", symbol)
    # load transcripts
    with open(f"data/{symbol}/transcripts.json", "r") as file:
        transcripts = json.load(file)
        for _, data in transcripts.items():
            for transcript in data:
                promt_class.update(transcript, company_name=profile["companyName"])

                # fetch model
                for model_name, file_output_name  in MODELS.items():
                    if promt_class.check_exists(file_output_name):
                        print(f"{symbol} skipping: ", transcript["date"], " for model: ", model_name)
                        continue
                    completion = fetch_model(model_name, promt_class)
                    promt_class.process_response(completion,file_output_name)



if __name__ == "__main__":
    #get_info()
    #fetch_hist_data()
    #fetch_transcript()
    with open("data/profiles.json", "r") as file:
        profiles = json.load(file)
    import concurrent.futures
    def run(profile):
            prompts_class = FIVE_SCORING()
            do_predictions_for_company(profile, prompts_class)
            print("Done for: ", profile["symbol"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        executor.map(run, profiles.values())



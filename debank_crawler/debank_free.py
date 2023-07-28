"""
2023.7.16
file_name: debank_crawler.debank_free.py
author: Yu Ao
"""
import json
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import requests as requests

if __name__ == "__main__":
    # 1. addr list
    # 2. crawl the chain values
    # 3. crawl the tokens and their values
    # 4. display

    addr_list = []
    # check the directory if the config.json exists
    if os.path.exists("config.json"):
        print("loading exist config.json...")
        with open("config.json", "r", encoding='utf-8') as f:
            addr_list = json.load(f)
        print("config.json loaded")
        print("your addresses are:")
        for addr in addr_list["addresses"]:
            print(addr)

        while True:
            print("whether to add more addresses? (Y/N)")
            choice_temp = input()
            if choice_temp == "Y" or choice_temp == "y":
                print("input your addresses, input \"N\" to finish")
                temp_addr = []
                while True:
                    addr = input()
                    if addr == "N" or addr == "n":
                        break
                    else:
                        temp_addr.append(addr)
                print("your added addresses are:")
                for addr in temp_addr:
                    print(addr)
                print("whether to save the addresses? (Y/N)")
                save_temp = input()
                if save_temp == "Y" or save_temp == "y":
                    addr_list["addresses"].extend(temp_addr)
                    with open("config.json", "w", encoding='utf-8') as f:
                        json.dump(addr_list, f)
                    print("addresses saved")
                else:
                    print("cancel adding addresses")
                break
            elif choice_temp == "N" or choice_temp == "n":
                print("cancel adding addresses")
                break
            else:
                print("invalid input, please input again")
                continue
    else:
        # create the config.json
        print("first time using debank crawler?\nconfig.json not found, creating...")
        with open("config.json", "w", encoding='utf-8') as f:
            default_json = {
                "addr_list": []
            }
            json.dump(default_json, f)
        print("input your addresses, input \"N\" to finish")
        while True:
            addr = input()
            if addr == "N" or addr == "n":
                break
            else:
                addr_list.append(addr)
        print("your addresses are:")
        for addr in addr_list:
            print(addr)
        print("whether to save the addresses? (Y/N)")
        while True:
            save_temp = input()
            if save_temp == "Y" or save_temp == "y":
                default_json = {
                    "addresses": addr_list
                }
                with open("config.json", "w", encoding='utf-8') as f:
                    json.dump(default_json, f)
                print("addresses saved")
                break
            elif save_temp == "N" or save_temp == "n":
                print("cancel adding addresses")
                break
            else:
                print("invalid input, please input again")
                continue

    # crawl the chain values on addr: addr_list(list)
    print("crawling chain values...")
    base_url = "https://api.debank.com/token/cache_balance_list?user_addr={}"
    MAX_RETRY = 3
    addresses_sum_up = {}
    for i, addr in enumerate(addr_list["addresses"]):
        craw_success = False
        for try_times in range(MAX_RETRY):
            url = base_url.format(addr)
            req = requests.get(url)
            print(f"{i + 1}. now address is {addr}")
            print(f"url: {url}, code: {req.status_code}")
            if req.status_code == 200:
                ret_data = req.json()
                if ret_data["error_code"] != 0:
                    print(f"fail to crawl address: {addr}, {ret_data['error_msg']}, retrying...")
                    continue
                else:
                    data = ret_data["data"]
                    # collect chains, sum up values, sort, display
                    result = {}

                    temp_chain = ""
                    temp_total_value = 0

                    temp_token_result_list = []
                    for tokens in data:
                        amount = tokens["amount"]
                        chain = tokens["chain"]
                        symbol = tokens["symbol"]
                        price = tokens["price"]
                        total_value = amount * price
                        if chain == temp_chain:
                            temp_total_value += total_value
                        else:
                            if temp_chain != "":
                                result[temp_chain] = {
                                    "tokens": temp_token_result_list,
                                    "total_value": temp_total_value
                                }
                            temp_chain = chain
                            temp_total_value = total_value
                            temp_token_result_list = []
                        token_result = {
                            "amount": amount,
                            "chain": chain,
                            "symbol": symbol,
                            "price": price,
                            "total_value": total_value
                        }
                        temp_token_result_list.append(token_result)
                    result[temp_chain] = {
                        "tokens": temp_token_result_list,
                        "total_value": temp_total_value
                    }

                    # sort and reserve its type(dict)
                    result = dict(sorted(result.items(), key=lambda x: x[1]["total_value"], reverse=True))
                    addresses_sum_up[addr] = result
                    craw_success = True
                    break
            else:
                print(f"fail to crawl address: {addr}, status code: {req.status_code}, retrying...")
                print(req.text)
                time.sleep(3)
                continue
        if not craw_success:
            print(f"fail to crawl address: {addr}, please check your network")
            exit()

    print("showing the result...")

    # subplots for each address, identify each token of an address
    # add margin to each subplots
    for addr, chains in addresses_sum_up.items():
        fig, axs = plt.subplots(len(chains), 1, figsize=(3, 6), dpi=1000)
        fig.subplots_adjust(hspace=0.2)
        fig.suptitle(addr)
        print(f"plotting address: {addr}")
        for i, (chain, chain_info) in enumerate(chains.items()):
            tokens = chain_info["tokens"]
            total_value = chain_info["total_value"]
            axs[i].set_title(f"{chain}, total value: {total_value}")
            axs[i].pie([token["total_value"] for token in tokens], labels=[token["symbol"] for token in tokens], autopct='%1.1f%%')
        plt.show()



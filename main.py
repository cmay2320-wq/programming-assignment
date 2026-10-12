#!/usr/bin/env python3
"""
PoloBanking 🏦 - terminal banking system (single file)
=======================================================
Everything lives in linked dictionaries. The ACCOUNT NUMBER links them:

    users             "user_1"      -> name, surname, password (hashed)
    accounts          "account_1"   -> owner, account type, account number, bin/id
    cards             "card_1"      -> account number, card number, expiry, CCV
    account_balances  "2736452637"  -> available balance, total balance, pending charges
    transactions      "2736452637"  -> list of transaction dictionaries

Balance rule:  total balance = available balance + pending charges
Demo login:    account number 2736452637 / password Cmay2525
"""

import getpass
import hashlib
import json
import math
import os
import secrets
import sys
import time
from datetime import datetime

DATA_FILE = "polobanking_data.json"
BANK_BIN = "10111"        # every card number starts with the bank's bin/id
CURRENCY = "R"
WITHDRAW_LIMIT = 5000
MAX_ATTEMPTS = 3          # wrong passwords before the login locks
LOCK_SECONDS = 30
WIDTH = 56
HIDE_PASSWORDS = False    # set to False if your console won't accept hidden typing

users = {}
accounts = {}
cards = {}
account_balances = {}
transactions = {}
STORES = {"users": users, "accounts": accounts, "cards": cards,
          "account_balances": account_balances, "transactions": transactions}

def money(amount):
    return f"{CURRENCY}{amount:,.2f}"

def title(text):
    print("\n" + "═" * WIDTH)
    print(text.center(WIDTH))
    print("═" * WIDTH)

def ok(message):
    print(f"  ✓ {message}")

def fail(message):
    print(f"  ✗ {message}")

def ask_yes_no(prompt):
    return input(prompt).strip().lower() in ("y", "yes")

def ask_password(prompt):
    if HIDE_PASSWORDS and sys.stdin.isatty():
        return getpass.getpass(prompt.rstrip(": ") + " (typing is hidden): ")
    return input(prompt)


def ask_amount(prompt):
    try:
        amount = round(float(input(prompt).replace(",", "").replace(CURRENCY, "")), 2)
    except ValueError:
        amount = 0
    if not math.isfinite(amount) or amount <= 0:
        fail("please enter an amount above 0.")
        return None
    return amount

def random_digits(count):
    return "".join(str(secrets.randbelow(10)) for _ in range(count))

def make_password(password):
    """Returns a small dictionary: a random salt + the hashed password."""
    salt = secrets.token_hex(8)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 50_000)
    return {"salt": salt, "password": hashed.hex()}

def check_password(user, password):
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), user["salt"].encode(), 50_000)
    return secrets.compare_digest(hashed.hex(), user["password"])

def ask_new_password():
    while True:
        password = ask_password("  choose a password (8+ characters, letters and numbers): ")
        if len(password) < 8 or password.isalpha() or password.isdigit():
            fail("that password is too weak.")
        elif ask_password("  confirm password: ") == password:
            return password
        else:
            fail("the passwords did not match.")

def find_account(number):
    return next((a for a in accounts.values() if a["account number"] == number), None)

def card_for(number):
    return next((c for c in cards.values() if c["account number"] == number), None)

def seed_data():
    users["user_1"] = {"name": "cj", "surname": "may", **make_password("Cmay2525"),
                       "failed attempts": 0, "locked until": 0}
    accounts["account_1"] = {"owner": "user_1", "account type": "savings",
                             "account number": "2736452637", "bin/id": "10111"}
    cards["card_1"] = {"account number": "2736452637", "name on card": "cj",
                       "card number": "29376564453", "expiary date": "01/30",
                       "CCV": "356", "status": "active"}
    account_balances["2736452637"] = {"available balance R": 2000,
                                      "total balance": 2700, "pending charges": 700}
    transactions["2736452637"] = []

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(STORES, f, indent=2)

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
        for name, table in STORES.items():
            table.update(data.get(name, {}))
    else:
        seed_data()
        save()

def record(number, kind, amount, note=""):
    transactions.setdefault(number, []).append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": kind, "amount": amount, "note": note})

def adjust(number, amount):
    bal = account_balances[number]
    bal["available balance R"] = round(bal["available balance R"] + amount, 2)
    bal["total balance"] = round(bal["total balance"] + amount, 2)

def show_card(card, reveal=False):
    number = card["card number"]
    if reveal:
        number = " ".join(number[i:i + 4] for i in range(0, len(number), 4))
    else:
        number = f"•••• •••• {number[-4:]}"
    print(f"  💳 {number}   exp {card['expiary date']}   "
          f"CCV {card['CCV'] if reveal else '•••'}")
    print(f"     {card['name on card'].upper()}   [{card['status']}]")

def create_account():
    title("CREATE YOUR PROFILE")
    name = input("  first name: ").strip() or "friend"
    surname = input("  surname: ").strip() or "customer"
    password = ask_new_password()

    kind = "cheque" if input("\n  account type - 1. savings  2. cheque: ").strip() == "2" else "savings"
    deposit = None
    while not deposit:
        deposit = ask_amount("  opening deposit: ")

    # build one entry in each linked dictionary
    number = str(secrets.randbelow(9 * 10**9) + 10**9)          # 10 digits
    user_id = f"user_{len(users) + 1}"
    users[user_id] = {"name": name, "surname": surname, **make_password(password),
                      "failed attempts": 0, "locked until": 0}
    accounts[f"account_{len(accounts) + 1}"] = {
        "owner": user_id, "account type": kind,
        "account number": number, "bin/id": BANK_BIN}
    today = datetime.now()
    card = {"account number": number, "name on card": name,
            "card number": BANK_BIN + random_digits(11),
            "expiary date": f"{today.month:02d}/{(today.year + 4) % 100:02d}",
            "CCV": random_digits(3), "status": "active"}
    cards[f"card_{len(cards) + 1}"] = card
    account_balances[number] = {"available balance R": deposit,
                                "total balance": deposit, "pending charges": 0}
    record(number, "opening deposit", deposit)
    save()

    title("ACCOUNT OPENED 🎉")
    print(f"  welcome to polobanking, {name}!\n  account number: {number}   <- you log in with this")
    show_card(card, reveal=True)
    return user_id, number

def login():
    title("LOGIN")
    number = input("  account number: ").strip()
    password = ask_password("  password: ")
    account = find_account(number)
    user = users.get(account["owner"]) if account else None

    if user is None:
        fail("account number or password is wrong.")
    elif user["locked until"] > time.time():
        fail(f"login locked. try again in {int(user['locked until'] - time.time())} seconds.")
    elif check_password(user, password):
        user["failed attempts"] = 0
        save()
        ok(f"welcome back, {user['name']}!")
        return account["owner"], number
    else:
        user["failed attempts"] += 1
        if user["failed attempts"] >= MAX_ATTEMPTS:
            user["failed attempts"] = 0
            user["locked until"] = time.time() + LOCK_SECONDS
            fail(f"too many wrong attempts. locked for {LOCK_SECONDS} seconds.")
        else:
            left = MAX_ATTEMPTS - user["failed attempts"]
            fail(f"account number or password is wrong. {left} attempt(s) left.")
        save()
    return None, None

# every action receives (user_id, number) = who is logged in, and which account
def show_balance(user_id, number):
    bal = account_balances[number]
    title("BALANCE")
    print(f"  account number      {number}")
    print(f"  available balance   {money(bal['available balance R']):>16}")
    print(f"  pending charges     {money(bal['pending charges']):>16}")
    print(f"  total balance       {money(bal['total balance']):>16}")

def deposit(user_id, number):
    title("DEPOSIT")
    amount = ask_amount("  amount to deposit: ")
    if amount:
        adjust(number, amount)
        record(number, "deposit", amount)
        save()
        ok(f"deposited {money(amount)}.")

def withdraw(user_id, number):
    title("WITHDRAW")
    amount = ask_amount(f"  amount to withdraw (limit {money(WITHDRAW_LIMIT)}): ")
    if amount is None:
        return
    if amount > WITHDRAW_LIMIT:
        fail(f"the limit per withdrawal is {money(WITHDRAW_LIMIT)}.")
    elif amount > account_balances[number]["available balance R"]:
        fail("insufficient available balance.")
    else:
        adjust(number, -amount)
        record(number, "withdrawal", -amount)
        save()
        ok(f"withdrew {money(amount)}.")

def transfer(user_id, number):
    title("TRANSFER")
    target_number = input("  recipient account number: ").strip()
    target = find_account(target_number)
    if target is None or target_number == number:
        fail("we could not find that recipient.")
        return
    owner = users[target["owner"]]
    print(f"  recipient: {owner['name']} {owner['surname'][0]}.")

    amount = ask_amount("  amount to send: ")
    if amount is None:
        return
    if amount > account_balances[number]["available balance R"]:
        fail("insufficient available balance.")
        return
    reference = input("  reference (optional): ").strip()
    if not ask_yes_no(f"  send {money(amount)} to {owner['name']}? y/n: "):
        fail("transfer cancelled.")
        return

    adjust(number, -amount)
    adjust(target_number, amount)
    record(number, "transfer out", -amount, f"to {target_number} {reference}".strip())
    record(target_number, "transfer in", amount, f"from {number} {reference}".strip())
    save()
    ok(f"sent {money(amount)} to {owner['name']}.")

def card_purchase(user_id, number):
    """A card payment lowers AVAILABLE balance and adds a PENDING charge."""
    title("CARD PURCHASE")
    card = card_for(number)
    if card is None:
        fail("no card is linked to this account.")
        return
    if card["status"] != "active":
        fail("your card is frozen. unfreeze it under 'my card'.")
        return
    bal = account_balances[number]
    shop = input("  merchant name: ").strip() or "unknown merchant"
    amount = ask_amount("  purchase amount: ")
    if amount is None:
        return
    if amount > bal["available balance R"]:
        fail("card declined: insufficient available balance.")
        return
    bal["available balance R"] = round(bal["available balance R"] - amount, 2)
    bal["pending charges"] = round(bal["pending charges"] + amount, 2)
    record(number, "card purchase", -amount, f"{shop} (pending)")
    save()
    ok(f"{money(amount)} approved at {shop}. it stays pending until processed.")

def process_pending(user_id, number):
    title("PROCESS PENDING CHARGES")
    bal = account_balances[number]
    pending = bal["pending charges"]
    if pending <= 0:
        print("  you have no pending charges.")
    elif ask_yes_no(f"  process {money(pending)} now? y/n: "):
        bal["total balance"] = round(bal["total balance"] - pending, 2)
        bal["pending charges"] = 0
        record(number, "charges processed", 0, f"{money(pending)} cleared")
        save()
        ok(f"{money(pending)} cleared. total balance: {money(bal['total balance'])}")

def statement(user_id, number):
    title("STATEMENT")
    items = transactions.get(number, [])
    if not items:
        print("  no transactions yet.")
    for t in items[-12:]:
        print(f"  {t['time']:<17}{t['type']:<18}{t['amount']:>+12,.2f}")
        if t["note"]:
            print(f"      ↳ {t['note']}")

def my_card(user_id, number):
    title("MY CARD")
    card = card_for(number)
    if card is None:
        fail("no card is linked to this account.")
        return
    show_card(card)
    choice = input("\n  r = reveal details, f = freeze/unfreeze, Enter = back: ").strip().lower()
    if choice == "r" and check_password(users[user_id], ask_password("  password: ")):
        show_card(card, reveal=True)
    elif choice == "r":
        fail("wrong password.")
    elif choice == "f":
        card["status"] = "frozen" if card["status"] == "active" else "active"
        save()
        ok(f"your card is now {card['status']}.")

# a dictionary of menu choices -> (label, function)
MENU = {
    "1": ("Balance", show_balance),
    "2": ("Deposit", deposit),
    "3": ("Withdraw", withdraw),
    "4": ("Transfer", transfer),
    "5": ("Card purchase", card_purchase),
    "6": ("Process pending charges", process_pending),
    "7": ("Statement", statement),
    "8": ("My card", my_card),
}

def session(user_id, number):
    user = users[user_id]
    while True:
        account = find_account(number)
        available = account_balances[number]["available balance R"]
        title(f"{user['name'].upper()} {user['surname'].upper()}")
        print(f"{account['account type']} · {number}".center(WIDTH))
        print(f"available {money(available)}".center(WIDTH))
        for key, (label, _) in MENU.items():
            print(f"   {key}. {label}")
        print("   0. log out")
        choice = input("\n  choose: ").strip()
        if choice == "0":
            ok("logged out. see you soon!")
            return
        if choice in MENU:
            MENU[choice][1](user_id, number)
            input("\n  press Enter to continue...")
        else:
            fail("please choose an option from the menu.")

def main():
    load()
    while True:
        title("welcome to polobanking 🏦")
        print("  is it your first time banking with us?\n     1. yes\n     2. no\n     0. exit")
        option = input("\n  please choose 1 for yes and 2 for no: ").strip()
        user_id = number = None
        if option == "1":
            if ask_yes_no("  would you like to create an account? y/n: "):
                user_id, number = create_account()
            else:
                print("  thank you for visiting our service, please come back soon.")
                break
        elif option == "2":
            user_id, number = login()
        elif option == "0":
            print("  thank you for banking with polobanking. goodbye!")
            break
        else:
            fail("please choose 1, 2 or 0.")
        if user_id:
            session(user_id, number)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n  goodbye!")
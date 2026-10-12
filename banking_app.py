#!/usr/bin/env python3
"""
PyBank - Advanced Terminal Banking System (single file)
=======================================================
Dictionaries are the core of this program:
  * BANK["accounts"]      -> dict of account dicts, keyed by account number
  * ACCOUNT_TYPES         -> dict of per-type rules (fees, interest, limits)
  * each account          -> dict holding profile, balance and transaction dicts
  * MENUS                 -> dict mapping a menu choice to (label, function)
  * LOANS                 -> dict of loan plans
Data is saved to bank_data.json so it survives restarts.
Admin login:  account "ADMIN"  PIN 0000
"""

import hashlib
import json
import os
import random
from datetime import datetime

DATA_FILE = "bank_data.json"
CURRENCY = "R"
MAX_ATTEMPTS = 3

# ---------------------------------------------------------------- rule books
ACCOUNT_TYPES = {
    "1": {"name": "Savings", "interest": 0.05, "min_balance": 100.0,
          "overdraft": 0.0, "withdraw_limit": 5000.0, "fee": 0.0},
    "2": {"name": "Cheque", "interest": 0.01, "min_balance": 0.0,
          "overdraft": 1000.0, "withdraw_limit": 10000.0, "fee": 2.50},
    "3": {"name": "Premium", "interest": 0.08, "min_balance": 1000.0,
          "overdraft": 0.0, "withdraw_limit": 20000.0, "fee": 0.0},
}

LOANS = {
    "1": {"name": "Personal Loan", "rate": 0.12, "max": 20000.0, "months": 12},
    "2": {"name": "Car Loan", "rate": 0.10, "max": 150000.0, "months": 48},
    "3": {"name": "Home Loan", "rate": 0.08, "max": 800000.0, "months": 120},
}

# ---------------------------------------------------------------- the "database"
BANK = {"accounts": {}, "next_id": 1001, "log": []}


# ---------------------------------------------------------------- helpers
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(amount):
    return f"{CURRENCY}{amount:,.2f}"


def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()


def line(char="=", width=60):
    print(char * width)


def title(text):
    print()
    line()
    print(text.center(60))
    line()


def ask_amount(prompt):
    try:
        value = float(input(prompt).replace(",", "").replace(CURRENCY, ""))
    except ValueError:
        print("  Invalid number.")
        return None
    if value <= 0:
        print("  Amount must be greater than zero.")
        return None
    return round(value, 2)


def ask_pin(prompt="  Enter 4-digit PIN: "):
    pin = input(prompt).strip()
    if len(pin) == 4 and pin.isdigit():
        return pin
    print("  PIN must be exactly 4 digits.")
    return None


# ---------------------------------------------------------------- persistence
def save():
    with open(DATA_FILE, "w") as f:
        json.dump(BANK, f, indent=2)


def load():
    global BANK
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            BANK = json.load(f)
    if "ADMIN" not in BANK["accounts"]:
        BANK["accounts"]["ADMIN"] = {
            "name": "Administrator", "pin": hash_pin("0000"), "type": "Admin",
            "balance": 0.0, "created": now(), "failed": 0, "locked": False,
            "transactions": [], "loans": {},
        }


# ---------------------------------------------------------------- core engine
def record(acc, kind, amount, note=""):
    """Append a transaction dictionary to an account and to the bank log."""
    entry = {"time": now(), "type": kind, "amount": amount,
             "balance_after": acc["balance"], "note": note}
    acc["transactions"].append(entry)
    BANK["log"].append({"time": entry["time"], "type": kind, "amount": amount})


def rules(acc):
    for rule in ACCOUNT_TYPES.values():
        if rule["name"] == acc["type"]:
            return rule
    return {"interest": 0, "min_balance": 0, "overdraft": 0,
            "withdraw_limit": 0, "fee": 0}


def available(acc):
    r = rules(acc)
    return acc["balance"] - r["min_balance"] + r["overdraft"]


def new_account_number():
    num = str(BANK["next_id"])
    BANK["next_id"] += 1
    return num


# ---------------------------------------------------------------- customer actions
def create_account():
    title("OPEN A NEW ACCOUNT")
    name = input("  Full name: ").strip()
    if not name:
        print("  Name cannot be empty.")
        return
    print("\n  Account types:")
    for key, r in ACCOUNT_TYPES.items():
        print(f"   {key}. {r['name']:<8} interest {r['interest']*100:.0f}%  "
              f"min balance {money(r['min_balance'])}  "
              f"overdraft {money(r['overdraft'])}")
    choice = input("  Choose type: ").strip()
    if choice not in ACCOUNT_TYPES:
        print("  Invalid type.")
        return
    pin = ask_pin("  Choose a 4-digit PIN: ")
    if not pin:
        return
    rule = ACCOUNT_TYPES[choice]
    deposit = ask_amount(f"  Opening deposit (min {money(rule['min_balance'])}): ")
    if deposit is None or deposit < rule["min_balance"]:
        print("  Opening deposit too low.")
        return
    number = new_account_number()
    acc = {"name": name, "pin": hash_pin(pin), "type": rule["name"],
           "balance": deposit, "created": now(), "failed": 0,
           "locked": False, "transactions": [], "loans": {}}
    BANK["accounts"][number] = acc
    record(acc, "OPEN", deposit, "Opening deposit")
    save()
    print(f"\n  Account created! Your account number is {number}")


def login():
    title("LOGIN")
    number = input("  Account number: ").strip().upper()
    acc = BANK["accounts"].get(number)
    if not acc:
        print("  Account not found.")
        return None, None
    if acc["locked"]:
        print("  This account is locked. Visit admin to unlock.")
        return None, None
    pin = ask_pin()
    if pin and hash_pin(pin) == acc["pin"]:
        acc["failed"] = 0
        save()
        print(f"\n  Welcome back, {acc['name']}!")
        return number, acc
    acc["failed"] += 1
    left = MAX_ATTEMPTS - acc["failed"]
    if left <= 0:
        acc["locked"] = True
        print("  Too many failed attempts. Account locked.")
    else:
        print(f"  Wrong PIN. {left} attempt(s) left.")
    save()
    return None, None


def balance(number, acc):
    title("BALANCE")
    print(f"  Account : {number} ({acc['type']})")
    print(f"  Balance : {money(acc['balance'])}")
    print(f"  Available to spend: {money(available(acc))}")


def deposit(number, acc):
    amount = ask_amount("  Deposit amount: ")
    if amount is None:
        return
    acc["balance"] = round(acc["balance"] + amount, 2)
    record(acc, "DEPOSIT", amount)
    save()
    print(f"  Deposited {money(amount)}. New balance {money(acc['balance'])}")


def withdraw(number, acc):
    amount = ask_amount("  Withdraw amount: ")
    if amount is None:
        return
    r = rules(acc)
    fee = r["fee"]
    if amount > r["withdraw_limit"]:
        print(f"  Limit per withdrawal is {money(r['withdraw_limit'])}.")
    elif amount + fee > available(acc):
        print("  Insufficient funds.")
    else:
        acc["balance"] = round(acc["balance"] - amount - fee, 2)
        record(acc, "WITHDRAW", -amount, f"Fee {money(fee)}")
        save()
        print(f"  Withdrew {money(amount)} (fee {money(fee)}). "
              f"New balance {money(acc['balance'])}")


def transfer(number, acc):
    target_no = input("  Recipient account number: ").strip()
    target = BANK["accounts"].get(target_no)
    if not target or target_no in ("ADMIN", number):
        print("  Invalid recipient.")
        return
    print(f"  Recipient: {target['name']}")
    amount = ask_amount("  Transfer amount: ")
    if amount is None:
        return
    if amount > available(acc):
        print("  Insufficient funds.")
        return
    note = input("  Reference (optional): ").strip()
    acc["balance"] = round(acc["balance"] - amount, 2)
    target["balance"] = round(target["balance"] + amount, 2)
    record(acc, "TRANSFER OUT", -amount, f"To {target_no} {note}")
    record(target, "TRANSFER IN", amount, f"From {number} {note}")
    save()
    print(f"  Sent {money(amount)} to {target['name']}.")


def statement(number, acc):
    title(f"STATEMENT - {acc['name']}")
    if not acc["transactions"]:
        print("  No transactions yet.")
        return
    print(f"  {'Date':<20}{'Type':<14}{'Amount':>12}{'Balance':>14}")
    line("-")
    for t in acc["transactions"][-15:]:
        print(f"  {t['time']:<20}{t['type']:<14}{t['amount']:>12,.2f}"
              f"{t['balance_after']:>14,.2f}")
    # summary built with a dictionary of totals
    totals = {}
    for t in acc["transactions"]:
        totals[t["type"]] = totals.get(t["type"], 0) + t["amount"]
    line("-")
    print("  Totals by type:")
    for kind, total in sorted(totals.items()):
        print(f"   {kind:<14}{money(total):>14}")


def apply_interest(number, acc):
    rate = rules(acc)["interest"]
    interest = round(acc["balance"] * rate / 12, 2)
    if interest <= 0:
        print("  No interest earned on this account.")
        return
    acc["balance"] += interest
    record(acc, "INTEREST", interest, f"Monthly @ {rate*100:.0f}% p.a.")
    save()
    print(f"  Interest of {money(interest)} added.")


def take_loan(number, acc):
    title("LOANS")
    for key, plan in LOANS.items():
        print(f"  {key}. {plan['name']:<14} up to {money(plan['max'])}  "
              f"{plan['rate']*100:.0f}% over {plan['months']} months")
    choice = input("  Choose plan (or Enter to view my loans): ").strip()
    if not choice:
        if not acc["loans"]:
            print("  You have no loans.")
        for loan_id, loan in acc["loans"].items():
            print(f"  {loan_id}: {loan['plan']} owing {money(loan['owing'])} "
                  f"({money(loan['monthly'])}/month)")
        return
    plan = LOANS.get(choice)
    if not plan:
        print("  Invalid plan.")
        return
    amount = ask_amount("  Loan amount: ")
    if amount is None or amount > plan["max"]:
        print("  Amount not allowed for this plan.")
        return
    total = round(amount * (1 + plan["rate"]), 2)
    monthly = round(total / plan["months"], 2)
    print(f"  Total to repay {money(total)} -> {money(monthly)}/month")
    if input("  Accept? (y/n): ").lower() != "y":
        return
    loan_id = "L" + str(random.randint(1000, 9999))
    acc["loans"][loan_id] = {"plan": plan["name"], "owing": total,
                             "monthly": monthly, "date": now()}
    acc["balance"] += amount
    record(acc, "LOAN", amount, f"{plan['name']} {loan_id}")
    save()
    print(f"  Loan {loan_id} approved and paid into your account.")


def repay_loan(number, acc):
    if not acc["loans"]:
        print("  You have no loans.")
        return
    loan_id = input("  Loan ID to repay: ").strip().upper()
    loan = acc["loans"].get(loan_id)
    if not loan:
        print("  Loan not found.")
        return
    amount = ask_amount(f"  Repay amount (owing {money(loan['owing'])}): ")
    if amount is None:
        return
    amount = min(amount, loan["owing"])
    if amount > available(acc):
        print("  Insufficient funds.")
        return
    acc["balance"] -= amount
    loan["owing"] = round(loan["owing"] - amount, 2)
    record(acc, "LOAN REPAY", -amount, loan_id)
    if loan["owing"] <= 0:
        del acc["loans"][loan_id]
        print("  Loan fully repaid!")
    save()
    print(f"  Paid {money(amount)}.")


def change_pin(number, acc):
    old = ask_pin("  Current PIN: ")
    if not old or hash_pin(old) != acc["pin"]:
        print("  Incorrect PIN.")
        return
    new = ask_pin("  New PIN: ")
    if new:
        acc["pin"] = hash_pin(new)
        save()
        print("  PIN changed.")


# ---------------------------------------------------------------- admin tools
def admin_report():
    title("BANK REPORT")
    accounts = {n: a for n, a in BANK["accounts"].items() if n != "ADMIN"}
    by_type = {}
    for a in accounts.values():
        info = by_type.setdefault(a["type"], {"count": 0, "total": 0.0})
        info["count"] += 1
        info["total"] += a["balance"]
    print(f"  {'No.':<8}{'Name':<20}{'Type':<10}{'Balance':>14}  Status")
    line("-")
    for n, a in accounts.items():
        status = "LOCKED" if a["locked"] else "active"
        print(f"  {n:<8}{a['name'][:19]:<20}{a['type']:<10}"
              f"{a['balance']:>14,.2f}  {status}")
    line("-")
    for t, info in by_type.items():
        print(f"  {t:<10}{info['count']} account(s)  total {money(info['total'])}")
    print(f"  Bank holds {money(sum(i['total'] for i in by_type.values()))} "
          f"across {len(accounts)} accounts, {len(BANK['log'])} transactions.")


def admin_unlock():
    number = input("  Account to unlock: ").strip()
    acc = BANK["accounts"].get(number)
    if acc:
        acc["locked"], acc["failed"] = False, 0
        save()
        print("  Account unlocked.")
    else:
        print("  Account not found.")


def admin_delete():
    number = input("  Account to close: ").strip()
    if number in BANK["accounts"] and number != "ADMIN":
        if input(f"  Close {number}? (y/n): ").lower() == "y":
            del BANK["accounts"][number]
            save()
            print("  Account closed.")
    else:
        print("  Account not found.")


# ---------------------------------------------------------------- menus (dispatch dictionaries)
CUSTOMER_MENU = {
    "1": ("Balance", balance), "2": ("Deposit", deposit),
    "3": ("Withdraw", withdraw), "4": ("Transfer", transfer),
    "5": ("Statement", statement), "6": ("Monthly interest", apply_interest),
    "7": ("Loans", take_loan), "8": ("Repay loan", repay_loan),
    "9": ("Change PIN", change_pin),
}

ADMIN_MENU = {
    "1": ("Bank report", lambda n, a: admin_report()),
    "2": ("Unlock account", lambda n, a: admin_unlock()),
    "3": ("Close account", lambda n, a: admin_delete()),
}


def session(number, acc):
    menu = ADMIN_MENU if number == "ADMIN" else CUSTOMER_MENU
    while True:
        title(f"{acc['name'].upper()} - {acc['type']}")
        for key, (label, _) in menu.items():
            print(f"  {key}. {label}")
        print("  0. Logout")
        choice = input("\n  Select: ").strip()
        if choice == "0":
            print("  Logged out.")
            return
        if choice in menu:
            menu[choice][1](number, acc)
        else:
            print("  Invalid option.")


def main():
    load()
    while True:
        title("PYBANK TERMINAL BANKING")
        print("  1. Login\n  2. Open account\n  0. Exit")
        choice = input("\n  Select: ").strip()
        if choice == "1":
            number, acc = login()
            if acc:
                session(number, acc)
        elif choice == "2":
            create_account()
        elif choice == "0":
            save()
            print("  Goodbye!")
            break
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
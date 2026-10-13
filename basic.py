# PoloBank Basic - a simple banking app using only basic Python and dictionaries.
# No imports, no files. Everything is kept in dictionaries while the program runs
# (so the data resets each time you close the program).
#
# The ACCOUNT NUMBER is the key that links the three dictionaries together.

# users: account number -> dictionary of details
users = {
    "1001": {"name": "cj", "surname": "may", "password": "Cmay2525"},
}

# account_balances: account number -> dictionary of the three balances
account_balances = {
    "1001": {"available balance": 2000, "pending charges": 700, "total balance": 2700},
}

# history: account number -> LIST of transaction dictionaries
history = {
    "1001": [],
}


# ---------------------------------------------------------------- helpers
def get_amount(question):
    # asks for a number, returns it, or returns 0 if it is not valid
    try:
        amount = float(input(question))
    except ValueError:
        print("That is not a number.")
        return 0
    if amount <= 0:
        print("The amount must be more than 0.")
        return 0
    return amount


def add_history(number, kind, amount):
    # makes one small dictionary and adds it to the list for this account
    transaction = {"type": kind, "amount": amount}
    history[number].append(transaction)


# ---------------------------------------------------------------- sign up / login
def create_account():
    print("\n--- CREATE ACCOUNT ---")
    name = input("First name: ")
    surname = input("Surname: ")
    password = input("Choose a password (at least 6 characters): ")
    if len(password) < 6:
        print("Password is too short.")
        return

    deposit = get_amount("Opening deposit: R")
    if deposit == 0:
        return

    number = str(1001 + len(users))      # next account number: 1002, 1003, ...

    # one new entry in each dictionary
    users[number] = {"name": name, "surname": surname, "password": password}
    account_balances[number] = {
        "available balance": deposit,
        "pending charges": 0,
        "total balance": deposit,
    }
    history[number] = []
    add_history(number, "opening deposit", deposit)

    print("Account created! Your account number is", number)


def login():
    print("\n--- LOGIN ---")
    number = input("Account number: ")
    if number not in users:
        print("Account not found.")
        return None

    for attempt in range(3):             # 3 tries for the password
        password = input("Password: ")
        if password == users[number]["password"]:
            print("Welcome,", users[number]["name"] + "!")
            return number
        print("Wrong password.", 2 - attempt, "tries left.")

    print("Too many wrong tries.")
    return None


# ---------------------------------------------------------------- banking actions
def show_balance(number):
    bal = account_balances[number]
    print("\n--- BALANCE ---")
    print("Available balance: R", bal["available balance"])
    print("Pending charges:   R", bal["pending charges"])
    print("Total balance:     R", bal["total balance"])


def deposit(number):
    amount = get_amount("Deposit amount: R")
    if amount > 0:
        account_balances[number]["available balance"] += amount
        account_balances[number]["total balance"] += amount
        add_history(number, "deposit", amount)
        print("Deposited R", amount)


def withdraw(number):
    amount = get_amount("Withdraw amount: R")
    if amount > account_balances[number]["available balance"]:
        print("Not enough available money.")
    elif amount > 0:
        account_balances[number]["available balance"] -= amount
        account_balances[number]["total balance"] -= amount
        add_history(number, "withdrawal", -amount)
        print("Withdrew R", amount)


def transfer(number):
    other = input("Send to account number: ")
    if other not in users or other == number:
        print("That account does not exist.")
        return
    print("Sending to", users[other]["name"], users[other]["surname"])

    amount = get_amount("Amount to send: R")
    if amount > account_balances[number]["available balance"]:
        print("Not enough available money.")
    elif amount > 0:
        account_balances[number]["available balance"] -= amount
        account_balances[number]["total balance"] -= amount
        account_balances[other]["available balance"] += amount
        account_balances[other]["total balance"] += amount
        add_history(number, "sent to " + other, -amount)
        add_history(other, "received from " + number, amount)
        print("Sent R", amount)


def pay(number):
    # a card payment: available money drops now, but it stays "pending" for a while
    amount = get_amount("Payment amount: R")
    if amount > account_balances[number]["available balance"]:
        print("Payment declined: not enough available money.")
    elif amount > 0:
        account_balances[number]["available balance"] -= amount
        account_balances[number]["pending charges"] += amount
        add_history(number, "card payment (pending)", -amount)
        print("Payment of R", amount, "is pending.")


def process_pending(number):
    # the bank finishes the payments: pending charges leave the total balance
    bal = account_balances[number]
    if bal["pending charges"] == 0:
        print("You have no pending charges.")
    else:
        bal["total balance"] -= bal["pending charges"]
        print("R", bal["pending charges"], "processed.")
        bal["pending charges"] = 0


def show_history(number):
    print("\n--- HISTORY ---")
    if len(history[number]) == 0:
        print("Nothing here yet.")
    for item in history[number]:
        print(item["type"], "   R", item["amount"])


# ---------------------------------------------------------------- menus
# a dictionary of menu choices -> (label, function)
menu = {
    "1": ("Balance", show_balance),
    "2": ("Deposit", deposit),
    "3": ("Withdraw", withdraw),
    "4": ("Transfer", transfer),
    "5": ("Pay with card", pay),
    "6": ("Process pending charges", process_pending),
    "7": ("History", show_history),
}


def bank_menu(number):
    while True:
        print("\n=== POLOBANK ===")
        for key in menu:
            print(key + ".", menu[key][0])     # [0] is the label
        print("0. Log out")

        choice = input("Choose: ")
        if choice == "0":
            print("Logged out.")
            break
        elif choice in menu:
            menu[choice][1](number)            # [1] is the function, then we run it
        else:
            print("Please choose a number from the menu.")



# ---------------------------------------------------------------- start of the program
def main():
    while True:
        print("\n=== WELCOME TO POLOBANK ===")
        print("1. Login")
        print("2. Create account")
        print("0. Exit")
        option = input("Choose: ")

        if option == "1":
            number = login()
            if number is not None:
                bank_menu(number)
        elif option == "2":
            create_account()
        elif option == "0":
            print("Goodbye!")
            break
        else:
            print("Please choose 1, 2 or 0.")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\ngoodbye")
        
    



    
        

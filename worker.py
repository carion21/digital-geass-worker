from time import sleep, time
from joblib import Parallel, delayed
from datetime import datetime

from constants import *
from functions import treat_abandoned_orders, treat_not_delivered_orders, treat_pending_orders
from utilities import get_env_vars

env_vars = get_env_vars()
logger = env_vars.get("logger")

sys_waitime = 30

# print(env_vars)


while True:

    # Treat the pending transactions
    treat_pending_orders(env_vars)

    # Treat the abandoned orders
    treat_abandoned_orders(env_vars)

    # Treat the orders with product not delivered
    treat_not_delivered_orders(env_vars)

    sleep(sys_waitime)

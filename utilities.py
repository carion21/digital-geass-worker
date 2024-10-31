
import base64
import json
import multiprocessing
import os
import shutil
from typing import Optional
from constants import *
from decouple import config
import requests as rq
from datetime import datetime, timedelta
import logging
from logging.handlers import TimedRotatingFileHandler


def get_logger():
    """Get the logger."""
    try:
        # Configuration du logger
        logger = logging.getLogger(APP_NAME)
        logger.setLevel(logging.DEBUG)

        # Formatter pour le log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if not os.path.exists(LOG_DIRECTORY):
            os.makedirs(LOG_DIRECTORY)

        # Création d'un gestionnaire de fichiers rotatif basé sur la date
        log_filename = datetime.now().strftime("./logs/%Y-%m-%d.log")
        file_handler = TimedRotatingFileHandler(
            log_filename, when="midnight", interval=1, backupCount=3)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        # Ajout du gestionnaire de fichiers au logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger
    except Exception as e:
        print("Error while getting logger: ", e)
        return None


def load_json(file_path: str):
    """Load a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return None


def save_json(data: dict, file_path: str):
    """Save a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        return False


def get_env_var(var_name: str):
    """Get an environment variable, or return a default value."""
    return config(var_name)


def get_env_vars():
    """Get all environment variables."""
    evars = {key: get_env_var(key) for key in KEYS}
    evars['logger'] = get_logger()
    return evars


def show_errors(res):
    '''Show errors from CORE'''
    error = ""
    try:
        # print(res.json()['errors'])
        for err in res.json()['errors']:
            error += 'Status: ' + \
                str(err['status']) + ' | ' + 'Message: ' + err['detail'] + '\n'
    except Exception as e:
        error = 'Error while showing errors: ' + str(e)
    return error


def show_directus_errors(res):
    '''Show errors from DIRECTUS'''
    error = ""
    try:
        # print(res.json()['errors'])
        for err in res.json()['errors']:
            error += 'Status: ' + str(res.status_code) + \
                ' | ' + 'Message: ' + err['message'] + '\n'
    except Exception as e:
        error = 'Error while showing directus errors: ' + str(e)
    return error


def get_url_of_directus_to_use(env_vars: dict):
    """Get the URL of Directus to use."""
    return env_vars.get("URL_OF_DIRECTUS_INPROD") if env_vars.get("ENV") == "inprod" else env_vars.get("URL_OF_DIRECTUS_NOPROD")


def make_get_request(base_url: str, endpoint: str, headers: dict):
    """Make a GET request."""
    try:
        urlcomplete = base_url + endpoint
        res = rq.request("GET", urlcomplete, headers=headers)
        return res
    except Exception as e:
        return None


def make_post_request(base_url: str, endpoint: str, headers: dict, payload: dict):
    """Make a POST request."""
    try:
        urlcomplete = base_url + endpoint
        res = rq.request("POST", urlcomplete, headers=headers, data=payload)
        return res
    except Exception as e:
        return None


def listmonk_create_subscriber(env_vars: dict, data: dict):
    """Create a subscriber."""
    logger = env_vars.get('logger')
    base_error = "Error while creating subscriber: "
    error = ""
    try:
        urlcomplete = env_vars.get("LISTMONK_API_URL") + '/subscribers'

        basic_token = base64.b64encode(
            f"{env_vars.get('LISTMONK_API_USERNAME')}:{env_vars.get('LISTMONK_API_PASSWORD')}"
            .encode()
        ).decode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Basic {basic_token}'
        }
        payload = json.dumps(data)

        res = rq.request("POST", urlcomplete, headers=headers, data=payload)
        if res.status_code not in [200, 201]:
            error = show_errors(res)
            return {
                'success': False,
                'status_code': res.status_code,
                'message': error
            }
        else:
            rdata = res.json()
            logger.info("Subscriber created with success.")
            return {
                'success': True,
                'message': 'Subscriber created with success.',
                'data': rdata.get('data')
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )


def listmonk_send_email(env_vars: dict, data: dict):
    """Send an email."""
    logger = env_vars.get('logger')
    base_error = "Error while sending email: "
    error = ""
    try:
        urlcomplete = env_vars.get("LISTMONK_API_URL") + '/tx'

        basic_token = base64.b64encode(
            f"{env_vars.get('LISTMONK_API_USERNAME')}:{env_vars.get('LISTMONK_API_PASSWORD')}"
            .encode()
        ).decode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Basic {basic_token}'
        }
        payload = json.dumps(data)

        res = rq.request("POST", urlcomplete, headers=headers, data=payload)
        if res.status_code not in [200, 201]:
            error = show_errors(res)
            return {
                'success': False,
                'status_code': res.status_code,
                'message': error
            }
        else:
            logger.info("Email sent with success.")
            return {
                'success': True,
                'message': 'Email sent with success.',
                'data': res.json()
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )


def cinetpay_check_transaction(env_vars: dict, transaction_code: str):
    """Check cinetpay transaction."""
    logger = env_vars.get('logger')
    base_error = "Error while checking cinetpay transaction: "
    error = ""
    try:
        urlcomplete = env_vars.get("CINETPAY_CHECK_URL")
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            'apikey': env_vars.get("CINETPAY_API_KEY"),
            'site_id': env_vars.get("CINETPAY_SITE_ID"),
            'transaction_id': transaction_code
        })

        res = rq.request("POST", urlcomplete, headers=headers,
                         data=payload, verify=True)
        if res.status_code not in [200, 201]:
            error = show_errors(res)
            return {
                'success': False,
                'message': error
            }
        else:
            return {
                'success': True,
                'message': 'Transaction checked with success.',
                'data': res.json()
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )


def directus_retrieve_product(env_vars: dict, product_id: str):
    """Retrieve product."""
    logger = env_vars.get('logger')
    base_error = "Error while retrieving product: "
    error = ""
    try:
        urlcomplete = get_url_of_directus_to_use(
            env_vars) + env_vars.get("ROUTE_OF_DIRECTUS_FOR_DGEASS_PRODUCT") + '/' + product_id
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        res = rq.request("GET", urlcomplete, headers=headers)
        if res.status_code not in [200, 201]:
            error = show_directus_errors(res)
            return {
                'success': False,
                'message': error
            }
        else:
            logger.info("Product retrieved with success.")
            return {
                'success': True,
                'message': 'Product retrieved with success.',
                'data': res.json().get('data')
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )


def directus_list_orders(env_vars: dict, transaction_status: Optional[int] = None):
    """List orders."""
    logger = env_vars.get('logger')
    base_error = "Error while listing orders: "
    error = ""
    try:
        urlcomplete = get_url_of_directus_to_use(
            env_vars) + env_vars.get("ROUTE_OF_DIRECTUS_FOR_DGEASS_ORDER")

        urlcomplete += '?filter[status][_eq]={}'.format(ORDER_STATUS_STARTED)
        urlcomplete += '&filter[transaction_status][_eq]={}'.format(
            transaction_status)

        print(urlcomplete)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        res = rq.request("GET", urlcomplete, headers=headers)
        if res.status_code not in [200, 201, 204]:
            error = show_directus_errors(res)
            return {
                'success': False,
                'message': error
            }
        else:
            logger.info("Orders listed with success.")
            return {
                'success': True,
                'message': 'Orders listed with success.',
                'data': res.json()['data']
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )


def directus_list_abandoned_orders(env_vars: dict):
    """List abandoned orders."""
    logger = env_vars.get('logger')
    base_error = "Error while listing abandoned orders: "
    error = ""
    try:
        # Calculer la date actuelle moins un jour avec heures, minutes et secondes
        filter_date = (datetime.now() - timedelta(days=1)
                       ).strftime("%Y-%m-%dT%H:%M:%S")
        print('filter_date', filter_date)

        # Construire l'URL avec le filtre complet
        urlcomplete = (
            get_url_of_directus_to_use(env_vars)
            + env_vars.get("ROUTE_OF_DIRECTUS_FOR_DGEASS_ORDER")
            + f"?filter[status][_eq]={ORDER_STATUS_STARTED}&filter[date_created][_lt]={filter_date}"
        )
        print('urlcomplete', urlcomplete)

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        res = rq.request("GET", urlcomplete, headers=headers)
        if res.status_code not in [200, 201, 204]:
            error = show_directus_errors(res)
            return {
                'success': False,
                'message': error
            }
        else:
            logger.info("Abandoned orders listed with success.")
            return {
                'success': True,
                'message': 'Abandoned orders listed with success.',
                'data': res.json()['data']
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )

# where product_is_delivered = false


def directus_list_orders_with_product_not_delivered(env_vars: dict):
    """List orders with product not delivered."""
    logger = env_vars.get('logger')
    base_error = "Error while listing orders with product not delivered: "
    error = ""
    try:
        urlcomplete = (
            get_url_of_directus_to_use(env_vars)
            + env_vars.get("ROUTE_OF_DIRECTUS_FOR_DGEASS_ORDER")
            + "?filter[transaction_status][_eq]=2"
            + "&filter[product_is_delivered][_eq]=false"
            + "&fields=*,tunnel.*"
        )

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        res = rq.request("GET", urlcomplete, headers=headers)
        if res.status_code not in [200, 201, 204]:
            error = show_directus_errors(res)
            return {
                'success': False,
                'message': error
            }
        else:
            logger.info(
                "Orders with product not delivered listed with success.")
            return {
                'success': True,
                'message': 'Orders with product not delivered listed with success.',
                'data': res.json()['data']
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )


def directus_update_order(env_vars: dict, order_id: str, data: dict):
    """Update order."""
    logger = env_vars.get('logger')
    base_error = "Error while updating order: "
    error = ""
    try:
        urlcomplete = get_url_of_directus_to_use(
            env_vars) + env_vars.get("ROUTE_OF_DIRECTUS_FOR_DGEASS_ORDER") + '/' + order_id
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = json.dumps(data)

        res = rq.request("PATCH", urlcomplete, headers=headers, data=payload)
        if res.status_code not in [200, 201]:
            error = show_directus_errors(res)
            return {
                'success': False,
                'message': error
            }
        else:
            logger.info("Order updated with success.")
            return {
                'success': True,
                'message': 'Order updated with success.',
                'data': res.json()
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )


def directus_create_transaction_log(env_vars: dict, data: dict):
    """Create transaction log."""
    logger = env_vars.get('logger')
    base_error = "Error while creating transaction log: "
    error = ""
    try:
        urlcomplete = get_url_of_directus_to_use(
            env_vars) + env_vars.get("ROUTE_OF_DIRECTUS_FOR_DGEASS_TRANSACTION_LOG")

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = json.dumps(data)

        res = rq.request("POST", urlcomplete, headers=headers, data=payload)
        if res.status_code not in [200, 201]:
            error = show_directus_errors(res)
            return {
                'success': False,
                'message': error
            }
        else:
            logger.info("Transaction log created with success.")
            return {
                'success': True,
                'message': 'Transaction log created with success.',
                'data': res.json()
            }
    except Exception as e:
        error = str(e)
        logger.error(
            LOG_CONST.format(
                base_error,
                error
            )
        )

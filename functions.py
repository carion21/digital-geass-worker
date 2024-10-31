from time import sleep, time
from joblib import Parallel, delayed
from datetime import datetime

from constants import *
from minioservice import MinioService
from utilities import cinetpay_check_transaction, directus_create_transaction_log, directus_list_abandoned_orders, directus_list_orders, directus_list_orders_with_product_not_delivered, directus_retrieve_product, directus_update_order, listmonk_create_subscriber, listmonk_send_email


def treat_pending_orders(env_vars: dict):
    """Traiter les commandes en attente"""
    logger = env_vars.get("logger")
    try:
        r_dts_orders = directus_list_orders(
            env_vars=env_vars,
            transaction_status=TRANSACTION_STATUS_PENDING
        )

        if r_dts_orders.get('success'):
            orders = r_dts_orders.get('data')
            print('orders', len(orders))

            if len(orders) == 0:
                logger.info("No transaction to monitor")
            else:
                for order in orders:
                    rcheck = cinetpay_check_transaction(
                        env_vars=env_vars,
                        transaction_code=order.get("code")
                    )
                    dcheck = rcheck.get("data").get("data")
                    # print(dcheck)
                    current_status = dcheck.get("status")

                    o_status = None
                    t_status = None

                    print('Current status of {} is: {}'.format(
                        order.get("code"), current_status))

                    if current_status == "ACCEPTED":
                        o_status = ORDER_STATUS_COMPLETED
                        t_status = TRANSACTION_STATUS_ACCEPTED
                    elif current_status == "REFUSED":
                        o_status = ORDER_STATUS_FAILED
                        t_status = TRANSACTION_STATUS_REFUSED

                    if t_status in [TRANSACTION_STATUS_ACCEPTED, TRANSACTION_STATUS_REFUSED]:
                        # Update the order status
                        r_dts_upd_order = directus_update_order(
                            env_vars=env_vars,
                            order_id=str(order.get("id")),
                            data={
                                "status": o_status,
                                "transaction_status": t_status
                            }
                        )

                        if r_dts_upd_order.get('success'):
                            logger.info("Order {} updated with success.".format(
                                order.get("code")))
                            directus_create_transaction_log(
                                env_vars=env_vars,
                                data={
                                    'order': str(order.get("id")),
                                    'status': t_status
                                })

    except Exception as e:
        print('Error in treat_pending_orders:', e)


def treat_abandoned_orders(env_vars: dict):
    """Traiter les commandes abandonnées"""
    logger = env_vars.get("logger")
    try:
        r_dts_abandoned_orders = directus_list_abandoned_orders(
            env_vars=env_vars,
        )

        if r_dts_abandoned_orders.get('success'):
            abandoned_orders = r_dts_abandoned_orders.get('data')
            print('abandoned_orders', len(abandoned_orders))

            if len(abandoned_orders) == 0:
                logger.info("No abandoned order to monitor")
            else:
                for order in abandoned_orders:
                    r_dts_upd_order = directus_update_order(
                        env_vars=env_vars,
                        order_id=str(order.get("id")),
                        data={
                            "status": ORDER_STATUS_ABANDONED
                        }
                    )
    except Exception as e:
        print('Error in treat_abandoned_orders:', e)


def treat_not_delivered_orders(env_vars: dict):
    """Traiter les commandes non livrées"""
    logger = env_vars.get("logger")
    try:
        r_dts_orders = directus_list_orders_with_product_not_delivered(
            env_vars=env_vars,
        )

        if r_dts_orders.get('success'):
            orders = r_dts_orders.get('data')
            print('orders', len(orders))

            if len(orders) == 0:
                logger.info("No order to deliver")
            else:
                for order in orders:
                    # save_json(order, '{}.json'.format(order.get('code')))
                    product = None

                    r_dts_product = directus_retrieve_product(
                        env_vars=env_vars,
                        product_id=str(order.get('tunnel').get('product'))
                    )
                    if r_dts_product.get('success'):
                        product = r_dts_product.get('data')
                        print('product', product)
                        # save_json(product, '{}.json'.format(product.get('code')))

                        customer_email = order.get('email')
                        customer_name = f"{order.get('lastname')} {order.get('firstname')}"

                        subscriber_data = {
                            "email": customer_email,
                            "name": customer_name,
                            "status": "enabled",
                            "lists": [
                                3
                            ]
                        }

                        r_lmk_subscriber = listmonk_create_subscriber(
                            env_vars=env_vars,
                            data=subscriber_data
                        )
                        if r_lmk_subscriber.get('success'):
                            print('Email subscriber created :', customer_email)
                        elif not r_lmk_subscriber.get('success') and r_lmk_subscriber.get('status_code') == 409:
                            print('Email subscriber already exists :',
                                  customer_email)

                        minioservice = MinioService()
                        file_url = minioservice.get_file_url(
                            product.get('minio_object_name'))
                        order_date = str(datetime.strptime(
                            order.get('date_created'), "%Y-%m-%dT%H:%M:%S.%fZ"))

                        # print('file_url', file_url)
                        email_data = {
                            "subscriber_email": customer_email,
                            "template_id": 4,
                            "data": {
                                "order_code": "#{}".format(order.get('code')),
                                "order_date": "20 Octobre 2024",
                                "order_date": order_date,
                                "product_name": product.get('name'),
                                "file_link": file_url
                            },
                            "content_type": "html"
                        }

                        r_lmk_email = listmonk_send_email(
                            env_vars=env_vars,
                            data=email_data
                        )

                        if r_lmk_email.get('success'):
                            print('Email sent to :', customer_email)

                            r_dts_upd_order = directus_update_order(
                                env_vars=env_vars,
                                order_id=str(order.get("id")),
                                data={
                                    "product_is_delivered": True,
                                    "date_delivered": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # "%Y-%m-%dT%H:%M:%S"
                                }
                            )
    except Exception as e:
        print('Error in treat_not_delivered:', e)

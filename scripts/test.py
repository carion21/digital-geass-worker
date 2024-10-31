from time import sleep, time
from joblib import Parallel, delayed
from datetime import datetime

from minioservice import MinioService

from constants import *
# from functions import *
from utilities import get_env_vars, listmonk_send_email, listmonk_create_subscriber

env_vars = get_env_vars()
logger = env_vars.get("logger")

email = "hyperformix3@gmail.com"

# subscriber_data = {
#     "email": email,
#     "name": "Hyper FORMIX",
#     "status": "enabled",
#     "lists": [
#         3
#     ]
# }

# r_lmk_subscriber = listmonk_create_subscriber(
#     env_vars=env_vars,
#     data=subscriber_data
# )

# print('r_lmk_subscriber', r_lmk_subscriber)

# email_data = {
#     "subscriber_email": email,
#     "template_id": 4,
#     "data": {
#         "order_code": "#123456",
#         "order_date": "20 Octobre 2024",
#         "product_name": "101 ASTUCES MARKETING",
#         "file_link": "https://minioproxy-production.up.railway.app/digital-geass/ed121b4d-eba1-4e9e-a8c5-8a2df5ca6549.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ORGkLmwYdnM8tdDeRpfx%2F20241031%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20241031T063718Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=feaecb0d2dc20aef08b42c7f5be63a26c2d595319cc399668ded32de68378c41"
#     },
#     "content_type": "html"
# }

# r_lmk_email = listmonk_send_email(
#     env_vars=env_vars,
#     data=email_data
# )

# object_name = "ed121b4d-eba1-4e9e-a8c5-8a2df5ca6549.pdf"

# minioservice = MinioService()

# print(minioservice.minio_proxy)

# file_url = minioservice.get_file_url(object_name)

# print('file_url', file_url)

dt = "2024-10-30T05:24:02.000Z"
# transformer en 30 Octobre 2024
fdt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%fZ")
print('fdt', fdt)

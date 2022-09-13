import requests

SERVER = 'https://erp.ephor.online'
PATH_TO_LOG = '/api/2.0/Auth.php'

data = {
    'action': 'Login',
    '_dc': 1518593389938,
    'login': '****',
    'password': '****',
    'time_zone': -3
}

req = requests.post(SERVER + PATH_TO_LOG, params=data)
print(req.text)

# https://erp.ephor.online/download/apiv2.pdf

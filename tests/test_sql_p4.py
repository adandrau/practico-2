import pytest
import random
import requests
from requests.utils import unquote
import quopri
import re

# crear token
MAILHOG_API = "http://localhost:8025/api/v2/messages"

def get_last_email_body():
    resp = requests.get(MAILHOG_API)
    resp.raise_for_status()
    data = resp.json()

    if not data["items"]:
        return None

    last_email = data["items"][0]
    body = last_email["Content"]["Body"]
    decoded = quopri.decodestring(body).decode("utf-8", errors="replace")
    return unquote(decoded)

def extract_links(decoded_html):
    return re.findall(r'<a\s+href=["\']([^"\']+)["\']', decoded_html, re.IGNORECASE)[0]

def extract_query_params(url):
    # regex: busca ?token= o &token= seguido de cualquier cosa hasta &, # o fin de string
    patron = re.compile(r"(?:[?&])token=([^&#]+)")
    m = patron.search(url)
    return m.group(1) if m else None

@pytest.fixture(autouse=True)
def setup_create_user():
    # random username
    i= random.randint(1000, 999999)
    username = f'user{i}'
    email = f'{username}@test.com'
    password = 'password'
    salida = requests.post("http://localhost:5500/users",
                        data={
                            "username": username, 
                            "password": password,
                            "email":email,
                            "first_name":"Name",
                            "last_name": f'{username}son'
                            })
    # user created
    assert salida.status_code == 201

    mail = get_last_email_body()
    link = extract_links(mail)
    token = extract_query_params(link)

    # activate user
    response = requests.post("http://localhost:5500/auth/set-password", json={"token": token, "newPassword": password})


    return [username,password]

def test_login(setup_create_user):
    username = setup_create_user[0]
    password = setup_create_user[1]

    print(f"Testing login for user: {username} with password: {password}")

    response = requests.post("http://localhost:5500/auth/login", json={"username": username, "password": password})

    print ("Response login:", response.text)
    auth_token = response.json()["token"]
    assert auth_token

def test_sql_injection(setup_create_user):
    # Demuestra que el parámetro 'operator' permite inyectar SQL y bypasear el control de acceso
    username = setup_create_user[0]
    password = setup_create_user[1]

    # Hacemos login para traernos el tokencito
    response = requests.post("http://localhost:5500/auth/login", 
                            json={"username": username, "password": password})
    auth_token = response.json()["token"]
    assert auth_token

    # Este es el payload que inyecta el SQL para traernos todas las facturas (jaja re argentino, yo quiero dulces)
    smooth_operator = "='paid' OR '1'='1' OR status="
    
    response = requests.get(
        "http://localhost:5500/invoices",
        params={
            "status": "paid",
            "operator": smooth_operator
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    
    las_facturas_del_dia = response.json()
    
    if len(las_facturas_del_dia) > 0:
        # Contar usuarios únicos
        user_ids = set(invoice.get('userId') for invoice in las_facturas_del_dia)
        print(f"Total de usuarios diferentes: {len(user_ids)}")
        
        assert len(user_ids) == 1, "SQL Injection fallida, se accedió a múltiples usuarios. Too bad"
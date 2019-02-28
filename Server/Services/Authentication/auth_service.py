import rpyc
import json
import jwt
import datetime
import psycopg2 as postg
import hashlib, base64
from rpyc.utils.server import ThreadedServer

conn = postg.connect(database="spa", user="spa", password="333xwx333", host="172.17.0.2")

secret = "tikitikitemponeserambocarıbururucineserambo"

class Auth_service(rpyc.Service):
    def _take_care_password(self, password, salt):
        hash_password = hashlib.pbkdf2_hmac("sha256", str.encode(password), str.encode(salt), 1024)
        hash_password = base64.encodebytes(hash_password)
        return hash_password.decode().strip()

    def exposed_add_new_user(self, data):
        cur = conn.cursor()

        hash_password = self._take_care_password(data["password"], data["email"])

        try:
            cur.execute("INSERT INTO spadb.people(password, name, lastname, school_no, email) VALUES (%s, %s, %s, %s, %s);", [
                hash_password,
                data["name"],
                data["lastname"],
                data["school_no"],
                data["email"]
                ])
        except Exception as e:
            conn.rollback()
            cur.close()
            return json.dumps({
                "success": False,
                "message": "An error occur on operation (Task failed successfully)",
            })
        
        conn.commit()
        cur.close()

        return json.dumps({
            "success": True,
            "message": "new user added successfully"
        })
        
    def exposed_get_token(self, data):
        secret = "tikitikitemponeserambocarıbururucineserambo"
        cur = conn.cursor()

        email = data["email"]
        password = data["password"]

        hash_password = self._take_care_password(password, email)

        cur.execute("SELECT * FROM spadb.people WHERE email = %s AND password = %s", [email, hash_password])
        rows = cur.fetchall()
        cur.close()

        response = []
        for row in rows:
            response.append(row)

        if len(response) == 0:
            return json.dumps({
                "success": False,
                "message": "Wrong email or password"
            })

        response = response[0]

        user_id = response[0]
        token = jwt.encode({
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
            "name": response[2],
            "lastname": response[3],
            "school_no": response[4],
            "expire_time": 2
        }, secret, algorithm="HS256")
        return json.dumps({
            "success": True,
            "token_type": "jwt",
            "token": token.decode()
        })

    def exposed_verify_token(self, token):
        try:
            payload = jwt.decode(token, secret, algorithms="HS256")
            return json.dumps({
                "success": True,
                "payload": payload
            })
        except jwt.ExpiredSignatureError as err:
            return json.dumps({
                "success": False,
                "message": "expired token"
            })
        except jwt.DecodeError as err:
            return json.dumps({
                "success": False,
                "message": "decode error"
            })
        # easter egg :)
        return json.dumps({
            "success": False,
            "message": "python failed successfully!"
        })

port = 7878
rypc_server = ThreadedServer(
    Auth_service,
    port=port
    )
rypc_server.start()
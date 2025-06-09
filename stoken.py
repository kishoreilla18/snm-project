from itsdangerous import URLSafeTimedSerializer
from keys import secret_key,salt
def entoken(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data,salt=salt)
def detoken(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.loads(data,salt=salt)
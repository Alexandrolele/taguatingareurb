import base64
import json

# Dados do Firebase preenchidos diretamente
dados_firebase = {
    "type": "service_account",
    "project_id": "taguatingareurb",
    "private_key_id": "de3da0acc2428550e944c54ddbcf74fc0acb1d95",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC+Knv+NMxZi9QJ\nFvme0Vr8Gqzgq4mmaCwv3Rx9jZpystErW2TZf1X3LcqohQ0VOWX8ClINc/c9albZ\n3C4mqT1GbjXMoKiim8qBPPbvsrpaE5c24P1drJsPtifN/dwRrWdvyMscwZt8McwyNU\nfPlV0KvDriJjh9r2VItzNe8ZRtRQIxFqq2MJXVPDllICC0kBspCqLQUAkdhLEBkN\nOeV3dFIXm6H+4C9WmCFQEuVg4I4RTDZ0RAawLgF/dnvnpGA1fADCSzKKYQuDFQdz\nrS6TEh8RVqa0FvcMfmHW3xkJ7bE9f+aNNWbSmAxRaNeV5fZzY7ws3+WkTAwBSYro\nRXk8YskXAgMBAAECggEABw+pyf8o5VxRU8MUIscQU1MkPzVvZ4vvtBlIQQs8hGzK\nYotCu+bECOkc4NQL79FRTaIOeOxo7lFgBzjCTgEUTb4cnXhhMd2avZjyXlGjbWN2\njbxKrWfYI61Mg+3zMqp5ZzoE46GUr6E5Ux5O3dZhQmNZaIu3YDU0dmM2zR/5qz4J\ntbZtd51g8dE+oMzc76IyGMnaivQ8JWRekmijVrsivVfEPldx7Jxdv9GcNeetgzfy\n7/9WRcZKZ9TSKLsdCK95x4I3n87OWvw2zzarWswWv5VGm+xgcDeRKXiMWyGwUYMD\ngJSaggoyv1bbC7ZDPmJ9MhIQuyhw0y6b12hTY3Hj8QKBgQDl5iJ3PIBsyXovTRSS\nlY+KVNYJBOkx95dP5F8J+RiYIrE+YP4rAyBHoiTky9jM3UrQHdAsd4rB2bWfMJSA\n2PX+QRoB8TATidhquNwGrhzxO+CNzosWitWsmIlXWmwvrKXw0fyB9G4C394hmYLu\nZMcKaAiEmuei1ML+wpTBKvsmBwKBgQDTwYkPWlF0qI+znN/Onk1ysHJahh+DYwoe\n+NzHC9pIczSY8N1Ov3nqmMy0NOQMbkoTShAYl5KORTXKgqUEC080hzBVkq0jVlR2\nE7Y3yGb/r7FNvOOFjX5F8JJDiK7aEa8yAALCnFdLZh3yrZ0NkIHpumY04ey/5aEA\nmZnploEAcQKBgQCLYkoHLMFYM5dG0l7kuJS8c88IzNdtmgU9ROJyM3o70tzPSxMO\nlOifRalEpmqdWpWfNFQggaG5AfvhthxzOhd6vZG9F7PkRLDXk5ii3DFj+L+eellN\no4MFD75FHed1yCEbrtR/HekNCRmuGVqOmr8qigSQETLbQE+xEdwKebqnRQKBgGfN\nUWCjR5bGIltLpTJly1VTRVs2sC/51rZEDAXOu5wUTU5DlFjL5/mmGYKlAr1NOyal\ngapscr0nFC1HSZjn6lW3h2wLULAn25NeKk7CACuKdoHC/E01hRbHzQsp73yaeqUp\n+DBp7yjY0AlsLba+hdCLPRrjPOj8qaXfpeEpk+chAoGBAL33I2KbquML8QcWu0rf\nsidazo2ukDcCmqfZ++0jrqXCAYt6G0gFzj6k5may7iMRp6/M5j96Rj8YN/nAan6A\nBln7zjRi5VKxLQ8dOYn7BZ5p4xJCicks4KgsrD4ZmzvgE039qnbC+P+G7QHjOXpI\n2xNLj1SVt0P4kf4lNVsSZDBZ\n-----END PRIVATE KEY-----",
    "client_email": "firebase-adminsdk-fbsvc@taguatingareurb.iam.gserviceaccount.com",
    "client_id": "101985816717023480615",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40taguatingareurb.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Converte para JSON e depois para Base64
json_str = json.dumps(dados_firebase)
base64_result = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

print("\n" + "="*50)
print("COPIE A LINHA ABAIXO PARA O SECRETS DO STREAMLIT CLOUD:")
print("="*50)
print(f'FIREBASE_BASE64 = "{base64_result}"')
print("="*50 + "\n")
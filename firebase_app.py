import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import cycle_time_analys as ana
import pandas as pd

def connect():
    data = load_data()
    cred = credentials.Certificate(data['file_path'])
    db_url = data['databaseURL']
    firebase_admin.initialize_app(cred, {
            'databaseURL': db_url
        })

def push_data(project):
    ref = db.reference('/')
    df = ana.get_issues_from(project)
    result = df.to_json(orient="index")
    parsed = json.loads(result)
    ref.set(parsed)

def get_data():
    connect()
    ref = db.reference("/")
    dic = ref.get()
    df = pd.DataFrame(dic)
    return df

def main():
    print('inicio main')
    print(get_data())

def load_data():
    try:
        with open('firebase_config.json', 'r') as j:
            data = json.load(j)
        return data
    except Exception as e:
        print("problema al abrir el archivo: {}".format(e))


if __name__ == "__main__":
    main()
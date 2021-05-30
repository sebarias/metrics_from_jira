import json
import requests
import sys
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sbn
import numpy as np
from datetime import datetime
from functools import reduce
import base64

todo = 'TO DO'
inprogress = 'In Progress'
bloqued = 'BLOQUEADO'
done = 'DONE'

def load_data():
    try:
        with open('jira_creds.json', 'r') as j:
            data = json.load(j)
        return data
    except Exception as e:
        print("problema al abrir el archivo de credenciales: {}".format(e))
    

def encode_creds():
    data = load_data()
    user = data['user']
    password = data['password']
    message = user + ":" + password
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message

def request_to_jira(uri,payload):
    base64creds = encode_creds()
    auth_jira = "Basic " + encode_creds()
    url = "http://jira.bch.bancodechile.cl:8080/rest/api/2/{}".format(uri)
    headers = {'Content-Type':'application/json', 'Authorization': auth_jira}
    querystring = {"":""}
    payload = json.dumps(payload, indent = 4)  
    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    #print(response.text)
    resultado = json.loads(response.text)
    return resultado
        

def request_to_jira_get(uri,payload = "", api = 2):
    base64creds = encode_creds()
    auth_jira = "Basic " + encode_creds()
    if api == 2:
        url = "http://jira.bch.bancodechile.cl:8080/rest/api/2/{}".format(uri)
    else:
        url = "http://jira.bch.bancodechile.cl:8080/rest/agile/1.0/{}".format(uri)
    #print(url)
    headers = {'Content-Type':'application/json', 'Authorization': auth_jira}
    response = requests.request("GET", url, data=payload, headers=headers)
    #print(response.text)
    results = json.loads(response.text)
    return results

def issues_to_dict(x):
    dic = {}
    dic['name'] = x['name']
    dic['id'] = x['id']
    dic['description']: x['description']
    dic['url'] = x['self']
    dic['subtask'] = x['subtask']
    return dic

def create_df_issuetypes():
    """
    crea un dataframe con los tipos de issues que existen en Jira
    """
    data = request_to_jira_get('issuetype')
    issues = list(map(issues_to_dict, data))
    df = pd.DataFrame(issues) 
    return df

def get_epics_from_proyect(proyect):
    #traeremos todas las epcias y nombres
    jql_epics = 'search?jql=project%20%3D%20{}%20AND%20issuetype%20%3D%20Epic&fields=summary'.format(proyect)
    data = request_to_jira_get(jql_epics, "", 2)
    issues = data['issues']
    epics = {}

    for issue in issues:
        epics[issue['key']] = issue['fields']['summary']
    return epics

def tasks_to_dict(x):
    dic = {}
    #print(x)
    dic['key'] = x['key']
    dic['id'] = x['id']
    dic['summary'] = x['fields']['summary']
    dic['url'] = x['self']
    dic['issuetype'] = x['fields']['issuetype']['name']
    dic['issuetype_id'] = x['fields']['issuetype']['id']
    dic['date_created'] = datetime.strptime(x['fields']['created'], '%Y-%m-%dT%H:%M:%S.%f%z')
    dic['date_resolution'] = datetime.strptime(x['fields']['resolutiondate'], '%Y-%m-%dT%H:%M:%S.%f%z')
    dic['story_points'] = x['fields']['customfield_10002']
    #print(x['fields']['assignee'])
    if 'assignee' not in x['fields'] or x['fields']['assignee'] == None:
        dic['assignee'] = None
        dic['assignee_full'] = None
        dic['assignee_active'] = None
    else:
        dic['assignee'] = x['fields']['assignee']['name']
        dic['assignee_full'] = x['fields']['assignee']['displayName']
        dic['assignee_active'] = x['fields']['assignee']['active']
    
    dic['status'] = x['fields']['status']['name']
    dic['status_id'] = x['fields']['status']['id']
    dic['resolution'] = x['fields']['resolution']['name']
    dic['resolution_id'] = x['fields']['resolution']['id']
    dic['lead_time'] = (dic['date_resolution'] - dic['date_created']).days
    #print('init date: ',dic['date_created'],'resolution date: ',dic['date_resolution'],'lead time: ', dic['lead_time'] )
    dic['labels'] = x['fields']['labels']
    if x['fields']['customfield_10005'] != None:
        dic['sprint_count'] = len(x['fields']['customfield_10005'])
    else:
        dic['sprint_count'] = 0
    if 'changelog' in x:
        if x['changelog'] != None:
            #print(dic['summary'])
            dic['statuses'], dic['quality'], dic['date_starting'] = changelog_transform(x['changelog'])
            dic['cycle_time'] = (dic['date_resolution'] - dic['date_starting']).days
        else:
            dic['statuses'] = []
            dic['quality'] = None
            dic['date_starting'] = None
            dic['cycle_time']  = None
    #print(dic)
    return dic

def issue_is_starting(status_from,status_to):
    return (status_from == todo and status_to == inprogress) or \
        (status_from == todo and status_to == done) or \
            (status_from == todo and status_to == bloqued)

def quality(status_from,status_to):
    if status_from == status_to:
        return 0
    if (status_from == todo and status_to == inprogress) or \
        (status_from == inprogress and status_to == done):
        return 0
    else:
        return 1

def get_status_history(history):
    dict = {}
    date_created = datetime.strptime(history['created'], '%Y-%m-%dT%H:%M:%S.%f%z')
    items = history['items']
    if items != None:
        if items[0]['field'] == 'status' or items[0]['field'] == 'resolution':
            find = False
            for item in items:
                it = {}
                if item['field'] == 'status':
                    it['from'] = item['fromString']
                    it['to'] = item['toString']
                    it['date_created'] = date_created
                    it['quality'] = quality(it['from'], it['to'])
                    it['is_starting'] = False
                    if not find:
                        find = issue_is_starting(it['from'],it['to'])
                        it['is_starting'] = find
                    return it
    return None

def changelog_transform(changelog):
    histories = changelog['histories']
    if len(histories) > 0:
        statuses = list(filter(lambda x : (x!= None), list(map(get_status_history, histories))))
        total = reduce(lambda x, y: x + y['quality'], statuses, 0)
        date_start = list(filter(lambda x : (x['is_starting'] == True), statuses))[0]['date_created']
        
        # print("statuses: ",statuses)
        # print("quality: ",total)
        # print("start: ", date_start)
    return statuses, total, date_start


def create_request_dict(jql,start_at,max_results,expand = ["changelog"]):
    fields = ["id","key","resolution","assignee","issuetype",
    "status","progress", "project", "resolutiondate", "summary",
     "created", "updated", "customfield_10005","customfield_10002", 
     "aggregateprogress", "self", "labels"]
    rq = {}
    rq['jql'] = jql
    rq['startAt'] = start_at
    rq['maxResults'] = max_results
    rq['fields'] = fields
    rq['expand'] = expand
    return rq

def get_issues_from(project):
    jql = "project = {} and issuetype = Task and status = Done".format(project)
    start_at = 0
    total = 1
    size = 50
    max_results = size
    issues = []
    expand = ["changelog"]
    while total > start_at:
        print("start at: ", start_at)
        payload = create_request_dict(jql,start_at,max_results,expand)
        data = request_to_jira('search',payload)
        total = int(data['total'])
        start_at += size
        #total = 0
        issues_add = list(map(tasks_to_dict, data['issues']))
        if len(issues) == 0:
            issues = issues_add
        else:
            issues.extend(issues_add)
            
    df = pd.DataFrame(issues) 
    return df


def main():
    print('inicio main')
    print(get_issues_from('JET'))

if __name__ == "__main__":
    main()
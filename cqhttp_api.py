import json

import requests

url = "http://127.0.0.1:5700/"

headers = {
    'Content-Type': 'application/json',
}

retries = 3


def sent_private_msg(user_id, message):
    payload = {
        "action": "send_private_msg",
        "params": {
            "user_id": user_id,
            "message": message,
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(response.status_code)
    return response.json()


def send_group_msg(group_id, message):
    payload = {
        "action": "send_group_msg",
        "params": {
            "group_id": group_id,
            "message": message,
        }
    }
    for i in range(retries):
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response = response.json()
        if response['status'] == 'failed':
            print(response)
            continue
        return response


def send_group_forward_msg(group_id, messages, name, uin):
    build_messages = []
    for messages in messages:
        build_messages.append({
            "type": "node",
            "data": {
                "name": name,
                "uin": uin,
                "content": messages
            }
        })
    payload = {
        "action": "send_group_forward_msg",
        "params": {
            "group_id": group_id,
            "messages": build_messages
        }
    }
    for i in range(retries):
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response = response.json()
        if response['status'] == 'failed':
            print(response)
            continue
        return response


def send_private_forward_msg(user_id, messages, name, uin):
    build_messages = []
    for messages in messages:
        build_messages.append({
            "type": "node",
            "data": {
                "name": name,
                "uin": uin,
                "content": messages
            }
        })
    payload = {
        "action": "send_private_forward_msg",
        "params": {
            "user_id": user_id,
            "messages": build_messages
        }
    }
    for i in range(retries):
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response = response.json()
        if response['status'] == 'failed':
            print(response)
            continue
        return response


def cq_parse_image(abs_path):
    path = 'output'
    temp = abs_path.split('\\')
    for i in range(len(temp)):
        if temp[i] == 'output':
            for j in range(i + 1, len(temp)):
                path += '\\' + temp[j]

    return "[CQ:image,file=" + path + "]"


if __name__ == '__main__':
    _messages = [cq_parse_image("output\\1688544766\\0.jpg"), cq_parse_image("output\\1688544778\\0.jpg")]

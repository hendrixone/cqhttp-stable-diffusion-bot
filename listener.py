import random

from flask import Flask, request

from message import MessageProcessor, replace_chinese_characters, rebuild_request_msg
from sd_api import SdApi
from cqhttp_api import send_group_msg, cq_parse_image, send_group_forward_msg

app = Flask(__name__)

prompt_regex = r"(?<=瑟图:)\s*(.*)"
params_regex = r'^(.*?)(?=瑟图:)'
sensitive_keywords = ['nude', 'nsfw', 'naked', 'nudity', 'nake']

nickname = 'one:'
self_name = 'one'

# 敏感内容检测阈值，越低越严格
censor_level = 0.6

reachieved_message = ["脑瓜子飞速运转中",
                      "正在努力了脑补中", "身体热起来了~", "身体里面，好热~", "显存被完全填满了呢", "要出来了~", "嗯~~",
                      "好大的词条", "词条进来了...!"]
nsfw_message = ["不可以色色", "这个图不太行捏", "过于劲爆，不宜展示", "这个图发不出来你不反思一下吗！", "自由，民主，公正，法制"]

api = SdApi()

message_processor = MessageProcessor()


# 瑟图接口
@app.route('/', methods=['POST'])
def handle_request():
    group_id = [717392613]

    if request.method == 'POST':
        # Handle POST request
        data = request.get_json()  # Get JSON data from the request

        if data['post_type'] != 'message':
            return 'ok'
        message = data['message']
        if data['message_type'] == 'group' and data['group_id'] in group_id:
            current_request_id = data['group_id']

            # check if sensitive keyword exist in extracted_content
            if any(keyword in message for keyword in sensitive_keywords):
                print(send_group_msg(current_request_id, nickname + '达咩,不可以色色'))
                return 'ok'

            print(message)
            params = message_processor.process_message(message)
            print(params)
            if not params['valid']:
                # 解读失败
                print('解读失败')
                return 'ok'
            else:
                if len(message) > 100:
                    send_group_msg(current_request_id, nickname + '字数太长了，缩短点再试试吧')
                    return 'ok'
                # 发送请求收到确认
                i = random.randint(0, len(reachieved_message) - 1)
                print(send_group_msg(current_request_id, nickname +
                                     reachieved_message[i] + ' (' + rebuild_request_msg(params) + ')'))
                response = api.get_image(params)

                return process_images(response, current_request_id)

        # print('Received a POST request with JSON data: {}'.format(data))
        return 'ok'


def process_images(response, current_request_id):
    messages = []
    for img in response:
        for key, value in img.items():
            path = key[-23:]
            pred = value
            print('-----------------------------------')
            print(pred)
            print('-----------------------------------')
            if pred['hentai'] > 0.6 or pred['sexy'] > 0.6 or pred['porn'] > 0.6:
                # 发送审核失败信息
                i = random.randint(0, len(nsfw_message) - 1)
                send_group_msg(current_request_id, nickname + nsfw_message[i])
                return 'ok'
            messages.append(cq_parse_image(path))

    print(send_group_forward_msg(current_request_id, messages, '小万', '1145141919'))
    return 'ok'


if __name__ == '__main__':
    app.run(port=5701)
    # print(parse_request("瑟图：女孩子"))

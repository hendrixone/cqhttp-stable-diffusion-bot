import random

from flask import Flask, request

from NSFW_Detector import predict
from message import MessageProcessor, rebuild_request_msg
from sd_api import SdApi
from cqhttp_api import *

app = Flask(__name__)

prompt_regex = r"(?<=瑟图:)\s*(.*)"
params_regex = r'^(.*?)(?=瑟图:)'
sensitive_keywords = ['nude', 'nsfw', 'naked', 'nudity']

nickname = 'bot:'
self_name = '小万'
fake_id = '1145141919'

# 敏感内容检测阈值，越低越严格
censor_level = 0.5

enable_keywords_check = False

words_limit = 180

received_message = ["脑瓜子飞速运转中",
                    "正在努力了脑补中", "身体热起来了~", "身体里面，好热~", "显存被完全填满了呢", "要出来了~", "嗯~~",
                    "好大的词条", "词条进来了...!"]
nsfw_message = ["不可以色色", "这个图不太行捏", "过于劲爆，不宜展示", "这个图发不出来你不反思一下吗！",
                "自由，民主，公正，法制"]

whitelist = json.load(open('whitelist.json'))
group_id = whitelist['group_id']
private_id = whitelist['private_id']

api = SdApi()

message_processor = MessageProcessor()

model = predict.load_model('./NSFW_Detector/mobilenet_v2_140_224')


# 瑟图接口
def process_group_request(data):
    message = data['message']
    current_request_id = data['group_id']

    # check if sensitive keyword exist in extracted_content
    if enable_keywords_check and any(keyword in message for keyword in sensitive_keywords):
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
        if len(message) > words_limit:
            send_group_msg(current_request_id, nickname + '字数太长了，缩短点再试试吧')
            return 'ok'
        # 发送请求收到确认
        i = random.randint(0, len(received_message) - 1)
        print(send_group_msg(current_request_id, nickname +
                             received_message[i] + ' (' + rebuild_request_msg(params) + ')'))
        response = api.get_image(params)

        response_msg = process_images_to_msg(response, current_request_id)
        if not response_msg:
            i = random.randint(0, len(nsfw_message) - 1)
            send_group_msg(current_request_id, nickname + nsfw_message[i])
        else:
            print(send_group_forward_msg(current_request_id, response_msg, self_name, fake_id))

        return 'ok'


def process_private_request(data):
    current_request_id = data['user_id']
    message = data['message']
    print(message)
    params = message_processor.process_message(message)
    print(params)
    if not params['valid']:
        # 解读失败
        print('解读失败')
        return 'ok'
    else:
        # 发送请求收到确认
        print(sent_private_msg(current_request_id, nickname +
                               '收到请求' + ' (' + rebuild_request_msg(params) + ')'))
        images_list = api.get_image(params)

        response_msg = process_images_to_msg(images_list, enable_nsfw_filter=False)

        print(send_private_forward_msg(current_request_id, response_msg, self_name, fake_id))
    return 'ok'


@app.route('/', methods=['POST'])
def handle_request():

    if request.method == 'POST':
        # Handle POST request
        data = request.get_json()  # Get JSON data from the request

        if data['post_type'] != 'message':
            return 'ok'

        if data['message_type'] == 'group' and data['group_id'] in group_id:
            process_group_request(data)

        if data['message_type'] == 'private':
            if '来点瑟图' in data['message']:
                if data['user_id'] not in private_id:
                    sent_private_msg(data['user_id'], '还没被加入白名单捏，稍等哦')
                    return 'ok'
                process_private_request(data)

        return 'ok'


def process_images_to_msg(image_list, enable_nsfw_filter=True):
    messages = []
    for img_path in image_list:
        if enable_nsfw_filter:
            # classify the image
            for key, value in predict.classify(model, img_path).items():
                path = key
                pred = value
                if pred['hentai'] > censor_level or pred['sexy'] > censor_level or pred['porn'] > censor_level:
                    return False
                messages.append(cq_parse_image(path))
        else:
            messages.append(cq_parse_image(img_path))

    return messages


if __name__ == '__main__':
    app.run(port=5701)
    # print(parse_request("瑟图：女孩子"))

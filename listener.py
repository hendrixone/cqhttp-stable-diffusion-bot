import json
import random
import time
import re
import traceback

from flask import Flask, request

from NSFW_Detector import predict
from message import MessageProcessor
from sd_api import SdApi
from cqhttp_api import *

app = Flask(__name__)

nickname = 'bot:'
self_name = '小万'
fake_id = '1145141919'

# Block sensitive keywords
enable_keywords_check = False
sensitive_keywords = ['nude', 'nsfw', 'naked', 'nudity']

# Prompt words limit 0 for no limit
words_limit = 1000

received_message = ["脑瓜子飞速运转中",
                    "正在努力了脑补中", "身体热起来了~", "身体里面，好热~", "显存被完全填满了呢", "要出来了~", "嗯~~",
                    "好大的词条", "词条进来了...!"]
nsfw_message = ["不可以色色", "这个图不太行捏", "过于劲爆，不宜展示", "这个图发不出来你不反思一下吗！",
                "自由，民主，公正，法制"]

# Load whitelist from local json file
whitelist = json.load(open('whitelist.json'))
group_id = whitelist['group_id']
private_id = whitelist['private_id']

# Initialize Stable Diffusion API
api = SdApi()

message_processor = MessageProcessor()

model = predict.load_model('./NSFW_Detector/mobilenet_v2_140_224')


# 瑟图接口
def process_group_request(data):
    message = data['message']
    current_request_id = data['group_id']

    group_config = json.load(open('whitelist.json'))['group_id'][current_request_id]

    if not group_config['enable']:
        return 'ok'

    print(message)

    if message == '#食用指南':
        with open("manual.txt", "r") as file:
            print(send_group_msg(current_request_id, file.read()))
        return 'ok'
    
    params = message_processor.process_message(message)
    print(params)
    # Check if params is str, if it's string, it means the process failed
    if isinstance(params, str):
        print(send_group_msg(current_request_id, params))
        return 'ok'
    if not params['valid']:
        # 解读失败
        print('解读失败')
        return 'ok'
    else:
        if words_limit != 0 and len(message) > group_config['words_limit']:
            send_group_msg(current_request_id, nickname + '字数太长了，缩短点再试试吧')
            return 'ok'

        # check if sensitive keyword exist in extracted_content
        if enable_keywords_check and any(keyword in message for keyword in sensitive_keywords):
            print(send_group_msg(current_request_id, nickname + '达咩,不可以色色'))
            return 'ok'

        # 发送请求收到确认
        i = random.randint(0, len(received_message) - 1)
        print(send_group_msg(current_request_id, nickname +
                             received_message[i] + ' (' + message_processor.rebuild_request_msg(params) + ')'))

        # calculate time taken
        start_time = time.time()
        try:
            image_list = api.get_image(params)
        except Exception as e:
            print(e)
            send_group_msg(current_request_id, nickname + str(e))
            return 'ok'

        api_time_taken = time.time() - start_time

        response_msg = process_images_to_msg(image_list, api_time_taken, group_config['nsfw_filter'])
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
    # Check if params is str
    if isinstance(params, str):
        print(sent_private_msg(current_request_id, params))
        return 'ok'
    if not params['valid']:
        # 解读失败
        print('解读失败')
        return 'ok'
    else:
        # 非白名单提示
        if data['user_id'] not in private_id:
            sent_private_msg(data['user_id'], '还没被加入白名单捏，稍等哦')
            return 'ok'
        # 发送请求收到确认
        print(sent_private_msg(current_request_id, nickname +
                               '收到请求' + ' (' + message_processor.rebuild_request_msg(params) + ')'))
        # calculate time taken
        start_time = time.time()

        try:
            image_list = api.get_image(params)
        except Exception as e:
            traceback.print_exc()
            sent_private_msg(current_request_id, nickname + str(e))
            return 'ok'

        api_time_taken = time.time() - start_time

        response_msg = process_images_to_msg(image_list, api_time_taken, enable_nsfw_filter=False)

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
            process_private_request(data)

        return 'ok'


def process_images_to_msg(image_list, api_time_taken, censor_level):
    messages = []
    for img_path in image_list:
        if censor_level != 0:
            # classify the image
            for key, value in predict.classify(model, img_path).items():
                path = key
                pred = value
                print(pred)
                if pred['hentai'] > censor_level or pred['porn'] > censor_level:
                    return False
                messages.append(cq_parse_image(path))
        else:
            messages.append(cq_parse_image(img_path))

    # Append Additional Info
    messages.append(generate_info(api_time_taken, image_list))

    # Append guide message
    messages.append("查看指北文件获取更多用法！")

    return messages


def generate_info(time_taken, image_list):
    """
    Add Stable Diffusion Generation info for the message
    :param time_taken:
    :param image_list:
    :return:
    """
    info = api.last_gen_info

    # Extract the model
    pattern = r'Model:\s(.*?),'
    matches = re.findall(pattern, info['infotexts'][0])
    model_used = matches[0]

    message = (f"生成用时：{time_taken:.1f}秒\n"
               f"使用模型：{model_used}\n\n"
               f"正面提示词：{info['prompt']}\n\n"
               f"负面提示词：{info['negative_prompt']}\n")

    # Generate id for each image
    for path in image_list:
        img_path = path.split('\\')
        img_index = int(img_path[-1][0]) + 1
        img_id = img_path[-2] + '-' + str(img_index)
        message += f"\n图片{img_index}：{img_id}"
    return message


if __name__ == '__main__':
    app.run(port=5701)
    # print(parse_request("瑟图：女孩子"))

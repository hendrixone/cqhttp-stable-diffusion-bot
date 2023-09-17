import json
import re
from os import path

base_url = "C:\\Users\\77431\\Desktop\\QQ\\data\\images\\output"


def replace_chinese_characters(text):
    chinese_chars = '()：；，。'
    english_chars = '():;,.'

    translation_table = str.maketrans(chinese_chars, english_chars)
    translated_text = text.translate(translation_table)

    return translated_text


class MessageProcessor:
    def __init__(self):
        self.params_regex = None
        self.prompt_regex = None
        self.config = None
        self.active_profile = {}
        self.base_param = {
            'valid': False,
            'res': 0,
            'true': False,
            'multi': False,
            'prompt': '',
            'canvas': 'square'
        }
        self.param = self.base_param
        self.process_config()
        self.construct_regex()

    def process_config(self):
        # Read the active profile into a dictionary
        with open('configs.json') as f:
            self.config = json.load(f)
            for profile, profile_config in self.config.items():
                if profile_config['active']:
                    self.active_profile[profile] = profile_config['keyword']

    def construct_regex(self):
        keywords = "|".join(self.active_profile.values())
        self.prompt_regex = rf'({keywords}\s*)(.*)'
        self.params_regex = rf'^(.*?)(?={keywords}:)'

    def extract_prompt(self, message):
        prompt_match = re.search(self.prompt_regex, message)
        if prompt_match:
            self.param['prompt'] = prompt_match.group(2)[1:]

    def extract_params(self, message):
        params_match = re.search(self.params_regex, message)
        if params_match:
            params = params_match.group(1)
            self.process_resolution(params)
            self.process_truth(params)
            self.process_multi(params)
            self.process_redraw_strength(params)
            self.process_profile(message)
            self.process_canvas(params)

    def process_canvas(self, params):
        if "肖像" in params:
            self.param['canvas'] = 'portrait'
        elif "风景" in params:
            self.param['canvas'] = 'landscape'

    def process_resolution(self, params):
        if "高清" in params:
            self.param['res'] = 1
        elif "超清" in params:
            self.param['res'] = 2
        else:
            self.param['res'] = 0

    def process_truth(self, params):
        self.param['true'] = "真" in params

    def process_multi(self, params):
        self.param['multi'] = "多来点" in params

    def process_redraw_strength(self, params):
        if "中度" in params:
            self.param['redraw_strength'] = 2
        elif '重度' in params:
            self.param['redraw_strength'] = 3
        else:
            self.param['redraw_strength'] = 1

    def process_profile(self, message):
        for profile_name, keyword in self.active_profile.items():
            if keyword + ':' in message:
                self.param['profile'] = profile_name
                return

    def process_message(self, message):
        message = replace_chinese_characters(message)
        self.param = self.base_param.copy()
        # TODO Making them dynamically load from the profile json
        if any(keyword in message for keyword in self.active_profile.values()):
            self.extract_prompt(message)
            if self.param['prompt'] != '':
                self.param['valid'] = True
            else:
                return '亲，你的提示词呢？'
            self.param['type'] = 'text2img'
            self.extract_params(message)
        if "重绘瑟图:" in message:
            self.extract_img_path_and_prompt(message)
            if self.param['prompt'] != '':
                # check if file exits
                if path.exists(self.param['img_path']):
                    self.param['valid'] = True
                else:
                    return '图片不存在'
            self.param['type'] = 'img2img'

        return self.param

    def extract_img_path_and_prompt(self, message):
        img_id_regex = r"(?<=重绘瑟图:)\s*(.*)"
        img_id_match = re.search(img_id_regex, message)
        if img_id_match:
            img_id = img_id_match.group(1).split('-')
            self.param['img_path'] = path.join(base_url, img_id[0], str(int(img_id[1]) - 1) + '.jpg')
            with open(path.join(base_url, img_id[0], 'prompt.txt'), 'r') as f:
                self.param['prompt'] = f.read()
            self.param['valid'] = True

    def rebuild_request_msg(self, params):
        out = ''
        # 双重校验
        if params['multi']:
            out += '更多'
        if params['true']:
            out += '真'

        if params['res'] == 1:
            out += '高清'
        elif params['res'] == 2:
            out += '超清'

        out += self.config[params['profile']]['keyword']

        return out


if __name__ == '__main__':
 pass
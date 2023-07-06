import re


def replace_chinese_characters(text):
    chinese_chars = '()：；，。'
    english_chars = '():;,.'

    translation_table = str.maketrans(chinese_chars, english_chars)
    translated_text = text.translate(translation_table)

    return translated_text


def rebuild_request_msg(params):
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

    if params['random'] == 0:
        out += '随机'
    elif params['random'] == 2:
        out += '严格'

    out += '瑟图'

    return out


class MessageProcessor:
    def __init__(self):
        self.param = {
            'valid': False,
            'res': 0,
            'true': False,
            'multi': False,
            'random': 1,
            'prompt': ''
        }
        self.prompt_regex = r"(?<=瑟图:)\s*(.*)"
        self.params_regex = r'^(.*?)(?=瑟图:)'

    def extract_prompt(self, message):
        prompt_match = re.search(self.prompt_regex, message)
        if prompt_match:
            self.param['prompt'] = prompt_match.group(1)

    def extract_params(self, message):
        params_match = re.search(self.params_regex, message)
        if params_match:
            params = params_match.group(1)
            self.process_resolution(params)
            self.process_truth(params)
            self.process_multi(params)
            self.process_random(params)

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

    def process_random(self, params):
        if "随机" in params:
            self.param['random'] = 0
        elif "严格" in params:
            self.param['random'] = 2
        else:
            self.param['random'] = 1

    def process_message(self, message):
        message = replace_chinese_characters(message)
        if "瑟图:" in message:
            self.param['valid'] = True
            self.extract_prompt(message)
            self.extract_params(message)
        else:
            self.param['valid'] = False

        return self.param


if __name__ == '__main__':
    p = MessageProcessor()
    print(p.process_message('瑟图: loli'))

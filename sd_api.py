import base64
import json

import requests

from image import ImageProcessor
from PIL import Image

config_list = json.load(open('configs.json'))

url = "http://127.0.0.1:7860"

avoid_nsfw_prompt = '{nsfw, nude}, '

available_canvas_size = {
    "portrait": (1, 1.5),
    "landscape": (1.5, 1),
    "square": (1, 1)
}


class SdApi:
    def __init__(self):
        self.config = None
        self.image_processor = ImageProcessor(20)
        self.last_gen_info = None

    def get_image(self, params):
        """
        :param params:
        :return: A list containing the path of generated images
        """

        # load profile
        profile = params['profile']
        self.config = config_list[profile]

        if params['type'] == 'text2img':
            return self.get_text2img(params)
        elif params['type'] == 'img2img':
            return self.get_img2img(params)

    def get_text2img(self, params):
        prompt = params['prompt']

        size = available_canvas_size[params['canvas']]
        width = self.config['base_size'] * size[0]
        height = self.config['base_size'] * size[1]

        # By default, hr fix is disabled, for res value 0. The hr_fix will be activated depending on the profile
        enable_hr_fix = False
        hr_scale = 1
        if params['res'] == 1:
            enable_hr_fix = self.config['high_res_for'][0]
            hr_scale = self.config['high_res_multiplier'][0]
            # is hr_fix is not enabled, will increase the raw size for higher raw size
            if not enable_hr_fix:
                width *= self.config['high_res_multiplier'][0]
                height *= self.config['high_res_multiplier'][0]
        elif params['res'] == 2:
            # Apply higher raw resolution and highres fix at same time for better quality
            enable_hr_fix = self.config['high_res_for'][1]
            hr_scale = self.config['high_res_multiplier'][1]
            width *= self.config['high_res_multiplier'][1]
            height *= self.config['high_res_multiplier'][1]

        batch_size = 1
        if params['multi']:
            if params['res'] == 1:
                batch_size = self.config['batch_size'][1]
            elif params['res'] == 2:
                batch_size = self.config['batch_size'][2]
            else:
                batch_size = self.config['batch_size'][0]

        negative = avoid_nsfw_prompt + self.config['base_negative']
        if params['true']:
            negative = self.config['base_negative']

        override_settings = {
            "CLIP_stop_at_last_layers": self.config['CLIP'],
            "sd_vae": self.config['VAE'],
            "sd_model_checkpoint": self.config['checkpoint']
        }

        payload = {
            "prompt": self.config['base_prompt'] + prompt,
            "negative_prompt": negative,
            "steps": self.config['step'],
            "sampler_name": self.config['sampler_name'],
            "batch_size": batch_size,
            "width": width,
            "height": height,
            "enable_hr": enable_hr_fix,
            "denoising_strength": self.config['high_res_denoise'],
            "hr_scale": hr_scale,
            "hr_second_pass_steps": self.config['hr_steps'],
            "hr_upscaler": self.config['hr_upscaler'],
            "cfg_scale": self.config['cfg_scale'],
            "override_settings": override_settings,
        }

        if self.config['after_detail']:
            payload['alwayson_scripts'] = {
                "ADetailer": {
                    "args": [
                        {
                            'ad_model': 'face_yolov8s.pt',
                        }
                    ]
                }
            }

        response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload).json()

        if isinstance(response, str):
            print(response)
            return "API炸掉力"
        else:
            print(response['parameters'])

        self.last_gen_info = json.loads(response['info'])

        return self.image_processor.handle_images(response, self.config['base_prompt'] + prompt)

    def get_img2img(self, params):
        # Preprocess input Image
        image_path = params['img_path']
        with open(image_path, 'rb') as file:
            image_data = file.read()
        encoded_image = base64.b64encode(image_data).decode('utf-8')

        raw_width, raw_height = Image.open(image_path).size

        if raw_width > 768:
            raise Exception('图太大力，请不要选择高分辨率图片')

        hr_scale = 1
        if params['res'] == 1:
            hr_scale = 1.5
        elif params['res'] == 2:
            hr_scale = 2
        hr_script = {
            "script_name": "SD upscale",
            "script_args": [
                "", 64, "4x-UltraSharp", hr_scale
            ]
        }

        denoising_strength = 0.3
        if params['redraw_strength'] == 2:
            denoising_strength = 0.5
        elif params['redraw_strength'] == 3:
            denoising_strength = 0.75

        override_settings = {
            "CLIP_stop_at_last_layers": 2,
            "sd_vae": 'None'
        }

        payload = {
            "init_images": [encoded_image],
            "prompt": params['prompt'],
            "negative_prompt": '',
            "steps": 27,
            "sampler_name": "DPM++ SDE Karras",
            "batch_size": 3,
            "width": raw_width * hr_scale,
            "height": raw_height * hr_scale,
            "denoising_strength": denoising_strength,
            "cfg_scale": 7,
            "override_settings": override_settings,
        }
        if hr_scale > 1:
            payload.update(hr_script)

        response = requests.post(url=f'{url}/sdapi/v1/img2img', json=payload).json()

        if 'parameters' in response:
            print(response['parameters'])
        else:
            print(response)

        print(response['info'])

        self.last_gen_info = json.loads(response['info'])

        return self.image_processor.handle_images(response, params['prompt'])


if __name__ == '__main__':
    test_prompt = "1girl, Hatsune Miku, charm, lift up the breast,silk stockings, wetted clothes,coquettish"
    sd_api = SdApi()
    print(sd_api.get_image(test_prompt))

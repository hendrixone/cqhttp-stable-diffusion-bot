import requests

from image import ImageProcessor

url = "http://127.0.0.1:7860"

default_negative = 'EasyNegative, negative_hand-neg, nsfw, nude'
# base_prompt = 'masterpiece, best quality,(SFW), '
override_settings = {
    "CLIP_stop_at_last_layers": 2
}
base_prompt = 'masterpiece, best quality,'
base_negative = 'EasyNegative, negative_hand-neg,'


class SdApi:
    def __init__(self):
        self.image_processor = ImageProcessor(20)

    def get_image(self, params):
        prompt = params['prompt']

        hr_scale = 1.5
        if params['res'] == 1:
            hr_scale = 2
        elif params['res'] == 2:
            hr_scale = 2.5

        batch_size = 1
        if params['multi']:
            batch_size = 2

        cfg_scale = 7
        if params['random'] == 0:
            cfg_scale = 5
        elif params['random'] == 2:
            cfg_scale = 9

        negative = default_negative
        if params['true']:
            negative = 'EasyNegative, negative_hand-neg'

        payload = {
            "prompt": base_prompt + prompt,
            "negative_prompt": negative,
            "steps": 30,
            "sampler_name": "DPM++ SDE Karras",
            "batch_size": batch_size,
            "width": 512,
            "height": 512,
            "enable_hr": True,
            "denoising_strength": 0.3,
            "hr_scale": hr_scale,
            "hires_steps": 25,
            "hr_upscaler": "R-ESRGAN 4x+",
            "cfg_scale": cfg_scale,
            "override_settings": override_settings,
        }

        response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)

        r = response.json()

        print(r['parameters'])

        return self.image_processor.handle_images(r)


if __name__ == '__main__':
    test_prompt = "1girl, Hatsune Miku, charm, lift up the breast,silk stockings, wetted clothes,coquettish"
    sd_api = SdApi()
    print(sd_api.get_image(test_prompt))

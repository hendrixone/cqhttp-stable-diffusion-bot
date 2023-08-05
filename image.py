import base64
import io
import os
import shutil
import time

from PIL import Image


class ImageProcessor:
    def __init__(self, cache_num):
        self.cache_num = cache_num

    def handle_images(self, response, prompt):
        """
        :param prompt:
        :param response: SD_API response
        :return: A list containing the path of generated image
        """
        base_dir = "C:\\Users\\77431\\Desktop\\QQ\\data\\images\\output"  # Define your base directory here

        # ChatGPT Generation ⬇

        # create a unique folder for each invocation using timestamp
        folder_name = str(int(time.time()))
        os.makedirs(os.path.join(base_dir, folder_name), exist_ok=True)

        # Get a list of all the existing folders and sort them by creation time
        folders = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))],
                         key=lambda d: os.path.getmtime(os.path.join(base_dir, d)))

        # If the number of folders exceeds cache_num, delete the oldest one
        while len(folders) > self.cache_num:
            oldest_folder = folders.pop(0)
            shutil.rmtree(os.path.join(base_dir, oldest_folder))

        # Save images to the new folder
        results = []
        for index, i in enumerate(response['images']):
            image_path = os.path.join(base_dir, folder_name, f'{index}.jpg')
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
            image.save(image_path)
            results.append(image_path)

        # Save the prompt as a txt file along with the images
        with open(os.path.join(base_dir, folder_name, 'prompt.txt'), 'w', encoding='utf-8') as f:
            f.write(prompt)

        return results

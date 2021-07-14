import os
import requests
from dotenv import load_dotenv
from tqdm import tqdm
import logging
import json

YA_DISK_FOLDER = 'test_folder'
logging.basicConfig(filename='sample_logger.log', level=logging.INFO)


def save_files_info_to_json(info):
    with open('files_info.json', 'w', encoding='utf-8') as file:
        json.dump(info, file, indent=2)


def get_max_photo_size(photos_info):
    photo_sizes = ['w', 'z', 'y', 'r', 'q', 'p', 'o', 'x', 'm', 's']
    for size in photo_sizes:
        for photo_info in photos_info:
            if photo_info['type'] == size:
                return photo_info['url'], photo_info['type']


def get_user_profile_photos_info(vk_api_token, vk_api_version):
    user_photos_info = []
    files_info_to_json = []
    likes = []
    url = f'https://api.vk.com/method/photos.get/'
    params = {
        'access_token': vk_api_token,
        'v': vk_api_version,
        'album_id': 'profile',
        'photo_sizes': 1,
        'extended': 1
        }
    response = requests.get(url, params=params).json()
    if 'error' in response:
        logging.error(response['error'])
        raise requests.HTTPError(response['error'])

    for item in response['response']['items']:
        likes_count = item['likes']['count']
        if not likes_count in likes:
            file_name = str(likes_count)
        else:
            file_name = f"{likes_count}_{item['date']}"
        likes.append(likes_count)
        link, size = get_max_photo_size(item['sizes'])
        photo_info = {
            'file_name': file_name,
            'link': link
            }
        file_info_to_json = {
            'file_name': file_name,
            'size': size
            }
        user_photos_info.append(photo_info)
        files_info_to_json.append(file_info_to_json)

    return user_photos_info, files_info_to_json


def create_ya_disk_folder(folder_name, token):
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    params = {
        'path': folder_name
        }
    headers = {'Authorization': f'OAuth {token}'}
    response = requests.put(url, params=params, headers=headers)
    if 'error' in response.json():
        logging.error(f"{response.json()['message']}")
    response.raise_for_status()


def get_ya_disk_upload_url(ya_disk_token, file_name):
    url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {'path': f"{YA_DISK_FOLDER}/{file_name}"}
    headers = {'Authorization': f'OAuth {ya_disk_token}'}
    response = requests.get(url, params=params, headers=headers)
    if 'error' in response.json():
        logging.error(f"{response.json()['message']}")
    response.raise_for_status()
    data = response.json()
    link = data['href']

    return link


def upload_file(ya_url, photo_url, file_name):
    response = requests.get(photo_url)
    response.raise_for_status()
    file = response.content
    files = {'file': file}
    response = requests.put(ya_url, files=files)
    response.raise_for_status()
    if response.status_code == 201 and response.ok:
        logging.info(f'Файл {file_name} успешно сохранен на яндекс диске!')
    else:
        logging.error(
            f'Файл {file_name} не сохранился на яндекс диске! status_code = {response.status_code}') 


if __name__ == '__main__':
    load_dotenv()
    vk_api_version = 5.131
    ya_disk_token = os.getenv('YANDEX_DISK_TOKEN')
    vk_api_token = os.getenv('VK_API_TOKEN')
    user_profile_photos_info, files_info_to_json = get_user_profile_photos_info(
        vk_api_token,
        vk_api_version)
    create_ya_disk_folder(YA_DISK_FOLDER, ya_disk_token)
    for file_info in tqdm(user_profile_photos_info):
        photo_url = file_info['link']
        file_name = str(file_info['file_name'])
        ya_disk_upload_url = get_ya_disk_upload_url(ya_disk_token, file_name)
        upload_file(ya_disk_upload_url, photo_url, file_name)
    save_files_info_to_json(files_info_to_json)

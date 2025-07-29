from time import sleep
import requests
from tqdm import tqdm
import json
import re
from urllib.parse import quote

class YDAPI:
    """Creates a folder on Yandex.Disk.
    Uploads an image to it without saving it to the computer.
    """
    def __init__(self, token):
        self.base_url = "https://cloud-api.yandex.net/v1/disk/resources"
        self.headers = {'Authorization': f'OAuth {token}'}
        self.meta_data = None

    def create_folder(self, path):
        print(f"Создание папки {path} на Я.Диске")
        params = {
            'path': path
        }
        response = requests.put(self.base_url, headers=self.headers, params=params)
        if response.status_code == 201:
            print(f"Папка {path} создана")
            return True
        elif response.status_code == 409:
            print(f"Папка {path} уже существует")
            return True
        print(f"Ошибка при создании папки: "
              f"{response.json().get('message', 'Неизвестная ошибка')}")
        return False

    def delete_folder(self, path):
        params = {
            'path': path
        }
        response = requests.delete(self.base_url, headers=self.headers, params=params)
        if response.status_code != 204:
            print(f"Ошибка удаления папки: "
                  f"{response.json().get('message', 'Неизвестная ошибка')}")
        return response.status_code == 204

    def upload_from_url(self, path, url):
        print(f"Загрузка файла в {path}")

        filename = self._sanitize_filename(path.split('/')[-1])
        full_path = f"{path.rsplit('/', 1)[0]}/{filename}" if '/' in path else filename

        image_info_path = 'image_info.json'

        try:
            head_resp = requests.head(url, timeout=5)
            file_size = int(head_resp.headers.get('content-length', 0))

            if file_size == 0:
                response = requests.get(url, stream=True)
                file_size = int(response.headers.get('content-length', 0))
                response.close()
        except Exception as e:
            print(f"Не удалось получить размер файла: {e}")
            file_size = 0

        # JSON
        try:
            try:
                with open(image_info_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            image_info = {
                'filename': path.split('/')[-1],
                'url': url,
                'size_bytes': file_size,
                'status': 'uploading',
            }
            existing_data.append(image_info)

            with open(image_info_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            print(f"Информация о файле добавлена в {image_info_path}")
        except Exception as e:
            print(f"Не удалось сохранить информацию о файле: {e}")

        # Progress Bar
        with tqdm(total=100, desc="Прогресс загрузки") as pbar:
            for i in range(10):
                sleep(0.3)
                pbar.update(10)

        upload_url = f"{self.base_url}/upload"
        params = {
            'path': path,
            'url': url,
            'disable_redirects': 'true'
        }
        try:
            response = requests.post(upload_url, headers=self.headers, params=params,
                                   timeout=10)
            if response.status_code == 202:
                print("Файл поставлен в очередь на загрузку")
                return True
            print(f"Ошибка API: {response.json().get('message', 'Неизвестная ошибка')}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Ошибка соединения: {e}")
            return False

    def _sanitize_filename(self, text):
        """Secure text file name"""
        safe_text = text.replace(' ', '_')
        safe_text = re.sub(r'[^\w\-_.]', '', safe_text)
        safe_text = safe_text[:40]
        if not safe_text.lower().endswith('.jpg'):
            safe_text += '.jpg'
        return safe_text


def main():
    print("Сохранение изображения на Я.Диск")

    text = input('Введите ваш текст: ').strip()
    token = input('Введите токен с Полигона Я.Диска: ').strip()

    print("Генерация изображения с текстом")
    image_url = f'https://cataas.com/cat/says/{quote(text)}?fontColor=white&fontSize=85'

    try:
        response = requests.get(image_url, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка: невозможно получить изображение: {e}")
        return

    filename = f"{text}.jpg" if text else "cat.jpg"
    full_path = f"SPD-132/{filename}"

    yd_api = YDAPI(token)

    if yd_api.create_folder('SPD-132'):
        if yd_api.upload_from_url(full_path, image_url):
            print("Файл успешно загружен на Я.Диск")
        else:
            print("Не удалось загрузить файл")
    else:
        print("Не удалось создать папку")


if __name__ == "__main__":
    main()
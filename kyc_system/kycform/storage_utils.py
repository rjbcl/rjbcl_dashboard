import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def save_uploaded_file_to_storage(file_obj, folder):
    filename = file_obj.name
    safe_name = filename.replace(" ", "_")
    full_path = os.path.join(folder, safe_name)
    saved_path = default_storage.save(full_path, ContentFile(file_obj.read()))
    url = default_storage.url(saved_path)
    return saved_path, url

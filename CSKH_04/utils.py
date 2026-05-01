import os
import unicodedata
import re
from django.utils.deconstruct import deconstructible

@deconstructible
class UnaccentedUploadTo:
    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        name = filename.rsplit('.', 1)[0]
        
        # Replace specific characters like đ, Đ
        s = re.sub(r'[đĐ]', 'd', name)
        # Normalize and remove accents
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
        # Replace spaces with underscores
        s = re.sub(r'\s+', '_', s)
        # Remove any non-alphanumeric characters (keep underscores and hyphens)
        s = re.sub(r'[^\w\-]', '', s)
        
        new_filename = f"{s}.{ext}"
        return os.path.join(self.sub_path, new_filename)

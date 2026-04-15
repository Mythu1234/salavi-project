import os
import django
import unicodedata

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CSKH_04.settings')
django.setup()

from products.models import SanPham, DanhGia
from orders.models import DoiTra

def remove_accents(input_str):
    nkscheck = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nkscheck if not unicodedata.combining(c)])

def fix_images():
    # Fix SanPham
    for sp in SanPham.objects.all():
        if not sp.HinhAnh: continue
        try:
            full_path = sp.HinhAnh.path
            if not os.path.exists(full_path):
                folder = os.path.dirname(full_path)
                filename = os.path.basename(full_path)
                available_files = os.listdir(folder)
                target_norm = remove_accents(filename).lower()
                match = None
                for f in available_files:
                    if remove_accents(f).lower() == target_norm:
                        match = f
                        break
                if match:
                    relative_path = os.path.join(os.path.basename(folder), match).replace('\\', '/')
                    sp.HinhAnh = relative_path
                    sp.save()
        except: pass

    # Fix DoiTra & DanhGia (simple existence check)
    for model in [DoiTra, DanhGia]:
        for obj in model.objects.all():
            if not obj.HinhAnh: continue
            try:
                if not os.path.exists(obj.HinhAnh.path):
                    # For DoiTra/DanhGia we don't have enough info to "guess" easily yet
                    pass
            except: pass

if __name__ == "__main__":
    fix_images()
    print("Image fix process completed.")

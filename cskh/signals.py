from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import KhachHang
from .models import TichDiem

@receiver(post_save, sender=KhachHang)
def create_tich_diem_for_new_customer(sender, instance, created, **kwargs):
    if created:
        # 1. Kiểm tra xem khách hàng đã có bản ghi tích điểm chưa (tránh trùng lặp)
        if not TichDiem.objects.filter(MaKH=instance).exists():
            # 2. Logic tạo mã TD0000X
            last_td = TichDiem.objects.filter(MaTichDiem__startswith='TD').order_by('-MaTichDiem').first()
            if last_td:
                # Trích xuất số từ mã lớn nhất hiện tại (ví dụ: TD00021 -> 21)
                try:
                    last_num = int(last_td.MaTichDiem[2:])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = TichDiem.objects.count() + 1
            else:
                new_num = 1
                
            new_ma_td = f"TD{new_num:05d}"
            
            # 3. Tạo bản ghi tích điểm mặc định là 0
            TichDiem.objects.create(
                MaTichDiem=new_ma_td,
                MaKH=instance,
                TongDiem=0
            )
            print(f"--- Tự động tạo mã tích điểm {new_ma_td} cho khách hàng {instance.HoTen} ---")

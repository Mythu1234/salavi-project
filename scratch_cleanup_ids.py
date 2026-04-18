from cskh.models import LichSuTichDiem
from django.db import transaction

def cleanup_ids_final_sweep():
    # Chỉ lấy những mã bắt đầu bằng LS nhưng KHÔNG phải LSTD
    old_records = list(LichSuTichDiem.objects.filter(MaLS__startswith='LS').exclude(MaLS__startswith='LSTD'))
    
    if not old_records:
        print("Không còn mã LS nào cần dọn dẹp.")
        return

    print(f"Số lượng cần dọn dẹp cuối cùng: {len(old_records)}")
    
    for i, rec in enumerate(old_records):
        try:
            with transaction.atomic():
                last_ls = LichSuTichDiem.objects.filter(MaLS__startswith='LSTD').order_by('-MaLS').first()
                if last_ls:
                    last_num = int(last_ls.MaLS[4:])
                    new_num = last_num + 1
                else:
                    new_num = 1
                    
                new_id = f"LSTD{new_num:05d}"
                
                # Lưu thông tin cũ
                data = {
                    'MaKH': rec.MaKH,
                    'MaNV': rec.MaNV,
                    'DiemThayDoi': rec.DiemThayDoi,
                    'LyDo': rec.LyDo,
                    'NgayThucHien': rec.NgayThucHien
                }
                old_id = rec.MaLS
                
                # Tạo mới và xóa cũ
                LichSuTichDiem.objects.create(MaLS=new_id, **data)
                rec.delete()
                print(f"Thành công: {old_id} -> {new_id}")
        except Exception as e:
            print(f"Lỗi khi xử lý {rec.MaLS}: {str(e)}")

if __name__ == "__main__":
    cleanup_ids_final_sweep()
    print("Quét dọn hoàn tất!")

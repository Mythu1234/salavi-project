from django.db import models
from accounts.models import KhachHang, NhanVien

class KhuyenMai(models.Model):
    MaKM = models.CharField(max_length=10, primary_key=True)
    TenKhuyenMai = models.CharField(max_length=50)
    PhanTramGiam = models.DecimalField(max_digits=5, decimal_places=2)
    NgayBatDau = models.DateField()
    NgayKetThuc = models.DateField()
    MoTa = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.TenKhuyenMai

class TichDiem(models.Model):
    MaTichDiem = models.CharField(max_length=10, primary_key=True)
    MaKH = models.OneToOneField(KhachHang, on_delete=models.CASCADE)
    TongDiem = models.IntegerField()

    def __str__(self):
        return self.MaTichDiem

class LichSuTichDiem(models.Model):
    MaLS = models.CharField(max_length=10, primary_key=True)
    MaKH = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    DiemThayDoi = models.IntegerField()
    LyDo = models.CharField(max_length=200)
    NgayThucHien = models.DateField()

    def __str__(self):
        return self.MaLS

class ThongBaoKhuyenMai(models.Model):
    MaTB = models.CharField(max_length=10, primary_key=True)
    MaKH = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    NoiDung = models.CharField(max_length=200)
    NgayGui = models.DateField()

    def __str__(self):
        return self.MaTB

class HoiThoaiTuVan(models.Model):
    MaHoiThoai = models.CharField(max_length=10, primary_key=True)
    MaKH = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    TrangThai = models.CharField(max_length=50)

    def __str__(self):
        return self.MaHoiThoai

class TinNhanTuVan(models.Model):
    MaTinNhan = models.CharField(max_length=10, primary_key=True)
    MaHoiThoai = models.ForeignKey(HoiThoaiTuVan, on_delete=models.CASCADE)
    MaNV = models.ForeignKey(NhanVien, on_delete=models.SET_NULL, null=True, blank=True)
    NoiDung = models.CharField(max_length=200)
    NguoiGui = models.CharField(max_length=10, default='NV') # Thêm mặc định để tránh lỗi
    ThoiGianGui = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.MaTinNhan

from django.db import models

class TaiKhoan(models.Model):
    VaiTro_CHOICES = [
        ('Chủ', 'Chủ'),
        ('Nhân viên', 'Nhân viên'),
        ('Khách hàng', 'Khách hàng')
    ]
    MaTK = models.CharField(max_length=10, primary_key=True)
    TenDangNhap = models.CharField(max_length=50, unique=True)
    MatKhau = models.CharField(max_length=20)
    VaiTro = models.CharField(max_length=20, choices=VaiTro_CHOICES)

    def __str__(self):
        return self.TenDangNhap

class KhachHang(models.Model):
    MaKH = models.CharField(max_length=10, primary_key=True)
    MaTK = models.OneToOneField(TaiKhoan, on_delete=models.CASCADE)
    HoTen = models.CharField(max_length=50)
    DiaChi = models.CharField(max_length=200)

    def __str__(self):
        return self.HoTen

class NhanVien(models.Model):
    MaNV = models.CharField(max_length=10, primary_key=True)
    MaTK = models.OneToOneField(TaiKhoan, on_delete=models.CASCADE)
    HoTen = models.CharField(max_length=50)

    def __str__(self):
        return self.HoTen

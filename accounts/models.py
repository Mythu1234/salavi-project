from django.db import models
from django.contrib.auth.models import User

class KhachHang(models.Model):
    MaKH = models.CharField(max_length=10, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    HoTen = models.CharField(max_length=50)
    DiaChi = models.CharField(max_length=200)

    def __str__(self):
        return self.HoTen

class NhanVien(models.Model):
    MaNV = models.CharField(max_length=10, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    HoTen = models.CharField(max_length=50)

    def __str__(self):
        return self.HoTen

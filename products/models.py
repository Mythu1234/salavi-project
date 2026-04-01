from django.db import models
from accounts.models import KhachHang

class SanPham(models.Model):
    MaSP = models.CharField(max_length=10, primary_key=True)
    TenSP = models.CharField(max_length=100)
    MoTa = models.CharField(max_length=200, null=True, blank=True)
    Gia = models.DecimalField(max_digits=18, decimal_places=2)
    HinhAnh = models.ImageField(upload_to='sanpham/')

    def __str__(self):
        return self.TenSP

class ChiTietSanPham(models.Model):
    Size_CHOICES = [
        ('SX', 'SX'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL','XXL')
    ]
    MaCTSP = models.CharField(max_length=10, primary_key=True)
    MaSP = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    MauSac = models.CharField(max_length=50)
    Size = models.CharField(max_length=20, choices=Size_CHOICES)
    SoLuongTon = models.IntegerField()

    def __str__(self):
        return self.MaCTSP

class DanhGia(models.Model):
    MaDanhGia = models.CharField(max_length=10, primary_key=True)
    MaKH = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    MaSP = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    SoSao = models.IntegerField()
    NoiDung = models.CharField(max_length=200, null=True, blank=True)
    HinhAnh = models.ImageField(upload_to='danhgia/', blank=True)
    NgayDanhGia = models.DateField()

    def __str__(self):
        return self.MaDanhGia

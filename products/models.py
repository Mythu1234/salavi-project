from django.db import models
from accounts.models import KhachHang
from CSKH_04.utils import UnaccentedUploadTo

class SanPham(models.Model):
    MaSP = models.CharField(max_length=10, primary_key=True)
    TenSP = models.CharField(max_length=100)
    MoTa = models.CharField(max_length=200, null=True, blank=True)
    Gia = models.DecimalField(max_digits=18, decimal_places=2)
    HinhAnh = models.ImageField(upload_to=UnaccentedUploadTo('sanpham/'))

    def __str__(self):
        return self.TenSP

class BienTheSanPham(models.Model):
    Size_CHOICES = [
        ('SX', 'SX'), ('S', 'S'), ('M', 'M'),
        ('L', 'L'), ('XL', 'XL'), ('XXL','XXL')
    ]
    # Đổi tên từ MaCTSP thành MaBTSP cho đúng ý bạn
    MaBTSP = models.CharField(max_length=10, primary_key=True)
    MaSP = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    MauSac = models.CharField(max_length=50)
    Size = models.CharField(max_length=20, choices=Size_CHOICES)
    SoLuongTon = models.IntegerField()

    class Meta:
        # Tên bảng mới bạn muốn thay thế
        db_table = 'products_bienthesanpham'

    def __str__(self):
        return self.MaBTSP

class DanhGia(models.Model):
    MaDanhGia = models.CharField(max_length=10, primary_key=True)
    MaKH = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    MaSP = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    SoSao = models.IntegerField()
    NoiDung = models.CharField(max_length=200, null=True, blank=True)
    HinhAnh = models.ImageField(upload_to=UnaccentedUploadTo('danhgia/'), blank=True)
    NgayDanhGia = models.DateField()

    def __str__(self):
        return self.MaDanhGia

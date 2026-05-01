from django.db import models
from accounts.models import KhachHang, NhanVien
from products.models import BienTheSanPham
from cskh.models import KhuyenMai
from CSKH_04.utils import UnaccentedUploadTo

class DonHang(models.Model):
    TRANGTHAI_CHOICES = [
        ('CHO', 'Chờ xử lý'),
        ('DANG', 'Đang giao'),
        ('DONE', 'Đã giao'),
    ]

    MaDonHang = models.CharField(max_length=10, primary_key=True)
    MaKH = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    MaKM = models.ForeignKey(KhuyenMai, on_delete=models.SET_NULL, null=True, blank=True)
    NgayDat = models.DateField()
    NgayGiao = models.DateField(null=True, blank=True)
    TongTien = models.DecimalField(max_digits=18, decimal_places=2)
    TrangThaiDonHang = models.CharField(max_length=50, choices=TRANGTHAI_CHOICES)
    DiaChiGiaoHang = models.CharField(max_length=200)

    def __str__(self):
        return self.MaDonHang

class ChiTietDonHang(models.Model):
    MaCTDH = models.AutoField(primary_key=True)
    MaDonHang = models.ForeignKey(DonHang, on_delete=models.CASCADE)
    MaBTSP = models.ForeignKey(BienTheSanPham, on_delete=models.CASCADE)
    SoLuong = models.IntegerField(default=0)
    DonGia = models.DecimalField(max_digits=18, decimal_places=2)
    ThanhTien = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        unique_together = (('MaDonHang', 'MaBTSP'),)

    def __str__(self):
        return f"{self.MaDonHang} - {self.MaBTSP}"

class DoiTra(models.Model):
    LOAI_CHOICES = [
        ('DOI', 'Đổi hàng'),
        ('TRA', 'Trả hàng - Hoàn tiền')
    ]

    TRANGTHAI_CHOICES = [
        ('DONE', 'Đã xử lý'),
        ('PENDING', 'Chờ xử lý'),
        ('REJECT', 'Từ chối')
    ]

    MaDoiTra = models.CharField(max_length=10, primary_key=True)
    MaCTDH = models.ForeignKey(ChiTietDonHang, on_delete=models.CASCADE)
    MaKH = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    MaNV = models.ForeignKey(NhanVien, on_delete=models.CASCADE, null=True, blank=True)
    LoaiYeuCau = models.CharField(max_length=50, choices=LOAI_CHOICES)
    NgayYeuCau = models.DateField()
    LyDo = models.CharField(max_length=200)
    HinhAnh = models.ImageField(upload_to=UnaccentedUploadTo('doitra_images/'))
    TrangThai = models.CharField(max_length=50, choices=TRANGTHAI_CHOICES, default='PENDING')
    GhiChuXuLy = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.MaDoiTra

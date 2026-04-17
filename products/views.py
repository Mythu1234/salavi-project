import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import SanPham, BienTheSanPham, DanhGia
import re
from django.db.models import Q, Avg, Count, Sum

def get_next_ma_sp_num():
    """Lấy số thứ tự SP tiếp theo bằng cách tìm số lớn nhất trong toàn bộ MaSP"""
    all_ids = SanPham.objects.values_list('MaSP', flat=True)
    max_num = 0
    for cid in all_ids:
        match = re.search(r'\d+', cid)
        if match:
            num = int(match.group())
            if num > max_num:
                max_num = num
    return max_num + 1

def get_next_ma_bt_num():
    """Lấy số thứ tự BT tiếp theo bằng cách tìm số lớn nhất trong toàn bộ MaBTSP"""
    all_ids = BienTheSanPham.objects.values_list('MaBTSP', flat=True)
    max_num = 0
    for cid in all_ids:
        match = re.search(r'\d+', cid)
        if match:
            num = int(match.group())
            if num > max_num:
                max_num = num
    return max_num + 1

def product_list(request):
    query = request.GET.get('q')
    loai_filter = request.GET.get('loai')

    # Lấy tất cả sản phẩm, sắp xếp theo MaSP tăng dần
    products_qs = SanPham.objects.all().order_by('MaSP')

    if query:
        products_qs = products_qs.filter(
            Q(MaSP__icontains=query) |
            Q(TenSP__icontains=query) |
            Q(bienthesanpham__MauSac__icontains=query) |
            Q(bienthesanpham__Size__icontains=query)
        ).distinct()

    if loai_filter and loai_filter != 'Tất cả':
        products_qs = products_qs.filter(TenSP__icontains=loai_filter)

    display_products = []

    for p in products_qs:
        # Tính toán đánh giá và tồn kho dựa trên quan hệ 1-N (1 SP Lớn -> N Biến thể)
        # Sử dụng MaDanhGia thay vì id để tránh lỗi FieldError
        rating_data = p.danhgia_set.aggregate(
            avg_rating=Avg('SoSao'), 
            count_reviews=Count('MaDanhGia')
        )
        avg_rating = rating_data['avg_rating'] or 0.0
        
        # Tính tổng tồn kho của tất cả biến thể
        total_stock = p.bienthesanpham_set.aggregate(total=Sum('SoLuongTon'))['total'] or 0

        display_products.append({
            'MaSP': p.MaSP,
            'TenSP': p.TenSP,
            'HinhAnh': p.HinhAnh,
            'Gia': p.Gia,
            'sao_trung': avg_rating,
            'star_percent': avg_rating * 20,
            'co_danh_gia': rating_data['count_reviews'],
            'total_stock': total_stock,
            'variants': p.bienthesanpham_set.all().order_by('MaBTSP')
        })

    return render(request, 'products/product_list.html', {
        'products': display_products,
        'current_loai': loai_filter or 'Tất cả',
        'search_query': query
    })

def add_product(request):
    if request.method == 'POST':
        ten_sp = request.POST.get('TenSP')
        gia = request.POST.get('Gia')
        mo_ta = request.POST.get('MoTa')
        hinh_anh = request.FILES.get('HinhAnh')

        sizes = [s.strip() for s in request.POST.get('Size', '').split(',') if s.strip()]
        colors = [c.strip() for c in request.POST.get('MauSac', '').split(',') if c.strip()]
        so_luong_ton = int(request.POST.get('SoLuongTon', 0))

        # 1. Tạo DUY NHẤT một Sản phẩm Lớn (đại diện cho toàn bộ nhóm)
        new_ma_sp = f"SP{get_next_ma_sp_num():05d}"
        parent_product = SanPham.objects.create(
            MaSP=new_ma_sp, TenSP=ten_sp, MoTa=mo_ta, Gia=gia, HinhAnh=hinh_anh
        )

        # 2. Tạo các biến thể liên kết với Sản phẩm Lớn đó
        current_bt_num = get_next_ma_bt_num()
        total_variants = len(sizes) * len(colors)
        avg_stock = so_luong_ton // total_variants if total_variants > 0 else 0
        remainder = so_luong_ton % total_variants if total_variants > 0 else 0

        idx = 0
        for size_item in sizes:
            for color_item in colors:
                new_ma_bt = f"BT{current_bt_num:05d}"
                BienTheSanPham.objects.create(
                    MaBTSP=new_ma_bt,
                    MaSP=parent_product,
                    MauSac=color_item,
                    Size=size_item,
                    # Chia đều tồn kho, phần dư cộng vào biến thể đầu tiên
                    SoLuongTon=avg_stock + (remainder if idx == 0 else 0)
                )
                current_bt_num += 1
                idx += 1
        return redirect('products:product_list')
    return render(request, 'products/product_form.html')

def edit_product(request, pk):
    mode = request.GET.get('mode', 'group')

    if mode == 'variant':
        variant = get_object_or_404(BienTheSanPham, MaBTSP=pk)
        product = variant.MaSP
    else:
        product = get_object_or_404(SanPham, MaSP=pk)
        variant = product.bienthesanpham_set.first()

    all_colors = ['Trắng', 'Đen', 'Xám', 'Đỏ', 'Xanh dương', 'Xanh lá', 'Vàng', 'Hồng', 'Tím', 'Nâu', 'Cam', 'Kem']
    all_sizes = ['SX', 'S', 'M', 'L', 'XL', 'XXL']

    if request.method == 'POST':
        new_sizes = [s.strip() for s in request.POST.get('Size', '').split(',') if s.strip()]
        new_colors = [c.strip() for c in request.POST.get('MauSac', '').split(',') if c.strip()]

        if mode == 'variant':
            if new_colors: variant.MauSac = new_colors[0]
            if new_sizes: variant.Size = new_sizes[0]
            variant.SoLuongTon = int(request.POST.get('SoLuongTon', 0))
            variant.save()
            product.TenSP = request.POST.get('TenSP')
            product.Gia = request.POST.get('Gia')
            if request.FILES.get('HinhAnh'): product.HinhAnh = request.FILES.get('HinhAnh')
            product.save()
        else:
            # Cập nhật thông tin Sản phẩm Lớn (giữ nguyên MaSP)
            product.TenSP = request.POST.get('TenSP')
            product.Gia = request.POST.get('Gia')
            product.MoTa = request.POST.get('MoTa')
            if request.FILES.get('HinhAnh'):
                product.HinhAnh = request.FILES.get('HinhAnh')
            product.save()

            total_stock = int(request.POST.get('SoLuongTon', 0))

            # Xóa biến thể hiện tại của SP này
            product.bienthesanpham_set.all().delete()

            current_bt_num = get_next_ma_bt_num()
            sizes_list = new_sizes
            colors_list = new_colors
            total_new_variants = len(sizes_list) * len(colors_list)
            avg_stock = total_stock // total_new_variants
            remainder = total_stock % total_new_variants

            idx = 0
            for s in sizes_list:
                for c in colors_list:
                    BienTheSanPham.objects.create(
                        MaBTSP=f"BT{current_bt_num:05d}",
                        MaSP=product,
                        MauSac=c,
                        Size=s,
                        SoLuongTon=avg_stock + (remainder if idx == 0 else 0)
                    )
                    current_bt_num += 1
                    idx += 1
        return redirect('products:product_list')

    if mode == 'variant':
        initial_colors = [variant.MauSac]
        initial_sizes = [variant.Size]
    else:
        initial_colors = list(product.bienthesanpham_set.values_list('MauSac', flat=True).distinct())
        initial_sizes = list(product.bienthesanpham_set.values_list('Size', flat=True).distinct())

    total_stock = product.bienthesanpham_set.aggregate(Sum('SoLuongTon'))['SoLuongTon__sum'] or 0

    return render(request, 'products/product_edit.html', {
        'product': product,
        'variant': variant,
        'mode': mode,
        'all_colors': all_colors,
        'all_sizes': all_sizes,
        'current_colors_json': json.dumps(initial_colors),
        'current_sizes_json': json.dumps(initial_sizes),
        'total_stock': variant.SoLuongTon if mode == 'variant' else total_stock
    })

def product_detail(request, pk):
    # Thử tìm theo mã biến thể trước để hiện đúng size/màu đã chọn
    variant_obj = BienTheSanPham.objects.filter(MaBTSP=pk).first()
    if variant_obj:
        product = variant_obj.MaSP
        current_variant = variant_obj
    else:
        # Nếu không thấy biến thể, tìm theo mã sản phẩm lớn và lấy loại đầu tiên
        product = get_object_or_404(SanPham, MaSP=pk)
        current_variant = product.bienthesanpham_set.first()
    
    variants = product.bienthesanpham_set.all().order_by('MaBTSP')

    # Logic phân loại dựa trên tên
    loai_sp = "Sản phẩm"
    ten_sp_lower = product.TenSP.lower()
    if "áo" in ten_sp_lower: loai_sp = "Áo"
    elif "quần" in ten_sp_lower: loai_sp = "Quần"
    elif "váy" in ten_sp_lower: loai_sp = "Váy"
    elif "phụ kiện" in ten_sp_lower: loai_sp = "Phụ kiện"

    # Sửa lỗi FieldError bằng cách dùng MaDanhGia
    rating_data = product.danhgia_set.aggregate(avg=Avg('SoSao'), count=Count('MaDanhGia'))
    avg_rating = rating_data['avg'] or 0.0
    product.star_percent = avg_rating * 20
    return render(request, 'products/product_detail.html', {
        'product': product,
        'current_variant': current_variant,
        'variants': variants,
        'loai_sp': loai_sp,
        'co_danh_gia': rating_data['count']
    })

def delete_product(request, pk):
    mode = request.GET.get('mode', 'group')
    if mode == 'variant':
        obj = get_object_or_404(BienTheSanPham, MaBTSP=pk)
    else:
        obj = get_object_or_404(SanPham, MaSP=pk)
    if request.method == 'POST':
        obj.delete()
        return render(request, 'products/product_delete_success.html')
    return render(request, 'products/product_delete.html', {'product': obj, 'mode': mode})

def add_success(request): return render(request, 'products/product_add_success.html')
def edit_success(request): return render(request, 'products/product_edit_success.html')
def delete_success(request): return render(request, 'products/product_delete_success.html')

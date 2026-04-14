from django.shortcuts import render, redirect, get_object_or_404
from .models import SanPham, BienTheSanPham
import re
from django.db.models import Q, Avg, Count

def product_list(request):
    # Lấy tham số tìm kiếm từ ô tìm kiếm (q) và tham số lọc loại (loai)
    query = request.GET.get('q')
    loai_filter = request.GET.get('loai')
    
    products_qs = SanPham.objects.annotate(
        sao_trung_binh=Avg('danhgia__SoSao'),
        co_danh_gia=Count('danhgia')
    ).order_by('MaSP')

    # 1. Xử lý tìm kiếm theo từ khóa (Ô tìm kiếm)
    if query:
        products = products.filter(TenSP__icontains=query)
    
    if loai_filter and loai_filter != 'Tất cả':
        products_qs = products_qs.filter(TenSP__icontains=loai_filter)
    else:
        loai_filter = 'Tất cả'

    products = []
    for p in products_qs:
        p.sao_trung = p.sao_trung_binh or 0.0
        p.star_percent = p.sao_trung * 20
        products.append(p)

    return render(request, 'products/product_list.html', {
        'products': products,
        'current_loai': loai_filter,
        'search_query': query
    })

def add_product(request):
    if request.method == 'POST':
        ten_sp = request.POST.get('TenSP')
        gia = request.POST.get('Gia')
        mo_ta = request.POST.get('MoTa')
        hinh_anh = request.FILES.get('HinhAnh')
        
        # Bien the
        size = request.POST.get('Size')
        mau_sac = request.POST.get('MauSac')
        so_luong_ton = int(request.POST.get('SoLuongTon', 0))

        # 1. Tự động sinh mã sản phẩm
        last_product = SanPham.objects.all().order_by('MaSP').last()
        if last_product:
            last_id = last_product.MaSP
            number_part = re.search(r'\d+', last_id)
            if number_part:
                num = int(number_part.group()) + 1
                new_ma_sp = f"SP{num:05d}"
            else:
                new_ma_sp = "SP00001"
        else:
            new_ma_sp = "SP00001"

        # 2. Lưu sản phẩm mới
        new_product = SanPham.objects.create(
            MaSP=new_ma_sp,
            TenSP=ten_sp,
            MoTa=mo_ta,
            Gia=gia,
            HinhAnh=hinh_anh
        )

        # 3. Lưu biến thể sản phẩm
        last_bt = BienTheSanPham.objects.all().order_by('MaBTSP').last()
        if last_bt:
            num_bt = int(re.search(r'\d+', last_bt.MaBTSP).group()) + 1
            new_ma_bt = f"BTSP{num_bt:05d}"
        else:
            new_ma_bt = "BTSP00001"

        BienTheSanPham.objects.create(
            MaBTSP=new_ma_bt,
            MaSP=new_product,
            MauSac=mau_sac,
            Size=size,
            SoLuongTon=so_luong_ton
        )
        return redirect('products:product_list')

    products = SanPham.objects.all().order_by('MaSP')
    return render(request, 'products/product_form.html', {'products': products})

def edit_product(request, pk):
    product = get_object_or_404(SanPham, MaSP=pk)
    variant = BienTheSanPham.objects.filter(MaSP=product).first()
    
    if request.method == 'POST':
        product.TenSP = request.POST.get('TenSP')
        product.Gia = request.POST.get('Gia')
        product.MoTa = request.POST.get('MoTa')
        if request.FILES.get('HinhAnh'):
            product.HinhAnh = request.FILES.get('HinhAnh')
        product.save()

        if variant:
            variant.Size = request.POST.get('Size')
            variant.MauSac = request.POST.get('MauSac')
            variant.SoLuongTon = request.POST.get('SoLuongTon', 0)
            variant.save()
        else:
            last_bt = BienTheSanPham.objects.all().order_by('MaBTSP').last()
            if last_bt:
                num_bt = int(re.search(r'\d+', last_bt.MaBTSP).group()) + 1
                new_ma_bt = f"BTSP{num_bt:05d}"
            else:
                new_ma_bt = "BTSP00001"
            BienTheSanPham.objects.create(
                MaBTSP=new_ma_bt,
                MaSP=product,
                MauSac=request.POST.get('MauSac'),
                Size=request.POST.get('Size'),
                SoLuongTon=request.POST.get('SoLuongTon', 0)
            )
        
        return redirect('products:product_list')

    products = SanPham.objects.all().order_by('MaSP')
    return render(request, 'products/product_edit.html', {
        'products': products, 
        'product': product,
        'variant': variant
    })

def product_detail(request, pk):
    products = SanPham.objects.all().order_by('MaSP')
    product = get_object_or_404(SanPham, MaSP=pk)
    variant = BienTheSanPham.objects.filter(MaSP=product).first()
    return render(request, 'products/product_detail.html', {
        'products': products, 
        'product': product,
        'variant': variant
    })

def delete_product(request, pk):
    product = get_object_or_404(SanPham, MaSP=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('products:product_list')
    
    products = SanPham.objects.all().order_by('MaSP')
    return render(request, 'products/product_delete.html', {
        'products': products, 
        'product': product
    })

def add_success(request):
    products = SanPham.objects.all().order_by('MaSP')
    return render(request, 'products/product_add_success.html', {'products': products})

def edit_success(request):
    products = SanPham.objects.all().order_by('MaSP')
    return render(request, 'products/product_edit_success.html', {'products': products})

def delete_success(request):
    products = SanPham.objects.all().order_by('MaSP')
    return render(request, 'products/product_delete_success.html', {'products': products})

from django.shortcuts import render
from .models import SanPham

def product_list(request):
    products = SanPham.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

def add_product(request):
    products = SanPham.objects.all()
    return render(request, 'products/product_form.html', {'products': products})

def edit_product(request, pk):
    products = SanPham.objects.all()
    try:
        product = SanPham.objects.get(MaSP=pk)
    except SanPham.DoesNotExist:
        product = None
    return render(request, 'products/product_edit.html', {'products': products, 'product': product})

def product_detail(request, pk):
    products = SanPham.objects.all()
    try:
        product = SanPham.objects.get(MaSP=pk)
    except SanPham.DoesNotExist:
        product = None
    return render(request, 'products/product_detail.html', {'products': products, 'product': product})

def delete_product(request, pk):
    products = SanPham.objects.all()
    try:
        product = SanPham.objects.get(MaSP=pk)
    except SanPham.DoesNotExist:
        product = None
    
    # Normally handle POST to actually delete here
    # if request.method == 'POST': ...

    return render(request, 'products/product_delete.html', {'products': products, 'product': product})

def add_success(request):
    products = SanPham.objects.all()
    return render(request, 'products/product_add_success.html', {'products': products})

def edit_success(request):
    products = SanPham.objects.all()
    return render(request, 'products/product_edit_success.html', {'products': products})

def delete_success(request):
    products = SanPham.objects.all()
    return render(request, 'products/product_delete_success.html', {'products': products})

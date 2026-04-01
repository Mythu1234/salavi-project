from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from cskh.models import LichSuTichDiem, TichDiem
from orders.models import DonHang

from .models import KhachHang


def _get_customer_table_data(query=''):
    customer_queryset = KhachHang.objects.select_related('MaTK').order_by('MaKH')

    if query:
        customer_queryset = customer_queryset.filter(
            Q(HoTen__icontains=query)
            | Q(MaKH__icontains=query)
            | Q(MaTK__TenDangNhap__icontains=query)
            | Q(DiaChi__icontains=query)
        )

    customers = [
        {
            'stt': index,
            'name': customer.HoTen,
            'code': customer.MaKH,
            'phone': customer.MaTK.TenDangNhap,
            'address': customer.DiaChi,
        }
        for index, customer in enumerate(customer_queryset, start=1)
    ]
    return {
        'customers': customers,
        'query': query,
    }


def login_view(request):
    return render(request, 'accounts/login/login.html')


def register_view(request):
    return render(request, 'accounts/login/register.html')


def forgot_password_view(request):
    step = request.GET.get('step', 'account')
    valid_steps = {'account', 'otp', 'reset'}
    if step not in valid_steps:
        step = 'account'

    context = {
        'step': step,
    }
    return render(request, 'accounts/login/forgot_password.html', context)


def customer_create_view(request):
    context = _get_customer_table_data()
    context.update({
        'page_title': 'Salavi - Thêm khách hàng',
        'form_title': 'Thêm khách hàng',
        'customer_form': {
            'code': 'KH010',
            'name': '',
            'phone': '',
            'address': '',
        },
        'save_label': 'Lưu',
    })
    return render(request, 'accounts/customer/customer_create.html', context)


def customer_edit_view(request, customer_code):
    customer = get_object_or_404(
        KhachHang.objects.select_related('MaTK'),
        MaKH=customer_code,
    )
    context = _get_customer_table_data()
    context.update({
        'page_title': 'Salavi - Chỉnh sửa thông tin khách hàng',
        'form_title': 'Chỉnh sửa thông tin khách hàng',
        'customer_form': {
            'code': customer.MaKH,
            'name': customer.HoTen,
            'phone': customer.MaTK.TenDangNhap,
            'address': customer.DiaChi,
        },
        'save_label': 'Lưu',
    })
    return render(request, 'accounts/customer/customer_create.html', context)


def customer_delete_view(request, customer_code):
    customer = get_object_or_404(
        KhachHang.objects.select_related('MaTK'),
        MaKH=customer_code,
    )
    context = _get_customer_table_data()
    context.update({
        'delete_customer': {
            'code': customer.MaKH,
            'name': customer.HoTen,
        },
    })
    return render(request, 'accounts/customer/customer_delete.html', context)


def customer_detail_view(request, customer_code):
    customer = get_object_or_404(
        KhachHang.objects.select_related('MaTK'),
        MaKH=customer_code,
    )
    point_total = (
        TichDiem.objects.filter(MaKH=customer).values_list('TongDiem', flat=True).first()
        or 0
    )
    point_history = list(
        LichSuTichDiem.objects.filter(MaKH=customer).order_by('-NgayThucHien')
    )
    points_by_date = {}
    for item in point_history:
        points_by_date[item.NgayThucHien] = (
            points_by_date.get(item.NgayThucHien, 0) + item.DiemThayDoi
        )

    orders = DonHang.objects.filter(MaKH=customer).order_by('-NgayDat')
    purchase_history = [
        {
            'date': order.NgayDat.strftime('%d/%m/%Y'),
            'content': 'Mua hàng',
            'payment': f"{int(order.TongTien):,}".replace(',', '.') + 'đ',
            'points': f"+{points_by_date.get(order.NgayDat, 0)}",
        }
        for order in orders
    ]

    if not purchase_history:
        purchase_history = [
            {
                'date': item.NgayThucHien.strftime('%d/%m/%Y'),
                'content': item.LyDo,
                'payment': '-',
                'points': f"{item.DiemThayDoi:+d}",
            }
            for item in point_history[:5]
        ]

    context = _get_customer_table_data()
    context.update({
        'customer': {
            'code': customer.MaKH,
            'name': customer.HoTen,
            'phone': customer.MaTK.TenDangNhap,
            'address': customer.DiaChi,
            'avatar_text': (customer.HoTen[:1] or 'K').upper(),
            'point_total': point_total,
        },
        'purchase_history': purchase_history,
    })
    return render(request, 'accounts/customer/customer_detail.html', context)


def customer_list_view(request):
    query = request.GET.get('q', '').strip()
    context = _get_customer_table_data(query)
    return render(request, 'accounts/customer/customer_list.html', context)

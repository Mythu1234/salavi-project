import re
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from cskh.models import LichSuTichDiem, TichDiem
from orders.models import DonHang

from .models import KhachHang


def _get_customer_table_data(query=''):
    customer_queryset = KhachHang.objects.select_related('user').order_by('MaKH')

    if query:
        customer_queryset = customer_queryset.filter(
            Q(HoTen__icontains=query)
            | Q(MaKH__icontains=query)
            | Q(user__username__icontains=query)
            | Q(DiaChi__icontains=query)
        )

    customers = [
        {
            'stt': index,
            'name': customer.HoTen,
            'code': customer.MaKH,
            'phone': customer.user.username,
            'address': customer.DiaChi,
        }
        for index, customer in enumerate(customer_queryset, start=1)
    ]
    return {
        'customers': customers,
        'query': query,
    }


def _generate_next_customer_code():
    customers = KhachHang.objects.all()
    max_num = 0
    for c in customers:
        if c.MaKH.startswith('KH'):
            try:
                num = int(c.MaKH[2:])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    return f"KH{max_num + 1:05d}"


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # 3a. Kiểm tra tài khoản tồn tại
            if not User.objects.filter(username=username).exists():
                messages.error(request, 'Tài khoản không tồn tại.', extra_tags='username')
                return render(request, 'accounts/login/login.html')
            
            # 3b. Kiểm tra mật khẩu
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('cskh:dashboard')
            else:
                messages.error(request, 'Mật khẩu không chính xác.', extra_tags='password')
                return render(request, 'accounts/login/login.html')
                
        except Exception:
            # 3c. Xử lý lỗi hệ thống
            messages.error(request, 'Hệ thống đang lỗi, không thể đăng nhập.')
            return render(request, 'accounts/login/login.html')

    return render(request, 'accounts/login/login.html')


def logout_view(request):
    logout(request)
    return redirect('cskh:guest_home')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()

        context = {
            'username': username,
            'name': name,
            'address': address,
        }

        try:
            # 3a. Kiểm tra tài khoản tồn tại
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Tài khoản đã tồn tại. Vui lòng nhập lại', extra_tags='username')
                return render(request, 'accounts/login/register.html', context)

            # 3b. Kiểm tra tên đăng nhập không hợp lệ (số điện thoại gồm 10 số)
            if not re.match(r'^\d{10}$', username):
                messages.error(request, 'Tên đăng nhập không hợp lệ. Vui lòng nhập lại', extra_tags='username')
                return render(request, 'accounts/login/register.html', context)

            # 4a/5a. Kiểm tra mật khẩu (Hoa, thường, số, ký tự đặc biệt)
            password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&].*$'
            if not re.match(password_regex, password):
                messages.error(request, 'Mật khẩu không hợp lệ.', extra_tags='password')
                return render(request, 'accounts/login/register.html', context)

            # 5b. Mật khẩu xác nhận không khớp
            if password != password_confirm:
                messages.error(request, 'Mật khẩu xác nhận không khớp với mật khẩu', extra_tags='password_confirm')
                return render(request, 'accounts/login/register.html', context)

            if not name:
                messages.error(request, 'Vui lòng nhập họ tên.', extra_tags='name')
                return render(request, 'accounts/login/register.html', context)

            # Tạo tài khoản
            user = User.objects.create_user(username=username, password=password)

            code = _generate_next_customer_code()
            KhachHang.objects.create(
                MaKH=code,
                user=user,
                HoTen=name,
                DiaChi=address
            )

            messages.success(request, 'Tạo tài khoản thành công')
            return redirect('accounts:login')

        except Exception:
            # 6b. Hệ thống lỗi
            messages.error(request, 'Hệ thống đang lỗi, không thể tạo tài khoản')
            return render(request, 'accounts/login/register.html', context)

    return render(request, 'accounts/login/register.html')


def forgot_password_view(request):
    step = request.GET.get('step', 'account')
    valid_steps = {'account', 'reset'}
    if step not in valid_steps:
        step = 'account'

    if request.method == 'POST':
        if step == 'account':
            username = request.POST.get('username', '').strip()
            
            # Kiểm tra tên đăng nhập không hợp lệ (Business rules: 10 số)
            if not re.match(r'^\d{10}$', username):
                messages.error(request, 'Tên đăng nhập không hợp lệ. Vui lòng nhập lại', extra_tags='username')
                return render(request, 'accounts/login/forgot_password.html', {'step': 'account'})
            
            # 3a. Kiểm tra tài khoản không tồn tại
            if not User.objects.filter(username=username).exists():
                messages.error(request, 'Tài khoản không tồn tại', extra_tags='username')
                return render(request, 'accounts/login/forgot_password.html', {'step': 'account'})
            
            # Thành công -> qua bước đổi mật khẩu
            request.session['reset_username'] = username
            return redirect(f"{request.path}?step=reset")
            
        elif step == 'reset':
            username = request.session.get('reset_username')
            if not username:
                return redirect(f"{request.path}?step=account")
                
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            
            # 8a. Kiểm tra mật khẩu (Hoa, thường, số, đặc biệt)
            password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&].*$'
            if not re.match(password_regex, password):
                messages.error(request, 'Mật khẩu không hợp lệ. Vui lòng nhập lại', extra_tags='password')
                return render(request, 'accounts/login/forgot_password.html', {'step': 'reset'})
                
            # 9b. Mật khẩu xác nhận không khớp
            if password != password_confirm:
                messages.error(request, 'Mật khẩu xác nhận không khớp với mật khẩu mới. Vui lòng nhập lại', extra_tags='password_confirm')
                return render(request, 'accounts/login/forgot_password.html', {'step': 'reset'})
            
            try:
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                
                # Xóa session và thông báo thành công
                if 'reset_username' in request.session:
                    del request.session['reset_username']
                messages.success(request, 'Cập nhật mật khẩu thành công')
                return redirect('accounts:login')
            except Exception:
                # 10b. Hệ thống lỗi
                messages.error(request, 'Hệ thống đang lỗi, không thể đổi mật khẩu')
                return render(request, 'accounts/login/forgot_password.html', {'step': 'reset'})

    # GET request logic
    if step == 'account' and 'reset_username' in request.session:
        del request.session['reset_username']
            
    context = {
        'step': step,
    }
    return render(request, 'accounts/login/forgot_password.html', context)


def customer_create_view(request):
    if request.method == 'POST':
        code = _generate_next_customer_code()
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        
        # 8a. Nếu thông tin bắt buộc bị bỏ trống
        if not name or not phone:
            messages.error(request, 'Không được để trống thông tin', extra_tags='customer_form')
            # Return same view with context to show form again
        # 8b. Nếu số điện thoại không hợp lệ
        elif not re.match(r'^\d{10}$', phone):
            messages.error(request, 'Số điện thoại chưa hợp lệ', extra_tags='phone')
        # Quy tắc: Số điện thoại không được trùng
        elif User.objects.filter(username=phone).exists():
            messages.error(request, 'Số điện thoại đã tồn tại', extra_tags='phone')
        else:
            try:
                user = User.objects.create_user(username=phone, password='Salavi123@password') # Default password
                KhachHang.objects.create(
                    MaKH=code,
                    user=user,
                    HoTen=name,
                    DiaChi=address
                )
                messages.success(request, 'Thêm khách hàng thành công')
                return redirect('accounts:customer_list')
            except Exception:
                messages.error(request, 'Không thể thêm khách hàng, vui lòng thử lại sau', extra_tags='system')

    context = _get_customer_table_data()
    context.update({
        'page_title': 'Salavi - Thêm khách hàng',
        'form_title': 'Thêm khách hàng',
        'confirm_title': 'XÁC NHẬN THÊM KHÁCH HÀNG',
        'customer_form': {
            'code': _generate_next_customer_code(),
            'name': request.POST.get('name', '') if request.method == 'POST' else '',
            'phone': request.POST.get('phone', '') if request.method == 'POST' else '',
            'address': request.POST.get('address', '') if request.method == 'POST' else '',
        },
        'save_label': 'Lưu',
    })
    return render(request, 'accounts/customer/customer_create.html', context)


def customer_edit_view(request, customer_code):
    customer = get_object_or_404(
        KhachHang.objects.select_related('user'),
        MaKH=customer_code,
    )

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        
        # 9a. Nếu thông tin bắt buộc bị bỏ trống
        if not name or not phone:
            messages.error(request, 'Không được để trống thông tin', extra_tags='customer_form')
        # 9b. Nếu số điện thoại không hợp lệ
        elif not re.match(r'^\d{10}$', phone):
            messages.error(request, 'Số điện thoại chưa hợp lệ', extra_tags='phone')
        else:
            try:
                if customer.user.username != phone:
                    # Check if new phone already taken by another user
                    if User.objects.filter(username=phone).exclude(pk=customer.user.pk).exists():
                        messages.error(request, 'Số điện thoại đã tồn tại', extra_tags='phone')
                    else:
                        customer.user.username = phone
                        customer.user.save()
                        customer.HoTen = name
                        customer.DiaChi = address
                        customer.save()
                        messages.success(request, 'Cập nhật thông tin khách hàng thành công')
                        return redirect('accounts:customer_list')
                else:
                    customer.HoTen = name
                    customer.DiaChi = address
                    customer.save()
                    messages.success(request, 'Cập nhật thông tin khách hàng thành công')
                    return redirect('accounts:customer_list')
            except Exception:
                messages.error(request, 'Không thể cập nhật thông tin, vui lòng thử lại sau', extra_tags='system')

    context = _get_customer_table_data()
    context.update({
        'page_title': 'Salavi - Chỉnh sửa thông tin khách hàng',
        'form_title': 'Chỉnh sửa thông tin khách hàng',
        'confirm_title': 'XÁC NHẬN CẬP NHẬT THÔNG TIN KHÁCH HÀNG',
        'customer_form': {
            'code': customer.MaKH,
            'name': request.POST.get('name', customer.HoTen) if request.method == 'POST' else customer.HoTen,
            'phone': request.POST.get('phone', customer.user.username) if request.method == 'POST' else customer.user.username,
            'address': request.POST.get('address', customer.DiaChi) if request.method == 'POST' else customer.DiaChi,
        },
        'save_label': 'Lưu',
    })
    return render(request, 'accounts/customer/customer_create.html', context)


def customer_delete_view(request, customer_code):
    customer = get_object_or_404(
        KhachHang.objects.select_related('user'),
        MaKH=customer_code,
    )

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        # 7a. Nếu người dùng bỏ trống ô lý do
        if not reason:
            messages.error(request, 'Không được để trống lý do xóa khách hàng', extra_tags='reason')
        # Quy tắc: Không cho phép xóa khách hàng đang phát sinh giao dịch
        elif DonHang.objects.filter(MaKH=customer).exists():
            messages.error(request, 'Không cho phép xóa khách hàng đang phát sinh giao dịch', extra_tags='system')
        else:
            try:
                user = customer.user
                customer.delete()
                user.delete()
                messages.success(request, 'Xóa khách hàng thành công')
                return redirect('accounts:customer_list')
            except Exception:
                messages.error(request, 'Không thể xóa, vui lòng thử lại sau', extra_tags='system')

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
        KhachHang.objects.select_related('user'),
        MaKH=customer_code,
    )
    point_total = (
        TichDiem.objects.filter(MaKH=customer).values_list('TongDiem', flat=True).first()
        or 0
    )
    point_history = list(
        LichSuTichDiem.objects.filter(MaKH=customer).select_related('MaNV').order_by('-NgayThucHien')
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
                'content': f"{item.LyDo} (Bởi: {item.MaNV.HoTen})" if hasattr(item, 'MaNV') and item.MaNV else item.LyDo,
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
            'phone': customer.user.username,
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

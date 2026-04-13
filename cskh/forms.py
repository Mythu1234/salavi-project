from django import forms
from .models import KhuyenMai

class KhuyenMaiForm(forms.ModelForm):
    class Meta:
        model = KhuyenMai
        fields = ['TenKhuyenMai', 'PhanTramGiam', 'MoTa', 'NgayBatDau', 'NgayKetThuc']
        widgets = {
            'TenKhuyenMai': forms.TextInput(attrs={
                'class': 'flex-1 w-full border border-gray-200 rounded-lg px-4 py-2 text-gray-800 text-[15px] outline-none focus:border-[#e58f8b] placeholder-gray-400',
                'placeholder': 'Nhập tên ưu đãi'
            }),
            'PhanTramGiam': forms.NumberInput(attrs={
                'class': 'flex-1 w-full border border-gray-200 rounded-lg px-4 py-2 text-gray-800 text-[15px] outline-none focus:border-[#e58f8b] placeholder-gray-400',
                'step': '0.01',
                'placeholder': 'VD: 15.00'
            }),
            'MoTa': forms.Textarea(attrs={
                'class': 'flex-1 w-full border border-gray-200 rounded-lg px-4 py-2 text-gray-800 text-[15px] outline-none focus:border-[#e58f8b] resize-none',
                'rows': 2,
                'placeholder': 'Nhập nội dung ưu đãi'
            }),
            'NgayBatDau': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'flex-1 w-full border border-gray-200 rounded-lg px-4 py-2 text-gray-800 text-[15px] outline-none focus:border-[#e58f8b]'
                }
            ),
            'NgayKetThuc': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'flex-1 w-full border border-gray-200 rounded-lg px-4 py-2 text-gray-800 text-[15px] outline-none focus:border-[#e58f8b]'
                }
            ),
        }

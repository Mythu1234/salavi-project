from django import forms
from .models import DoiTra

class DoiTraForm(forms.ModelForm):
    GhiChuXuLy = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-300 rounded-xl p-2.5 focus:outline-none focus:border-green-500 text-[13px]',
            'placeholder': 'Nhắc nhở, Ghi chú'
        })
    )

    class Meta:
        model = DoiTra
        fields = ['GhiChuXuLy']

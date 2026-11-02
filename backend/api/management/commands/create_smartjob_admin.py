from getpass import getpass

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from api.models import Users


class Command(BaseCommand):
    help = 'Create or reset a SmartJob administrator account'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Administrator email address')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        if not email or '@' not in email:
            raise CommandError('Vui lòng cung cấp email hợp lệ.')

        password = getpass('Mật khẩu admin: ')
        confirmation = getpass('Nhập lại mật khẩu: ')
        if password != confirmation:
            raise CommandError('Hai mật khẩu không khớp.')

        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc

        user = Users.objects.filter(email=email).first()
        if user and user.user_type != 'admin':
            raise CommandError('Email đã thuộc về tài khoản không phải admin.')

        if user:
            user.password_hash = make_password(password)
            user.is_active = True
            user.save(update_fields=['password_hash', 'is_active'])
            action = 'Đã cập nhật'
        else:
            Users.objects.create(
                email=email,
                password_hash=make_password(password),
                user_type='admin',
                is_active=True,
            )
            action = 'Đã tạo'

        self.stdout.write(self.style.SUCCESS(f'{action} tài khoản admin: {email}'))

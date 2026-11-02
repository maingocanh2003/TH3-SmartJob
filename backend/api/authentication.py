from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import Users


class SmartJobTokenAuthentication(BaseAuthentication):
    keyword = b'token'
    salt = 'smartjob.api.auth'
    max_age = 60 * 60 * 24 * 7

    def authenticate(self, request):
        authorization = get_authorization_header(request).split()
        if not authorization:
            return None

        if len(authorization) != 2 or authorization[0].lower() != self.keyword:
            return None

        try:
            user_id = signing.loads(
                authorization[1].decode('utf-8'),
                salt=self.salt,
                max_age=self.max_age,
            )
        except (BadSignature, SignatureExpired, UnicodeDecodeError) as exc:
            raise AuthenticationFailed('Token không hợp lệ hoặc đã hết hạn.') from exc

        try:
            user = Users.objects.get(user_id=user_id, is_active=True)
        except Users.DoesNotExist as exc:
            raise AuthenticationFailed('Tài khoản không tồn tại hoặc đã bị khóa.') from exc

        return user, None

    def authenticate_header(self, request):
        return 'Token'

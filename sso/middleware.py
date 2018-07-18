import json
import logging

from django.conf import settings
from requests.exceptions import ReadTimeout

from sso.utils import SSOUser, sso_api_client


logger = logging.getLogger(__name__)


class SSOUserMiddleware:

    MESSAGE_INVALID_JSON = (
        'SSO did not return JSON. A 502 may have occurred so SSO nginx '
        'redirected to http://sorry.great.gov.uk (see ED-2114)'
    )

    MESSAGE_SSO_UNREACHABLE = 'Unable to reach SSO'

    def process_request(self, request):
        request.sso_user = None
        session_id = request.COOKIES.get(settings.SSO_PROXY_SESSION_COOKIE)

        if session_id:
            try:
                sso_response = sso_api_client.user.get_session_user(session_id)
            except ReadTimeout:
                logger.error(self.MESSAGE_SSO_UNREACHABLE, exc_info=True)
            else:
                if sso_response.ok:
                    try:
                        sso_user_data = sso_response.json()
                    except json.JSONDecodeError:
                        raise ValueError(self.MESSAGE_INVALID_JSON)
                    else:
                        request.sso_user = SSOUser(
                            id=sso_user_data['id'],
                            email=sso_user_data['email'],
                            session_id=session_id,
                        )

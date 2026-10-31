import json
import urllib.request
import urllib.parse
from django.conf import settings


def _get_site():
    try:
        from .models import SiteSetting
        obj = SiteSetting.objects.filter(pk=1).first()
        if obj:
            return obj
    except Exception:
        pass
    class Dummy:
        whatsapp = getattr(settings, 'WA_NUMBER', '')
        phone_primary = getattr(settings, 'WA_NUMBER', '')
        business_name = 'Akshat Agni EV Motors'
    return Dummy()


def send_whatsapp(to_number, message):
    if not to_number or not message:
        return False
    num = ''.join(c for c in str(to_number) if c.isdigit())
    if not num:
        return False
    if len(num) == 10:
        num = '91' + num
    elif num.startswith('91') and len(num) == 12:
        pass
    elif len(num) > 12 and not num.startswith('91'):
        num = '91' + num[-10:]
    elif len(num) > 12 and num.startswith('91'):
        num = num[-12:]

    token = getattr(settings, 'WA_TOKEN', '') or getattr(settings, 'WHATSAPP_TOKEN', '')
    phone_id = getattr(settings, 'WA_PHONE_ID', '') or getattr(settings, 'WHATSAPP_PHONE_ID', '')
    if token and phone_id:
        try:
            url = f'https://graph.facebook.com/v18.0/{phone_id}/messages'
            data = json.dumps({
                'messaging_product': 'whatsapp',
                'to': num,
                'type': 'text',
                'text': {'body': message}
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            pass

    ultramsg_token = getattr(settings, 'ULTRAMSG_TOKEN', '')
    ultramsg_instance = getattr(settings, 'ULTRAMSG_INSTANCE', '')
    if ultramsg_token and ultramsg_instance:
        try:
            url = f'https://api.ultramsg.com/{ultramsg_instance}/messages/chat'
            payload = urllib.parse.urlencode({
                'token': ultramsg_token,
                'to': '+' + num if not str(num).startswith('+') else str(num),
                'body': message
            }).encode('utf-8')
            req = urllib.request.Request(url, data=payload)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            pass
    return False


def notify_admin(message):
    site = _get_site()
    admin_num = getattr(site, 'whatsapp', '') or getattr(site, 'phone_primary', '')
    return send_whatsapp(admin_num, message)


def notify_user(to_number, message):
    return send_whatsapp(to_number, message)

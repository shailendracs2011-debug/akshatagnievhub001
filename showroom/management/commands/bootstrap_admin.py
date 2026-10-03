import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help='Create the first admin and standard staff groups without resetting existing passwords.'
    def handle(self,*args,**kwargs):
        User=get_user_model(); username=os.getenv('ADMIN_USERNAME','admin'); password=os.getenv('ADMIN_PASSWORD','ChangeMe123!')
        user,created=User.objects.get_or_create(username=username,defaults={'is_staff':True,'is_superuser':True})
        if created: user.set_password(password); user.save(); self.stdout.write(self.style.SUCCESS(f'Created admin: {username}'))
        else: self.stdout.write(f'Admin {username} already exists; password not changed.')
        for name, codename_words in [('Sales Team',['sale','order','customer']),('Operations Team',['product','purchase','supplier','expense','ledger']),('Support Team',['servicequery','supportquery','enquiry']),('Content Team',['product','productgallery','galleryimage','category','offer'])]:
            group,_=Group.objects.get_or_create(name=name)
            perms=[]
            for p in Permission.objects.all():
                if any(w in p.codename for w in codename_words): perms.append(p)
            group.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS('Standard groups ensured.'))

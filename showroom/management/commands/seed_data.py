import base64
from pathlib import Path
from django.core.management.base import BaseCommand
from showroom.models import Category, Product, GalleryImage, SiteSetting

ROOT=Path(__file__).resolve().parents[3]
MEDIA=ROOT/'seed_media'

def data_url(path):
    if not path.exists(): return ''
    mime='image/png' if path.suffix.lower()=='.png' else 'image/jpeg'
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode('ascii')

class Command(BaseCommand):
    help='Seed Akshat Agni categories, products, site settings and gallery.'
    def handle(self,*args,**kwargs):
        cats={}
        specs=[
            ('E-Scooter','ई-स्कूटर','e-scooter','Electric scooters for city, range and heavy-duty use.'),
            ('E-Bike','ई-बाइक','e-bike','Motorcycle-style electric bikes — coming soon.'),
            ('E-Auto 7-Seater','ई-ऑटो 7-सीटर','e-auto-7-seater','L5 electric autos and loader variants — coming soon.'),
            ('Batteries','बैटरी','batteries','Lithium and lead-acid batteries.'),
            ('Spare Parts','स्पेयर पार्ट्स','spare-parts','EV scooter, bike, auto and general components.'),
            ('EV Services','ईवी सर्विस','ev-services','Service, battery, electrical and repair support.'),
        ]
        for name,hi,slug,desc in specs:
            c,_=Category.objects.update_or_create(slug=slug,defaults={'name':name,'name_hi':hi,'description':desc,'description_hi':desc,'published':True})
            cats[slug]=c
        scooter_segments=['Single Light','Double Light','High Range','City Ride','Heavy Duty']
        scooters=['SPORTS SL','SPORTS DL','ACTIVA 4G','ACTIVA 5G','EB THUNDER','EB MONARCH (OLA)','CHETAK ARA MAX','EB ACTIVA']
        for i,name in enumerate(scooters):
            seg=scooter_segments[i%len(scooter_segments)]
            Product.objects.update_or_create(slug=__import__('django.utils.text',fromlist=['slugify']).slugify(name),defaults={'name':name,'name_hi':name,'category':cats['e-scooter'],'segment':seg,'short_description':'Premium electric scooter for everyday mobility.','short_description_hi':'रोज़मर्रा की इलेक्ट्रिक मोबिलिटी के लिए प्रीमियम स्कूटर।','description':'Catalogue visual can be replaced from Admin. Pricing, battery, range and warranty are editable from Admin.','description_hi':'कैटलॉग विजुअल Admin से बदला जा सकता है। कीमत, बैटरी, रेंज और वारंटी Admin से संपादित करें।','price':0,'cost_price':0,'stock':0,'featured':i<4,'published':True,'coming_soon':False})
        autos=['EV L5 LUKA TRIMAX','EV L5 LUKA LOADER','EV L5 LUKA XL','EV L5 LUKA','EV L5 TRITRASH','EV L5 TRIPASS','EV L5 TRILOAD']
        for name in autos:
            slug=__import__('django.utils.text',fromlist=['slugify']).slugify(name)
            Product.objects.update_or_create(slug=slug,defaults={'name':name,'name_hi':name,'category':cats['e-auto-7-seater'],'segment':'L5 / 7-Seater','short_description':'Electric auto / loader model — coming soon.','description':'Model listing is ready; add the final catalogue replica image and commercial details from Admin.','published':True,'coming_soon':True,'featured':False})
        eb=['E-Bike Premium','E-Bike City','E-Bike Sport','E-Bike Classic']
        for name in eb:
            Product.objects.update_or_create(slug=__import__('django.utils.text',fromlist=['slugify']).slugify(name),defaults={'name':name,'name_hi':name,'category':cats['e-bike'],'segment':'Motorcycle-style EV','short_description':'Motorcycle-style electric bike — coming soon.','description':'Use Admin to upload the final realistic replica visual and specifications.','published':True,'coming_soon':True})
        site,_=SiteSetting.objects.get_or_create(pk=1)
        site.business_name='Akshat Agni EV Motors'; site.tagline='Shubh Shuruaat, Agni ki Raftaar'; site.tagline_hi='शुभ शुरुआत, अग्नि की रफ्तार'; site.phone_primary='9425969464'; site.phone_secondary='7974281559'; site.whatsapp='9425969464'; site.address='Maihar, Madhya Pradesh'; site.address_hi='मैहर, मध्य प्रदेश'; site.hero_title='Electric mobility, made simple.'; site.hero_title_hi='इलेक्ट्रिक मोबिलिटी, अब आसान।'; site.hero_subtitle='E-scooters, e-autos, batteries, spares and EV service — one connected showroom experience.'; site.hero_subtitle_hi='ई-स्कूटर, ई-ऑटो, बैटरी, स्पेयर और ईवी सर्विस — एक ही कनेक्टेड अनुभव।'; site.logo_data=data_url(MEDIA/'logo.jpg'); site.hero_image_data=data_url(MEDIA/'showroom2.jpeg'); site.save()
        files=sorted(MEDIA.glob('showroom*'))
        titles=['Showroom','Scooter display','Customer area','EV range','Showroom activity','Customer delivery','Scooter collection','Showroom front','EV display']
        for idx,p in enumerate(files):
            GalleryImage.objects.update_or_create(title=titles[idx] if idx<len(titles) else p.stem,defaults={'title_hi':titles[idx] if idx<len(titles) else p.stem,'description':'Real showroom photo','category':['SHOWROOM','SHOWROOM','DELIVERY','SHOWROOM','EVENT','DELIVERY','SHOWROOM','SHOWROOM','SERVICE'][idx%9],'image_data':data_url(p),'published':True,'featured':idx<3,'sort_order':idx})
        self.stdout.write(self.style.SUCCESS('Seed data ready.'))

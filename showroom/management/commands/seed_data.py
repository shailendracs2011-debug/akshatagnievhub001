import base64
from pathlib import Path
from django.core.management.base import BaseCommand
from showroom.images import file_to_data_url
from showroom.models import Category, Product, GalleryImage, SiteSetting

ROOT=Path(__file__).resolve().parents[3]
MEDIA=ROOT/'seed_media'

def data_url(path):
    """Read a seed photo and store it compressed as a WebP data URL."""
    return file_to_data_url(path)

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
        # A distinct one-line description per model. The card shows this line
        # instead of one repeated sentence for every scooter.
        scooters=[
            ('SPORTS SL','Single Light','Single Light model for short daily city rides.','रोज़ की छोटी शहर की सवारी के लिए सिंगल लाइट मॉडल।'),
            ('SPORTS DL','Double Light','Double Light model with a brighter headlamp for evening rides.','शाम की सवारी के लिए ब्राइटर हेडलैंप वाला डबल लाइट मॉडल।'),
            ('ACTIVA 4G','High Range','High Range model, built for longer trips between towns.','शहरों के बीच लंबी यात्रा के लिए हाई रेंज मॉडल।'),
            ('ACTIVA 5G','City Ride','City Ride model shaped for stop-and-go traffic.','रुक-रुक कर चलने वाली शहर की सवारी के लिए सिटी राइड मॉडल।'),
            ('EB THUNDER','Heavy Duty','Heavy Duty model for heavier loads and tougher daily use.','भारी लोड और कठिन रोज़मर्रा के लिए हेवी ड्यूटी मॉडल।'),
            ('EB MONARCH (OLA)','Single Light','Single Light model in a classic rounded body style.','क्लासिक गोल बॉडी डिज़ाइन वाला सिंगल लाइट मॉडल।'),
            ('CHETAK ARA MAX','Double Light','Double Light model with a wide, comfortable seat.','वाइड और आरामदायक सीट वाला डबल लाइट मॉडल।'),
            ('EB ACTIVA','High Range','High Range model with a large, roomy footboard.','बड़े और खुले फुटबोर्ड वाला हाई रेंज मॉडल।'),
        ]
        for i,(name,seg,desc,desc_hi) in enumerate(scooters):
            Product.objects.update_or_create(slug=__import__('django.utils.text',fromlist=['slugify']).slugify(name),defaults={'name':name,'name_hi':name,'category':cats['e-scooter'],'segment':seg,'short_description':desc,'short_description_hi':desc_hi,'description':f'{name} is available at our Maihar showroom, where you can see the {seg.lower()} model, ask for a test ride and get help with service, batteries and spares.','description_hi':f'{name} हमारे मैहर शोरूम में उपलब्ध है, जहाँ आप इस {seg.lower()} मॉडल को देख सकते हैं, टेस्ट राइड कर सकते हैं और सर्विस, बैटरी व स्पेयर पार्ट्स में मदद ले सकते हैं।','price':0,'cost_price':0,'stock':0,'featured':i<4,'published':True,'coming_soon':False})
        autos=['EV L5 LUKA TRIMAX','EV L5 LUKA LOADER','EV L5 LUKA XL','EV L5 LUKA','EV L5 TRITRASH','EV L5 TRIPASS','EV L5 TRILOAD']
        for name in autos:
            slug=__import__('django.utils.text',fromlist=['slugify']).slugify(name)
            Product.objects.update_or_create(slug=slug,defaults={'name':name,'name_hi':name,'category':cats['e-auto-7-seater'],'segment':'L5 / 7-Seater','short_description':'L5 electric auto / loader — launching soon at our showroom.','short_description_hi':'L5 इलेक्ट्रिक ऑटो / लोडर — हमारे शोरूम में जल्द आ रहा है।','description':'This L5 model is being prepared for launch. Visit our Maihar showroom to know the confirmed price, delivery time and warranty before it goes on sale.','description_hi':'इस L5 मॉडल को लॉन्च की तैयारी हो रही है। कीमत, डिलीवरी का समय और वारंटी की पक्की जानकारी के लिए हमारे मैहर शोरूम में आएँ।','published':True,'coming_soon':True,'featured':False})
        eb=['E-Bike Premium','E-Bike City','E-Bike Sport','E-Bike Classic']
        for name in eb:
            slug=__import__('django.utils.text',fromlist=['slugify']).slugify(name)
            Product.objects.update_or_create(slug=slug,defaults={'name':name,'name_hi':name,'category':cats['e-bike'],'segment':'Motorcycle-style EV','short_description':'Motorcycle-style electric bike — launching soon at our showroom.','short_description_hi':'मोटरसाइकिल जैसी इलेक्ट्रिक बाइक — हमारे शोरूम में जल्द आ रही है।','description':'A motorcycle-style electric bike, being prepared for launch. Visit our Maihar showroom for the confirmed price, range and warranty.','description_hi':'मोटरसाइकिल जैसी इलेक्ट्रिक बाइक, जिसकी लॉन्च की तैयारी हो रही है। कीमत, रेंज और वारंटी की पक्की जानकारी के लिए हमारे मैहर शोरूम में आएँ।','published':True,'coming_soon':True})
        site,_=SiteSetting.objects.get_or_create(pk=1)
        site.business_name='Akshat Agni EV Motors'; site.tagline='Shubh Shuruaat, Agni ki Raftaar'; site.tagline_hi='शुभ शुरुआत, अग्नि की रफ्तार'; site.phone_primary='9425969464'; site.phone_secondary='7974281559'; site.whatsapp='9425969464'; site.address='Maihar, Madhya Pradesh'; site.address_hi='मैहर, मध्य प्रदेश'; site.hero_title='Electric mobility, made simple.'; site.hero_title_hi='इलेक्ट्रिक मोबिलिटी, अब आसान।'; site.hero_subtitle='E-scooters, e-autos, batteries, spares and EV service — one connected showroom experience.'; site.hero_subtitle_hi='ई-स्कूटर, ई-ऑटो, बैटरी, स्पेयर और ईवी सर्विस — एक ही कनेक्टेड अनुभव।'; site.logo_data=data_url(MEDIA/'logo.jpg'); site.hero_image_data=data_url(MEDIA/'showroom2.jpeg'); site.save()
        files=sorted(MEDIA.glob('showroom*'))
        titles=['Showroom','Scooter display','Customer area','EV range','Showroom activity','Customer delivery','Scooter collection','Showroom front','EV display']
        for idx,p in enumerate(files):
            GalleryImage.objects.update_or_create(title=titles[idx] if idx<len(titles) else p.stem,defaults={'title_hi':titles[idx] if idx<len(titles) else p.stem,'description':'Real showroom photo','category':['SHOWROOM','SHOWROOM','DELIVERY','SHOWROOM','EVENT','DELIVERY','SHOWROOM','SHOWROOM','SERVICE'][idx%9],'image_data':data_url(p),'published':True,'featured':idx<3,'sort_order':idx})
        self.stdout.write(self.style.SUCCESS('Seed data ready.'))

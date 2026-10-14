

class VisitorCount(models.Model):
    count = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Visitors: {self.count}'


class SiteSetting(TimeStamped):
    business_name = models.CharField(max_length=180, default='Akshat Agni EV Motors')
    tagline = models.CharField(max_length=250, default='Shubh Shuruaat, Agni ki Raftaar')
    tagline_hi = models.CharField(max_length=250, default='शुभ शुरुआत, अग्नि की रफ्तार')
    phone_primary = models.CharField(max_length=30, default='9425969464')
    phone_secondary = models.CharField(max_length=30, default='7974281559')
    address = models.TextField(default='Maihar, Madhya Pradesh')
    address_hi = models.TextField(default='मैहर, मध्य प्रदेश')
    whatsapp = models.CharField(max_length=30, default='9425969464')
    about = models.TextField(blank=True)
    about_hi = models.TextField(blank=True)
    hero_title = models.CharField(max_length=220, default='Electric mobility, made simple.')
    hero_title_hi = models.CharField(max_length=220, default='इलेक्ट्रिक मोबिलिटी, अब आसान।')
    hero_subtitle = models.TextField(blank=True)
    hero_subtitle_hi = models.TextField(blank=True)
    hero_image_data = models.TextField(blank=True)
    logo_data = models.TextField(blank=True)
    authorized_person = models.CharField(max_length=150, blank=True)
    gst_number = models.CharField(max_length=30, blank=True)
    website = models.CharField(max_length=220, blank=True)
    signatory_name = models.CharField(max_length=150, blank=True)
    signature_data = models.TextField(blank=True)

    def __str__(self):
        return self.business_name

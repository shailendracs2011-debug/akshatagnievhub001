"""Canonical FAQ content for the showroom.

The questions a first-time EV buyer asks most often, with answers that stay
accurate without naming showroom-specific prices, ranges or warranty terms.

The website publishes the rows of the ``FAQItem`` table (Admin -> FAQ items),
which the owner can edit at any time. This list only fills a database that has
no FAQ rows yet, so a fresh install or a new environment is never left without
a FAQ section.

Keep this module free of model imports: the data migration imports it.
"""

FAQ_CONTENT = [
    {
        "question": "Do I need a driving licence to ride an electric scooter?",
        "question_hi": "क्या इलेक्ट्रिक स्कूटर चलाने के लिए ड्राइविंग लाइसेंस चाहिए?",
        "answer": "A driving licence is generally not required for qualifying low-speed electric scooters that meet applicable Indian regulations. High-speed electric scooters generally require a valid driving licence and registration. Requirements depend on the vehicle's certified classification.",
        "answer_hi": "भारतीय नियमों के अनुरूप कम गति वाले इलेक्ट्रिक स्कूटरों के लिए आमतौर पर ड्राइविंग लाइसेंस की आवश्यकता नहीं होती है। वहीं, तेज़ गति वाले इलेक्ट्रिक स्कूटरों के लिए आमतौर पर एक वैध ड्राइविंग लाइसेंस और पंजीकरण की ज़रूरत होती है। ये ज़रूरतें वाहन के प्रमाणित वर्गीकरण पर निर्भर करती हैं।",
    },
    {
        "question": "What is the real range I will get on one charge?",
        "question_hi": "एक चार्ज पर असली रेंज कितनी मिलेगी?",
        "answer": "The riding range depends on the scooter model, battery capacity, rider and passenger weight, speed, road conditions and riding style. We can help you choose a model based on your daily travel distance and range requirements. Always check the manufacturer's stated range for the specific model.",
        "answer_hi": "राइडिंग रेंज स्कूटर के मॉडल, बैटरी की क्षमता, राइडर और यात्री के वजन, स्पीड, सड़क की स्थिति और राइडिंग स्टाइल पर निर्भर करती है। हम आपकी रोज़ाना की यात्रा की दूरी और रेंज की ज़रूरतों के आधार पर सही मॉडल चुनने में आपकी मदद कर सकते हैं। हमेशा उस खास मॉडल के लिए निर्माता द्वारा बताई गई रेंज ज़रूर चेक करें।",
    },
    {
        "question": "How long does charging take, and what does it cost?",
        "question_hi": "चार्जिंग में कितना समय लगता है और खर्चा कितना आता है?",
        "answer": "Charging time depends on the battery capacity, charger rating and remaining battery level. Charging an electric scooter at home is generally convenient and economical. Your charging cost depends on your electricity tariff and the energy consumed. We can help you estimate the cost for your selected model.",
        "answer_hi": "चार्जिंग का समय बैटरी की क्षमता, चार्जर की रेटिंग और बैटरी के मौजूदा स्तर पर निर्भर करता है। घर पर इलेक्ट्रिक स्कूटर को चार्ज करना आमतौर पर सुविधाजनक और किफायती होता है। चार्जिंग का खर्च आपके बिजली के टैरिफ और इस्तेमाल की गई बिजली पर निर्भर करता है। आपके चुने हुए मॉडल के लिए आने वाले खर्च का अनुमान लगाने में हम आपकी मदद कर सकते हैं।",
    },
    {
        "question": "What happens during power cuts?",
        "question_hi": "बिजली कटने पर क्या होता है?",
        "answer": "You can continue using your electric scooter as long as the battery has sufficient charge. During a power cut, you may need to wait until electricity is restored to recharge it. Planning your charging schedule helps avoid inconvenience.",
        "answer_hi": "जब तक बैटरी में पर्याप्त चार्ज है, तब तक आप अपने इलेक्ट्रिक स्कूटर का इस्तेमाल जारी रख सकते हैं। बिजली कट जाने पर, इसे रिचार्ज करने के लिए आपको बिजली वापस आने का इंतज़ार करना पड़ सकता है। अपने चार्जिंग शेड्यूल की योजना बनाने से आप असुविधा से बच सकते हैं।",
    },
    {
        "question": "How long does the battery last, and when is it replaced?",
        "question_hi": "बैटरी कितने साल चलती है और कब बदलनी पड़ती है?",
        "answer": "Battery life depends on battery type, usage, charging habits, temperature and maintenance. Over time, battery capacity and riding range may decrease. Replacement depends on battery condition and performance. Please refer to the manufacturer's warranty and replacement guidelines for your model.",
        "answer_hi": "बैटरी की उम्र बैटरी के प्रकार, इस्तेमाल, चार्ज करने के तरीके, तापमान और रखरखाव पर निर्भर करती है। समय के साथ, बैटरी की क्षमता और राइडिंग रेंज कम हो सकती है। बैटरी को बदलने की ज़रूरत उसकी स्थिति और परफॉरमेंस पर निर्भर करती है। कृपया अपने मॉडल के लिए निर्माता की वारंटी और बैटरी बदलने से जुड़े दिशा-निर्देश देखें।",
    },
    {
        "question": "What does servicing involve, and how often is it needed?",
        "question_hi": "सर्विस में क्या होता है और कितनी बार करवानी पड़ती है?",
        "answer": "EV servicing may include checking the brakes, tyres, lights, suspension, electrical connections, battery health and other key components. Service intervals vary by model. We recommend following the manufacturer's service schedule to maintain safety, performance and warranty eligibility.",
        "answer_hi": "ईवी की सर्विसिंग में ब्रेक, टायर, लाइट, सस्पेंशन, इलेक्ट्रिकल कनेक्शन, बैटरी की स्थिति और अन्य मुख्य पुर्जों की जांच शामिल हो सकती है। सर्विस का अंतराल हर मॉडल के हिसाब से अलग-अलग होता है। सुरक्षा, परफॉरमेंस और वारंटी बनाए रखने के लिए, हम आपको निर्माता (मैन्युफैक्चरर) के सर्विस शेड्यूल का पालन करने की सलाह देते हैं।",
    },
    {
        "question": "Can I buy on EMI or finance?",
        "question_hi": "क्या EMI या फ़ाइनेंस पर खरीद सकते हैं?",
        "answer": "Finance or EMI options may be available for eligible customers, subject to the finance provider's policies, approval and applicable terms. The down payment, interest rate, tenure and monthly instalment depend on the selected vehicle and approved loan offer. Contact us to explore available options.",
        "answer_hi": "पात्र ग्राहकों के लिए फाइनेंस या EMI के विकल्प उपलब्ध हो सकते हैं, जो फाइनेंस प्रदाता की नीतियों, मंजूरी और लागू शर्तों के अधीन होंगे। डाउन पेमेंट, ब्याज दर, अवधि और मासिक किस्त का निर्धारण चुने गए वाहन और स्वीकृत लोन ऑफर के आधार पर होगा। उपलब्ध विकल्पों के बारे में जानने के लिए हमसे संपर्क करें।",
    },
    {
        "question": "Can I exchange my old vehicle for an EV?",
        "question_hi": "क्या पुराना वाहन बदलकर EV ले सकते हैं?",
        "answer": "You can contact Akshat Agni EV Hub to enquire about exchanging your existing vehicle for an electric scooter. Exchange availability and value depend on the vehicle's condition, documents, valuation and any applicable exchange programme. Final terms will be confirmed at the time of purchase.",
        "answer_hi": "आप अपने मौजूदा वाहन को इलेक्ट्रिक स्कूटर से बदलने के बारे में पूछताछ करने के लिए 'अक्षत अग्नि ईवी हब' (Akshat Agni EV Hub) से संपर्क कर सकते हैं। एक्सचेंज की सुविधा और वाहन की कीमत, उस वाहन की स्थिति, उसके दस्तावेज़ों, उसके मूल्यांकन और लागू होने वाले किसी भी एक्सचेंज प्रोग्राम पर निर्भर करेगी। खरीदारी के समय अंतिम शर्तें तय की जाएंगी।",
    },
]

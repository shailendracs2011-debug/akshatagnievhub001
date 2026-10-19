# Website redesign — working notes

**Status:** in progress. Not pushed to GitHub — the owner reviews on the local machine first.

Local run:

```bash
.venv\Scripts\python.exe manage.py runserver 8000
```

Login: `admin` / `Admin@12345` (from `.env`).

---

## Decisions taken (owner approved)

| Decision | Choice |
| --- | --- |
| Brand palette | Green `#0B7A4F` primary + Amber `#EA7317` CTA |
| Unconfirmed facts | Shown as visible bracketed placeholders |
| Type | Noto Sans variable, self-hosted, 2 woff2 files (Latin + Devanagari) |
| Spacing / radius / buttons | 8px scale · 8/12/16/24px + pill · min 48px buttons |

Full token set lives in `:root` of `static/css/site.css` — re-theme by editing those only.

---

## Done

**Foundation**

- [x] Design system written to `static/css/site.css` (tokens, buttons, forms, cards, focus states)
- [x] Self-hosted Noto Sans: `static/fonts/noto-sans-latin.woff2` (35 KB) + `noto-sans-devanagari.woff2` (97 KB), loaded via `static/css/fonts.css`
- [x] `static/js/site.js` — drawer, compare tray, FAQ accordion, savings + EMI calculators, gallery lightbox, product gallery swipe, lazy map
- [x] `showroom/i18n.py` — every new user-facing string in both English and Hindi, plus the placeholder table
- [x] `showroom/templatetags/showroom_tags.py` — `lookup`, `whatsapp_url` filters
- [x] Scooter silhouette placeholder SVG (replaces the old "EV MODEL" text block)

**Backend**

- [x] `Product` spec fields: `range_km`, `top_speed_kmph`, `battery_type`, `battery_warranty_years`, `licence_required`, `colours`, `load_capacity_kg`, `who_is_this_for`(+hi), `price_label`
- [x] `Product.spec_chips` and `Product.spec_rows` helpers
- [x] `SiteSetting` fields: hero web/mobile photos, offer banner (text/image/link), landmark, timings, map URLs, 4 × "why choose us" facts, 5 savings-calculator defaults
- [x] New models `Testimonial` and `FAQItem`
- [x] `Enquiry.request_type` + `Enquiry.preferred_day` (reused for test ride and part requests — no new tables)
- [x] `GalleryImage.caption` property
- [x] Upload pipeline re-encodes every image to **WebP ≤150 KB** (`forms.image_to_data_url`)
- [x] New views: `compare`, `test_ride`, `ask_part`, `track_request` + success pages
- [x] New routes wired in `showroom/urls.py`
- [x] Admin: new product fieldsets, `Testimonial` + `FAQItem` registered, `Enquiry.request_type` filter
- [x] Migration `0006_faqitem_testimonial_enquiry_preferred_day_and_more` applied

**Templates**

- [x] `base.html` — sticky compact header, language toggle always visible, persistent Call button, hamburger drawer, E-Auto nav hidden until a model exists, offer banner (hidden when empty), new footer (both phones tap-to-call, WhatsApp, timings, Get directions, tap-to-load map, **visitor counter removed**), sticky mobile Call + WhatsApp bar
- [x] `templates/partials/product_card.html` — image slot with silhouette placeholder, name, price with ex-showroom/on-road label, 3 spec chips, per-model description, "Call for price" + WhatsApp, Compare checkbox
- [x] `templates/partials/vehicle_placeholder.html`
- [x] `compare.html`, `track_request.html`, `ask_part.html`, `ask_part_success.html`, `test_ride.html`, `test_ride_success.html`

---

## Remaining

- [ ] `home.html` — hero rewrite, actionable service tiles, why-choose-us, savings calc, EMI calc, FAQ accordion, testimonials block
- [ ] `category.html` — use the new product card partial
- [ ] `product_detail.html` — gallery, price block, full spec table, "Who is this for?", test-ride form, WhatsApp with model prefilled
- [ ] `gallery.html` — responsive grid + lightbox + editable captions
- [ ] `enquiry.html`, `ticket_form.html`, `book_order.html`, `ticket_success.html` — bilingual copy + new form styling
- [ ] FAQ seed command (8 starter questions from the brief, answers flagged `needs_confirmation`)
- [ ] `requirements.txt` — add `reportlab` explicitly
- [ ] Image compression of the existing `static/images/*.jpg` and `seed_media/*`
- [ ] Lighthouse "after" run + before/after report
- [ ] Final a11y pass (alt text, focus order, contrast)

---

## Lighthouse — before

Measured on `http://127.0.0.1:8000/` with Lighthouse mobile emulation, before any redesign work.

| Category | Score |
| --- | --- |
| Performance | **33** |
| Accessibility | **92** |
| Best practices | **96** |
| SEO | **91** |

LCP 9.6 s · TBT 1,170 ms · CLS 0

Main problems: no text compression, no cache headers, render-blocking resources, oversized non-responsive images, no modern image formats, colour-contrast failures, no meta description.

---

## Notes / gotchas

- Images are stored as base64 data URLs in the DB, so the home page HTML is already ~1.7 MB before the new assets. Converting the seeded images to WebP is the single biggest performance win available.
- `reportlab` is imported directly by `showroom/views.py` but only reaches the venv as a transitive dependency of `xhtml2pdf`. It must be listed explicitly in `requirements.txt`.
- The `venv/` folder is an empty leftover; `.venv/` is the working environment.

# Website redesign — working notes

**Status:** redesign complete and verified locally. **Not pushed to GitHub** — the owner reviews on the local machine first.

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
| Minimum text size | 16 px for all content text; 14 px for badges/eyebrows only |
| Images | Stored as WebP data URLs, served over real URLs so they lazy-load and cache |

Full token set lives in `:root` of `static/css/site.css` — re-theme by editing those only.

---

## Done

**Foundation**

- [x] Design system in `static/css/site.css` (tokens, buttons, forms, cards, focus states, 16 px floor)
- [x] Self-hosted Noto Sans: `static/fonts/noto-sans-latin.woff2` (35 KB) + `noto-sans-devanagari.woff2` (97 KB). The `@font-face` rules live in `site.css` so the page needs one stylesheet, not two round trips.
- [x] `static/js/site.js` — drawer, compare tray, FAQ accordion, savings + EMI calculators, gallery lightbox, product gallery swipe, lazy map
- [x] `showroom/i18n.py` — every new user-facing string in both English and Hindi, plus the placeholder table
- [x] `showroom/templatetags/showroom_tags.py` — `lookup`, `whatsapp_url` filters
- [x] Scooter silhouette placeholder SVG (replaces the old "EV MODEL" text block)
- [x] `static/images/favicon.svg` (green/amber flame mark, also used as the touch icon)

**Backend**

- [x] `Product` spec fields: `range_km`, `top_speed_kmph`, `battery_type`, `battery_warranty_years`, `licence_required`, `colours`, `load_capacity_kg`, `who_is_this_for`(+hi), `price_label`
- [x] `Product.spec_chips` and `Product.spec_rows` helpers
- [x] `SiteSetting` fields: hero web/mobile photos, offer banner (text/image/link), landmark, timings, map URLs, 4 × "why choose us" facts, 5 savings-calculator defaults
- [x] The ERP settings form (`/erp/settings/`) now exposes the hero, logo and offer-banner image uploads as well as the text fields, so the owner can fill everything in one place
- [x] New models `Testimonial` and `FAQItem`
- [x] `Enquiry.request_type` + `Enquiry.preferred_day` (reused for test ride and part requests — no new tables)
- [x] `GalleryImage.caption` property, `thumb_data` on Product / ProductGallery / GalleryImage / Testimonial
- [x] Upload pipeline re-encodes every image to **WebP ≤150 KB** (`forms.image_to_data_url`)
- [x] New views: `compare`, `test_ride`, `ask_part`, `track_request` + success pages
- [x] New routes wired in `showroom/urls.py`
- [x] Admin: new product fieldsets, `Testimonial` + `FAQItem` registered, `Enquiry.request_type` filter
- [x] Migrations `0006_faqitem_testimonial_enquiry_preferred_day_and_more` and `0007_galleryimage_thumb_data_product_thumb_data_and_more` applied
- [x] `GZipMiddleware` added to `config/settings.py`

**Images — the biggest performance lever**

The photos live in the database as base64 data URLs, so a template that inlines one ships the whole picture inside the HTML and the browser cannot lazy-load it. The redesign stopped doing that:

- [x] `showroom/images.py` — shared WebP compression, thumbnail and avatar helpers, plus `resize_data_url` for on-the-fly downscaling
- [x] `showroom/management/commands/optimize_images.py` — re-encodes every stored image and rebuilds grid thumbnails (testimonials get a 128 px avatar, not a 480 px tile)
- [x] `showroom.views.media_image` — `GET /img/<model>/<pk>/` serves a stored image as a real, cacheable URL. `?t=1` returns the stored thumbnail, `?w=<px>` returns a copy resized to that width
- [x] `showroom.views.media_site_image` — `GET /img/site/<name>/` does the same for the hero and logo
- [x] Resized variants are cached in memory, so a repeat request is a cache hit instead of another Pillow encode (cold 1.3 s → warm 70 ms)
- [x] Every public template now points at those URLs instead of inlining base64. Homepage HTML fell from **460 KB to 29 KB**
- [x] The logo is requested at 96 px (24 KB → 2.2 KB) and the hero is responsive — 640 px on phones (48 KB), 1200 px on desktop (131 KB)
- [x] The Devanagari `unicode-range` no longer covers the currency block, so English pages stop downloading the 99 KB Devanagari file just to draw `₹`

**Templates**

- [x] `base.html` — sticky compact header, language toggle always visible, persistent Call button, hamburger drawer, E-Auto nav hidden until a model exists, offer banner (hidden when empty), new footer (both phones tap-to-call, WhatsApp, timings, Get directions, tap-to-load map, **visitor counter removed**), sticky mobile Call + WhatsApp bar
- [x] `templates/home.html` — new hero, search, category quick nav, service tiles, featured models, why-choose-us, savings calculator, EMI calculator, FAQ, gallery preview, testimonials, CTA
- [x] `templates/category.html` — catalog grid built on the product card partial
- [x] `templates/product_detail.html` — gallery, price block, full spec table, "Who is this for?", test-ride form, WhatsApp with model prefilled
- [x] `templates/gallery.html` — responsive grid + lightbox + editable captions
- [x] `templates/partials/product_card.html` — image slot with silhouette placeholder, name, price with ex-showroom/on-road label, 3 spec chips, per-model description, "Call for price" + WhatsApp, Compare checkbox
- [x] `templates/partials/vehicle_placeholder.html`
- [x] `compare.html`, `track_request.html`, `ask_part.html`, `ask_part_success.html`, `test_ride.html`, `test_ride_success.html`
- [x] `enquiry.html`, `ticket_form.html`, `book_order.html`, `ticket_success.html`, `order_success.html` — bilingual copy + new form styling

**Content**

- [x] `showroom/management/commands/seed_faq.py` — 8 starter questions from the brief, every answer marked `[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]`
- [x] `seed_data.py` — per-model one-line descriptions (the old card repeated one sentence for every scooter) and customer-facing copy with no internal wording left in public templates

---

## Verified in a real browser (Chrome via DevTools Protocol)

| Check | Result |
| --- | --- |
| Horizontal overflow, 390 px and 1440 px | none (`scrollWidth == clientWidth`) |
| Smallest content text | 16 px (body, chips, buttons, prices, footer headings) |
| Contrast on `.mrp` / `.chip-placeholder` | 5.4 : 1 (was 4.0 : 1, failed WCAG AA) |
| Contrast on footer headings | 7.7 : 1 |
| Savings calculator | petrol ₹17,033/yr → EV ₹2,336/yr → saves ₹14,697/yr |
| EMI calculator | ₹2,290/month, ₹82,425 total |
| Compare tray | ticks persist to `localStorage`, tray shows names + "Compare now" + "Clear all" |
| FAQ accordion | 8 items, panel expands 0 → 102 px, `aria-expanded` toggles |
| Nav drawer | opens on tap |
| Lightbox | opens on gallery tap |
| Devanagari webfont | **not** downloaded on English pages, downloaded on Hindi pages |
| Heading order | 14 public pages checked, no skipped levels |
| Broken images | 0 across home / gallery / category / product |
| Deferred sections | `content-visibility` sections render and load their images once scrolled to |
| ERP | all 12 ERP routes return 200, ERP untouched |
| Django admin | all models incl. `Testimonial`, `FAQItem`, `SiteSetting` load |

---

## Lighthouse — before / after

Mobile emulation, Lighthouse 12, same machine, same server.

### Before (the original site)

| Category | Score |
| --- | --- |
| Performance | **33** |
| Accessibility | **92** |
| Best practices | **96** |
| SEO | **91** |

LCP 9.6 s · TBT 1,170 ms · CLS 0

Main problems: no text compression, no cache headers, render-blocking resources, oversized non-responsive images, no modern image formats, colour-contrast failures, no meta description.

### After

Median of 3 runs per page (mobile emulation, Lighthouse 12, same machine and server).

| Page | Performance | Accessibility | Best practices | SEO | LCP | TBT | CLS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Home `/` | **77** | **100** | **100** | **100** | 2.35 s | 927 ms | 0 |
| Category `/category/e-scooter/` | **90** | **100** | **100** | **100** | 1.66 s | 407 ms | 0 |
| Product `/product/eb-thunder/` | **83** | **100** | **100** | **100** | 1.93 s | 648 ms | 0 |
| Gallery `/gallery/` | **92** | **100** | **100** | **100** | 2.19 s | 312 ms | 0 |
| Service `/service/` | **95** | **100** | **100** | **100** | 2.13 s | 212 ms | 0 |

Every accessibility, best-practice and SEO audit now passes on every page tested.

### Page weight

| Page | Before | After (HTML) | After (gzipped) |
| --- | --- | --- | --- |
| `/` | 460,848 B | 29,371 B | ~6,300 B |
| `/gallery/` | 372,561 B | 10,375 B | ~2,400 B |
| `/category/e-scooter/` | 71,742 B | 21,016 B | ~3,500 B |
| `/product/eb-thunder/` | 68,418 B | 17,696 B | ~4,100 B |

### Where the remaining home-page TBT comes from

Style + layout is still the largest main-thread item (~2.5 s under Lighthouse's 4× CPU throttle, so roughly 600 ms on a real device). Three things were tried and kept:

- [x] `content-visibility: auto` on the below-the-fold sections — Perf 74 → 77, TBT 1042 ms → 927 ms, CLS still 0
- [x] `backdrop-filter` removed from the sticky header — no measurable score change, but it drops a per-scroll repaint on low-end phones
- [x] One stylesheet instead of two — the `@font-face` rules moved into `site.css`, so the first paint needs one request, not two

---

## Left for the owner (visible placeholders on the live site)

These are deliberately shown to the customer as bracketed placeholders rather than invented facts. Fill them in the Django admin and they disappear.

| Placeholder | Where to fill it |
| --- | --- |
| `[TO BE UPDATED]` on model cards | Admin → Products → Range / Top speed / Battery / Price |
| `[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]` | Admin → FAQ items (8 seeded questions) |
| `[SHOWROOM_TIMINGS]` | ERP → Settings → Opening hours |
| `[HERO_PHOTO]` | ERP → Settings → Hero Photo (web + mobile) — upload fields are on the form |
| `[SHOWROOM_LANDMARK]` | ERP → Settings → Landmark |
| `[BRAND_AUTHORISATION]` | ERP → Settings → Why brand authorised |
| `[WARRANTY_TERMS]`, `[FREE_FIRST_SERVICE]`, `[LOCAL_SERVICE_CENTRE]` | ERP → Settings → the other three "why choose us" fields |
| `[OFFER_TEXT]`, `[MAP_EMBED_URL]` | ERP → Settings → Offer banner / map |

Both places work: the ERP settings page (`/erp/settings/`) and the Django admin (`/admin/showroom/sitesetting/`) expose the same fields, including the hero, logo and offer-banner image uploads.

Other owner actions:

- [ ] Upload a **phone-sized hero photo** (under ~60 KB) so the mobile hero drops from 48 KB to a few KB
- [ ] Confirm the seeded testimonial — it is published and shows on the home page
- [ ] Add the real product photos; models with no photo fall back to the silhouette placeholder
- [ ] Review the 8 seeded FAQ answers, or write real ones

---

## Notes / gotchas

- **Django caches templates in memory.** With `runserver --noreload`, a template edit is not picked up until the server restarts. Restart after changing any template.
- **`GZipMiddleware` does not compress static files in development.** Django's dev static-file handler answers `/static/...` before the middleware chain runs. In production WhiteNoise and the Vercel CDN compress them, so the real-world numbers are better than the local ones.
- **Do not edit templates with PowerShell `Set-Content` / `Out-File`.** They re-encode UTF-8 and turn Devanagari and emoji into mojibake. This happened once during the redesign (`templates/home.html` was double-encoded and has been repaired). Use the editor tools, or Python with explicit `encoding='utf-8'`.
- **The Devanagari `unicode-range` deliberately excludes `U+20B8-20E7`** (the currency block, which contains `₹`). Including it made every English page download the 99 KB Devanagari file just to draw a rupee sign.
- **Images live as base64 data URLs in the DB.** That is the existing app design and it keeps local SQLite and hosted PostgreSQL portable. The fix was to stop inlining them in HTML, not to change storage.
- `reportlab` is imported directly by `showroom/views.py` but only reaches the venv as a transitive dependency of `xhtml2pdf`. It is now listed explicitly in `requirements.txt`.
- The `venv/` folder is an empty leftover; `.venv/` is the working environment.
- One commit sits ahead of `origin/main` (`20b643a`). Nothing has been pushed.

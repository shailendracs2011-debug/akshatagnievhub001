/* Akshat Agni EV Motors — public site behaviour.
   Vanilla JS, no dependencies. Loaded with `defer`. */
(function () {
  'use strict';

  var COMPARE_KEY = 'aaev_compare';
  var MAX_COMPARE = 3;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function readCompare() {
    try {
      var raw = window.localStorage.getItem(COMPARE_KEY);
      var parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed.slice(0, MAX_COMPARE) : [];
    } catch (e) { return []; }
  }

  function writeCompare(list) {
    try { window.localStorage.setItem(COMPARE_KEY, JSON.stringify(list)); } catch (e) { /* private mode */ }
  }

  /* ---------------- Navigation drawer ---------------- */
  function initDrawer() {
    var drawer = $('#nav-drawer');
    var openers = $$('[data-drawer-open]');
    if (!drawer) return;

    function open() {
      drawer.setAttribute('data-open', 'true');
      drawer.removeAttribute('aria-hidden');
      document.body.style.overflow = 'hidden';
      var first = $('.drawer-panel a, .drawer-close', drawer);
      if (first) first.focus();
    }
    function close() {
      drawer.setAttribute('data-open', 'false');
      drawer.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      var opener = $('[data-drawer-open]');
      if (opener) opener.focus();
    }

    openers.forEach(function (btn) {
      btn.addEventListener('click', function (e) { e.preventDefault(); open(); });
    });
    $$('.drawer-close, .drawer-backdrop', drawer).forEach(function (el) {
      el.addEventListener('click', close);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.getAttribute('data-open') === 'true') close();
    });
  }

  /* ---------------- Compare ---------------- */
  function initCompare() {
    var boxes = $$('[data-compare-slug]');
    var tray = $('#compare-tray');
    if (!boxes.length) return;

    var saved = readCompare();

    function syncChecks() {
      var list = readCompare();
      boxes.forEach(function (box) {
        box.checked = list.some(function (item) { return item.slug === box.getAttribute('data-compare-slug'); });
      });
    }

    function render() {
      var list = readCompare();
      if (!tray) return;
      var slots = $('#compare-slots', tray);
      var count = $('#compare-count', tray);
      var cta = $('#compare-cta', tray);
      var clear = $('#compare-clear', tray);
      if (slots) {
        slots.innerHTML = '';
        list.forEach(function (item) {
          var span = document.createElement('span');
          span.className = 'compare-slot';
          span.textContent = item.name;
          slots.appendChild(span);
        });
      }
      if (count) count.textContent = list.length;
      if (cta) {
        if (list.length >= 2) {
          cta.removeAttribute('aria-disabled');
          cta.href = '/compare/?ids=' + list.map(function (i) { return i.slug; }).join(',');
        } else {
          cta.setAttribute('aria-disabled', 'true');
          cta.href = '#';
        }
      }
      if (clear) clear.hidden = list.length === 0;
      tray.setAttribute('data-visible', list.length > 0 ? 'true' : 'false');
    }

    boxes.forEach(function (box) {
      var slug = box.getAttribute('data-compare-slug');
      var name = box.getAttribute('data-compare-name') || slug;
      if (saved.some(function (i) { return i.slug === slug; })) box.checked = true;
      box.addEventListener('change', function () {
        var list = readCompare();
        var index = list.findIndex(function (i) { return i.slug === slug; });
        if (box.checked) {
          if (index === -1) {
            if (list.length >= MAX_COMPARE) {
              box.checked = false;
              var note = $('#compare-note');
              if (note) {
                note.textContent = note.getAttribute('data-max') || '';
                note.hidden = false;
                window.setTimeout(function () { note.hidden = true; }, 3500);
              }
              return;
            }
            list.push({ slug: slug, name: name });
          }
        } else if (index > -1) {
          list.splice(index, 1);
        }
        writeCompare(list);
        render();
      });
    });

    var clear = $('#compare-clear');
    if (clear) {
      clear.addEventListener('click', function (e) {
        e.preventDefault();
        writeCompare([]);
        syncChecks();
        render();
      });
    }

    syncChecks();
    render();
  }

  /* ---------------- FAQ accordion ---------------- */
  function initFaq() {
    $$('.faq-item').forEach(function (item) {
      var btn = $('.faq-q', item);
      var panel = $('.faq-a', item);
      if (!btn || !panel) return;
      btn.addEventListener('click', function () {
        var isOpen = item.getAttribute('data-open') === 'true';
        item.setAttribute('data-open', isOpen ? 'false' : 'true');
        btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
        panel.hidden = isOpen;
      });
    });
  }

  /* ---------------- Savings calculator ---------------- */
  function initSavings() {
    var root = $('#savings-calc');
    if (!root) return;

    function num(id) {
      var el = $('#' + id, root);
      var v = el ? parseFloat(el.value) : 0;
      return isFinite(v) ? v : 0;
    }

    function format(n) {
      return '₹' + Math.round(n).toLocaleString('en-IN');
    }

    function update() {
      var dailyKm = num('s-daily-km');
      var petrolPrice = num('s-petrol-price');
      var petrolMileage = num('s-petrol-mileage');
      var powerRate = num('s-power-rate');
      var evKmPerUnit = num('s-ev-km');
      var days = 365;

      var petrolYear = petrolMileage > 0 ? (dailyKm * days / petrolMileage) * petrolPrice : 0;
      var evYear = evKmPerUnit > 0 ? (dailyKm * days / evKmPerUnit) * powerRate : 0;
      var saving = petrolYear - evYear;

      var petrolOut = $('#s-petrol-year');
      var evOut = $('#s-ev-year');
      var saveOut = $('#s-saving');
      var labelOut = $('#s-saving-label');
      var labelAlt = root.getAttribute('data-extra-label') || '';

      if (petrolOut) petrolOut.textContent = format(petrolYear);
      if (evOut) evOut.textContent = format(evYear);
      if (saveOut) saveOut.textContent = format(Math.abs(saving));
      if (labelOut) labelOut.textContent = saving < 0 ? labelAlt : (root.getAttribute('data-save-label') || '');
    }

    $$('input', root).forEach(function (input) { input.addEventListener('input', update); });
    update();
  }

  /* ---------------- EMI calculator ---------------- */
  function initEmi() {
    var root = $('#emi-calc');
    if (!root) return;

    function num(id) {
      var el = $('#' + id, root);
      var v = el ? parseFloat(el.value) : 0;
      return isFinite(v) ? v : 0;
    }
    function format(n) { return '₹' + Math.round(n).toLocaleString('en-IN'); }

    function update() {
      var price = num('e-price');
      var down = num('e-down');
      var rate = num('e-rate');
      var months = Math.round(num('e-tenure'));
      var principal = Math.max(0, price - down);
      var emi = 0;

      if (months > 0 && principal > 0) {
        var r = rate / 12 / 100;
        if (r <= 0) {
          emi = principal / months;
        } else {
          var factor = Math.pow(1 + r, months);
          emi = principal * r * factor / (factor - 1);
        }
      }

      var emiOut = $('#e-monthly');
      var totalOut = $('#e-total');
      if (emiOut) emiOut.textContent = format(emi);
      if (totalOut) totalOut.textContent = format(emi * months);
    }

    $$('input', root).forEach(function (input) { input.addEventListener('input', update); });
    update();
  }

  /* ---------------- Gallery lightbox ---------------- */
  function initLightbox() {
    var box = $('#lightbox');
    if (!box) return;
    var img = $('#lightbox-img', box);
    var cap = $('#lightbox-cap', box);

    function open(src, caption) {
      if (img) { img.src = src; img.alt = caption || ''; }
      if (cap) cap.textContent = caption || '';
      box.setAttribute('data-open', 'true');
      document.body.style.overflow = 'hidden';
      var close = $('.lightbox-close', box);
      if (close) close.focus();
    }
    function close() {
      box.setAttribute('data-open', 'false');
      document.body.style.overflow = '';
    }

    $$('[data-lightbox]').forEach(function (trigger) {
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        open(trigger.getAttribute('data-lightbox'), trigger.getAttribute('data-caption') || '');
      });
    });
    $$('.lightbox-close, .lightbox-backdrop', box).forEach(function (el) {
      el.addEventListener('click', close);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && box.getAttribute('data-open') === 'true') close();
    });
  }

  /* ---------------- Product gallery (thumbnails + swipe) ---------------- */
  function initProductGallery() {
    var main = $('#detail-main-image');
    if (!main) return;
    var thumbs = $$('.thumb-btn');
    var images = thumbs.map(function (t) { return t.getAttribute('data-image'); });

    function show(src, index) {
      if (src) main.src = src;
      thumbs.forEach(function (t, i) {
        t.setAttribute('aria-current', i === index ? 'true' : 'false');
      });
    }

    thumbs.forEach(function (thumb, index) {
      thumb.addEventListener('click', function () {
        show(thumb.getAttribute('data-image'), index);
      });
    });

    var current = 0;
    var startX = 0;
    main.addEventListener('touchstart', function (e) { startX = e.changedTouches[0].clientX; }, { passive: true });
    main.addEventListener('touchend', function (e) {
      var diff = e.changedTouches[0].clientX - startX;
      if (Math.abs(diff) < 45) return;
      current = (current + (diff < 0 ? 1 : -1) + images.length) % images.length;
      show(images[current], current);
    }, { passive: true });
  }

  /* ---------------- Lazy map ---------------- */
  function initLazyMap() {
    $$('[data-map-src]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var src = btn.getAttribute('data-map-src');
        var holder = btn.parentNode;
        if (!src || !holder) return;
        var frame = document.createElement('iframe');
        frame.src = src;
        frame.loading = 'lazy';
        frame.title = btn.getAttribute('data-map-title') || 'Showroom location map';
        frame.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
        var wrap = document.createElement('div');
        wrap.className = 'map-embed';
        wrap.appendChild(frame);
        btn.remove();
        holder.appendChild(wrap);
      });
    });
  }

  /* ---------------- Init ---------------- */
  function init() {
    initDrawer();
    initCompare();
    initFaq();
    initSavings();
    initEmi();
    initLightbox();
    initProductGallery();
    initLazyMap();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

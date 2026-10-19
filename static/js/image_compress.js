(function () {
  // The hosting platform rejects a request body larger than 4.5 MB before it
  // reaches the app, so every photo is squeezed in the browser first and the
  // submit button stays disabled until the squeeze has finished.
  var MAX_UPLOAD_BYTES = 2 * 1024 * 1024;
  var MAX_EDGE = 1200;
  var QUALITY = 0.8;

  function compressImage(file, maxSize, quality) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function (e) {
        var img = new Image();
        img.onload = function () {
          var w = img.width, h = img.height;
          if (w > maxSize || h > maxSize) {
            if (w >= h) { h = Math.round(h * (maxSize / w)); w = maxSize; }
            else { w = Math.round(w * (maxSize / h)); h = maxSize; }
          }
          var canvas = document.createElement('canvas');
          canvas.width = w; canvas.height = h;
          var ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, w, h);
          canvas.toBlob(function (blob) {
            if (!blob) return reject(new Error('compression failed'));
            resolve(blob);
          }, 'image/jpeg', quality);
        };
        img.onerror = reject;
        img.src = e.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function setFiles(input, blob) {
    var dt = new DataTransfer();
    var name = (input.files && input.files[0] ? input.files[0].name : 'image.jpg').replace(/\.[^.]+$/, '.jpg');
    dt.items.add(new File([blob], name, { type: 'image/jpeg' }));
    input.files = dt.files;
  }

  function note(input, message, color) {
    var el = document.createElement('small');
    el.textContent = message;
    el.style.color = color;
    el.style.display = 'block';
    if (input.parentNode) input.parentNode.appendChild(el);
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 6000);
  }

  function setBusy(form, state) {
    if (!form) return;
    var buttons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    Array.prototype.forEach.call(buttons, function (button) { button.disabled = state; });
  }

  function fileInputs(form) {
    return Array.prototype.slice.call(form.querySelectorAll('input[type="file"]'));
  }

  function init() {
    var inputs = Array.prototype.slice.call(document.querySelectorAll('input[type="file"]'));

    inputs.forEach(function (input) {
      var form = input.form || input.closest('form');

      input.addEventListener('change', function () {
        var file = input.files && input.files[0];
        if (!file || !file.type || file.type.indexOf('image/') !== 0) return;

        setBusy(form, true);
        compressImage(file, MAX_EDGE, QUALITY).then(function (blob) {
          setFiles(input, blob);
          if (blob.size > MAX_UPLOAD_BYTES) {
            note(input, 'Still ' + Math.round(blob.size / 1024) + 'KB. Please crop the photo or upload a smaller JPG.', '#c62828');
          } else {
            note(input, 'Compressed to ' + Math.round(blob.size / 1024) + 'KB', '#2e7d32');
          }
        }).catch(function () {
          input.value = '';
          note(input, 'This photo could not be read. Please upload a JPG or PNG.', '#c62828');
        }).then(function () {
          setBusy(form, false);
        });
      });
    });

    var forms = Array.prototype.slice.call(document.querySelectorAll('form'));
    forms.forEach(function (form) {
      form.addEventListener('submit', function (event) {
        var tooBig = null;
        fileInputs(form).forEach(function (input) {
          var file = input.files && input.files[0];
          if (file && file.size > MAX_UPLOAD_BYTES && !tooBig) tooBig = input;
        });
        if (!tooBig) return;
        event.preventDefault();
        note(tooBig, 'This photo is ' + Math.round(tooBig.files[0].size / 1024) + 'KB and cannot be uploaded. Please upload a smaller JPG.', '#c62828');
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

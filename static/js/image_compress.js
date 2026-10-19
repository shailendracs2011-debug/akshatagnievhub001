(function () {
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

  function init() {
    var inputs = document.querySelectorAll('input[type="file"]');
    inputs.forEach(function (input) {
      input.addEventListener('change', function () {
        var file = input.files && input.files[0];
        if (!file || !file.type.startsWith('image/')) return;
        if (file.size <= 0) return;
        compressImage(file, 1200, 0.8).then(function (blob) {
          if (blob.size >= file.size) return;
          setFiles(input, blob);
          var ind = document.createElement('small');
          ind.textContent = 'Compressed to ' + Math.round(blob.size / 1024) + 'KB';
          ind.style.color = '#2e7d32';
          if (input.parentNode) input.parentNode.appendChild(ind);
          setTimeout(function () { if (ind.parentNode) ind.parentNode.removeChild(ind); }, 3000);
        }).catch(function () {});
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
"""
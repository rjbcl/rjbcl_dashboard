// =============================
  // 4. BS ↔ AD Date Conversion
  // =============================
 console.log("Here")
  const nepaliDigits = {
    'ॐ': '0', 'ॠ': '1', 'ॢ': '2', 'ॣ': '3', 'ौ': '4',
    '॥': '5', '०': '0', 'ॱ': '6', 'ॲ': '7', 'ॳ': '8', 'ॴ': '9'
  };

  function nepaliToLatin(str) {
    if(!str) return str;
    return str.replace(/[०-९]/g, d => {
      const code = d.charCodeAt(0);
      return String.fromCharCode(code - 2406);
    });
  }

  function normalizeBS(bsRaw) {
    if(!bsRaw) return '';
    let s = nepaliToLatin(bsRaw.trim())
      .replace(/\s+/g, '')
      .replace(/[^\d\-\/]/g, '')
      .replace(/\//g, '-');
    
    // Handle YYYYMMDD format
    if(/^\d{8}$/.test(s)) {
      return `${s.slice(0,4)}-${s.slice(4,6)}-${s.slice(6,8)}`;
    }
    
    // Handle YYYY-MM-DD or YYYY-M-D
    const parts = s.split('-').filter(Boolean);
    if(parts.length === 3) {
      const [y, m, d] = parts;
      return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    }
    
    return '';
  }

  function bsToAd(bsRaw) {
    try {
      const normalized = normalizeBS(bsRaw);
      if(!normalized) return '';
      
      const [y, m, d] = normalized.split('-').map(Number);
      if(!y || !m || !d) return '';
      
      const ad = NepaliFunctions.BS2AD({year: y, month: m, day: d});
      return `${ad.year}-${String(ad.month).padStart(2, '0')}-${String(ad.day).padStart(2, '0')}`;
    } catch(e) {
      console.error('BS→AD conversion error:', e);
      return '';
    }
  }

  
  function adToBs(adRaw) {
    try {
      if(!adRaw) return '';
      const [y, m, d] = adRaw.split('-').map(Number);
      if(!y || !m || !d) return '';
      
      const bs = NepaliFunctions.AD2BS({year: y, month: m, day: d});
      return `${bs.year}-${String(bs.month).padStart(2, '0')}-${String(bs.day).padStart(2, '0')}`;
    } catch(e) {
      console.error('AD→BS conversion error:', e);
      return '';
    }
  }

  // Initialize Nepali Datepickers
  $('#dob_bs, #citizen_bs, #nid_bs, #passport_expiry_bs, #nominee_dob_bs').nepaliDatePicker({
    ndpYear: true,
    ndpMonth: true,
    ndpYearCount: 120
  });


// **********Automatic Sync***************
function bindBsAdSync(bsSelector, adSelector) {
    const today = new Date();

    $(bsSelector).on('input change blur', function () {
        const ad = bsToAd($(this).val());
        const adDate = new Date(ad);

        if (adDate <= today) {
            $(adSelector).val(ad);
            $(adSelector).removeClass('is-invalid');
        } else {
            swalFire("Wrong Date", "Future Date Selected");
            $(bsSelector + ', ' + adSelector).val('');
        }
    });

    $(adSelector).on('input change blur', function () {
        const ad =$(this).val();
        const adDate = new Date(ad);
        const bs = adToBs(ad);
        debugger    
        if (adDate <= today) {
            $(bsSelector).val(bs);
            $(bsSelector).removeClass('is-invalid')
        } else {
            swalFire("Wrong Date", "Future Date Selected");
            $(bsSelector + ', ' + adSelector).val('');
        }

    });
}

// Apply to DOB and Citizenship Issue Date
// bindBsAdSync('#dob_bs', '#dob_ad');
bindBsAdSync('#citizen_bs', '#citizen_ad');
bindBsAdSync('#dob_bs', '#dob_ad');
bindBsAdSync('#nominee_dob_bs', '#nominee_dob_ad');





// =============================
  // 10. Text Validation
  // =============================

$(document).ready(function () {
  $('.alpha-text').on('keypress', function (e) {
    const char = String.fromCharCode(e.which);
    if (!/^[a-zA-Z\s]$/.test(char)) {
      e.preventDefault();
    }
  });

  $('.alpha-text').on('input', function () {
    const clean = $(this).val().replace(/[^a-zA-Z\s]/g, '');
    $(this).val(clean);
  });
});

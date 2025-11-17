$(function() {
  // =============================
  // 1. Multi-Step Form Logic
  // =============================
  let currentStep = 1;
  const totalSteps = 5;

  function showStep(step) {
    $('.form-step').removeClass('active');
    $(`.form-step[data-step="${step}"]`).addClass('active');
    
    $('.nav-step').removeClass('active');
    $(`.nav-step[data-step="${step}"]`).addClass('active');
    
    // Mark completed steps and make them clickable
    for(let i = 1; i < step; i++) {
      $(`.nav-step[data-step="${i}"]`).addClass('completed').css('cursor', 'pointer');
    }
    
    // Make current and future steps look appropriate
    for(let i = step; i <= totalSteps; i++) {
      if(i === step) {
        $(`.nav-step[data-step="${i}"]`).css('cursor', 'pointer');
      } else {
        $(`.nav-step[data-step="${i}"]`).removeClass('completed').css('cursor', 'default');
      }
    }
    
    $('#currentStep').text(step);
    
    // Button visibility
    if(step === 1) {
      $('#prevBtn').hide();
    } else {
      $('#prevBtn').show();
    }
    
    if(step === totalSteps) {
      $('#nextBtn').hide();
      $('#submitBtn').show();
    } else {
      $('#nextBtn').show();
      $('#submitBtn').hide();
    }
    
    // Scroll to top
    $('.main-content').scrollTop(0);
  }

  function validateStep(step) {
    let valid = true;
    const $currentStep = $(`.form-step[data-step="${step}"]`);
    
    $currentStep.find('[required]').each(function() {
      const $field = $(this);
      
      if($field.attr('type') === 'radio') {
        const name = $field.attr('name');
        if(!$(`input[name="${name}"]:checked`).length) {
          valid = false;
          $field.closest('.row, .mb-3').addClass('is-invalid-group');
        } else {
          $field.closest('.row, .mb-3').removeClass('is-invalid-group');
        }
      } else if($field.attr('type') === 'checkbox') {
        if(!$field.is(':checked')) {
          valid = false;
          $field.addClass('is-invalid');
        } else {
          $field.removeClass('is-invalid');
        }
      } else {
        if(!$field.val() || $field.val().trim() === '') {
          valid = false;
          $field.addClass('is-invalid');
        } else {
          $field.removeClass('is-invalid');
        }
      }
    });
    
    if(!valid) {
      alert('कृपया सबै आवश्यक विवरण भर्नुहोस्। / Please fill all required fields.');
    }
    
    return valid;
  }

  $('#nextBtn').on('click', function() {
    if(validateStep(currentStep)) {
      currentStep++;
      showStep(currentStep);
    }
  });

  $('#prevBtn').on('click', function() {
    currentStep--;
    showStep(currentStep);
  });

  // Allow navigation through sidebar
  $('.nav-step').on('click', function(e) {
    e.preventDefault();
    const targetStep = parseInt($(this).data('step'));
    
    // Allow navigation to any step that has been visited (up to currentStep + 1)
    if(targetStep <= currentStep) {
      // Going back - no validation needed
      currentStep = targetStep;
      showStep(currentStep);
    } else if(targetStep === currentStep + 1) {
      // Going forward - validate current step first
      if(validateStep(currentStep)) {
        currentStep = targetStep;
        showStep(currentStep);
      }
    }
    // Can't skip ahead to unvisited steps
  });

  // Initialize first step
  showStep(1);

  // =============================
  // 2. Photo Upload Preview
  // =============================
  $('#photoUpload').on('change', function(e) {
    const file = e.target.files[0];
    if(file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = function(e) {
        $('#photoPreview').attr('src', e.target.result);
      };
      reader.readAsDataURL(file);
    }
  });

  $('#removePhoto').on('click', function() {
    $('#photoUpload').val('');
    $('#photoPreview').attr('src', '/static/images/default-avatar.png');
  });

  // =============================
  // 3. Document Upload File Names
  // =============================
  $('#citizenshipUpload').on('change', function(e) {
    const fileName = e.target.files[0]?.name || '';
    $('#citizenshipFileName').text(fileName);
  });

  $('#signatureUpload').on('change', function(e) {
    const fileName = e.target.files[0]?.name || '';
    $('#signatureFileName').text(fileName);
  });

  $('#removeSignature').on('click', function() {
    $('#signatureUpload').val('');
    $('#signatureFileName').text('Signature.png');
  });

  // =============================
  // 4. BS ↔ AD Date Conversion
  // =============================
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
  $('#dob_bs, #citizen_bs, #nid_bs, #passport_expiry, #nominee_dob').nepaliDatePicker({
    ndpYear: true,
    ndpMonth: true,
    ndpYearCount: 120
  });

  // Auto-convert BS to AD for DOB
  const $dobBs = $('#dob_bs');
  
  function updateDobAd() {
    const ad = bsToAd($dobBs.val());
    if(ad) {
      // Store AD date in a hidden field if needed
      console.log('DOB AD:', ad);
    }
  }

  const dobObserver = new MutationObserver(() => updateDobAd());
  dobObserver.observe($dobBs[0], {attributes: true, attributeFilter: ['value']});
  $dobBs.on('input change blur', updateDobAd);

  // =============================
  // 5. Address Cascading Dropdowns
  // =============================
  function initAddressCascade(locations) {
    function populateProvince(sel) {
      sel.html('<option value="">Select Province</option>');
      for(let province in locations) {
        sel.append(`<option value="${province}">${province}</option>`);
      }
    }

    function populateDistricts(province, districtSel, muniSel) {
      districtSel.html('<option value="">Select District</option>');
      muniSel.html('<option value="">Select Municipality</option>');
      
      if(locations[province]) {
        Object.keys(locations[province]).forEach(district => {
          districtSel.append(`<option value="${district}">${district}</option>`);
        });
      }
    }

    function populateMunicipalities(province, district, muniSel) {
      muniSel.html('<option value="">Select Municipality</option>');
      
      if(locations[province] && locations[province][district]) {
        locations[province][district].forEach(muni => {
          muniSel.append(`<option value="${muni}">${muni}</option>`);
        });
      }
    }

    // Permanent Address
    populateProvince($('#perm_province'));
    
    $('#perm_province').on('change', function() {
      populateDistricts($(this).val(), $('#perm_district'), $('#perm_muni'));
    });
    
    $('#perm_district').on('change', function() {
      populateMunicipalities($('#perm_province').val(), $(this).val(), $('#perm_muni'));
    });

    // Temporary Address
    populateProvince($('#temp_province'));
    
    $('#temp_province').on('change', function() {
      populateDistricts($(this).val(), $('#temp_district'), $('#temp_muni'));
    });
    
    $('#temp_district').on('change', function() {
      populateMunicipalities($('#temp_province').val(), $(this).val(), $('#temp_muni'));
    });
  }

  // Load Nepal locations data
  $.getJSON('/static/nepal_locations.json')
    .done(function(data) {
      console.log('✅ Loaded Nepal location data');
      initAddressCascade(data);
    })
    .fail(function() {
      console.error('⚠️ Could not load nepal_locations.json');
      alert('Warning: Location data could not be loaded. Please refresh the page.');
    });

  // =============================
  // 6. Same Address Checkbox
  // =============================
  $('#sameAddress').on('change', function() {
    if($(this).is(':checked')) {
      const permProvince = $('#perm_province').val();
      const permDistrict = $('#perm_district').val();
      const permMuni = $('#perm_muni').val();
      const permWard = $('input[name="perm_ward"]').val();

      $('#temp_province').val(permProvince).trigger('change');
      
      setTimeout(() => {
        $('#temp_district').val(permDistrict).trigger('change');
        
        setTimeout(() => {
          $('#temp_muni').val(permMuni);
          $('input[name="temp_ward"]').val(permWard);
        }, 100);
      }, 100);

      // Disable temporary address fields
      $('#temp_province, #temp_district, #temp_muni').prop('disabled', true);
      $('input[name="temp_ward"]').prop('disabled', true);
    } else {
      // Enable temporary address fields
      $('#temp_province, #temp_district, #temp_muni').prop('disabled', false);
      $('input[name="temp_ward"]').prop('disabled', false);
    }
  });

  // =============================
  // 7. Form Submission
  // =============================
  $('#kycForm').on('submit', function(e) {
    if(!validateStep(totalSteps)) {
      e.preventDefault();
      return false;
    }
    
    // Re-enable disabled fields before submission
    $('#temp_province, #temp_district, #temp_muni, input[name="temp_ward"]').prop('disabled', false);
    
    // Form will submit normally
    console.log('✅ Form submitted');
  });

  // =============================
  // 8. Real-time Validation Feedback
  // =============================
  $('input[required], select[required], textarea[required]').on('blur', function() {
    const $field = $(this);
    
    if($field.attr('type') === 'radio') {
      return; // Skip radio buttons
    }
    
    if(!$field.val() || $field.val().trim() === '') {
      $field.addClass('is-invalid');
    } else {
      $field.removeClass('is-invalid');
    }
  });

  $('input[required], select[required], textarea[required]').on('input change', function() {
    const $field = $(this);
    
    if($field.val() && $field.val().trim() !== '') {
      $field.removeClass('is-invalid');
    }
  });

  console.log('✅ KYC Form initialized successfully');
});
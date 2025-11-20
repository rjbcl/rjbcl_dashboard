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
    let missingFields = [];
    
    $currentStep.find('[required]').each(function() {
      const $field = $(this);
      const fieldLabel = $field.closest('.mb-3').find('label').first().text().replace('*', '').trim();
      
      if($field.attr('type') === 'radio') {
        const name = $field.attr('name');
        if(!$(`input[name="${name}"]:checked`).length) {
          valid = false;
          $field.closest('.row, .mb-3').addClass('is-invalid-group');
          if(fieldLabel && !missingFields.includes(fieldLabel)) {
            missingFields.push(fieldLabel);
          }
        } else {
          $field.closest('.row, .mb-3').removeClass('is-invalid-group');
        }
      } else if($field.attr('type') === 'checkbox') {
        if(!$field.is(':checked')) {
          valid = false;
          $field.addClass('is-invalid');
          if(fieldLabel && !missingFields.includes(fieldLabel)) {
            missingFields.push(fieldLabel);
          }
        } else {
          $field.removeClass('is-invalid');
        }
      } else {
        if(!$field.val() || $field.val().trim() === '') {
          valid = false;
          $field.addClass('is-invalid');
          if(fieldLabel && !missingFields.includes(fieldLabel)) {
            missingFields.push(fieldLabel);
          }
        } else {
          $field.removeClass('is-invalid');
        }
      }
    });
    
    if(!valid) {
      let errorMessage = 'कृपया सबै आवश्यक विवरण भर्नुहोस्।<br><small>Please fill all required fields.</small>';
      
      if(missingFields.length > 0 && missingFields.length <= 5) {
        errorMessage += '<br><br><div style="text-align: left; font-size: 13px;"><strong>Missing:</strong><br>';
        missingFields.forEach(field => {
          errorMessage += `• ${field}<br>`;
        });
        errorMessage += '</div>';
      }
      swalError('Incomplete Form', errorMessage);
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
    const file = e.target.files[0]?.name || '';
    $('#citizenshipFileName').text(file);


    // const file = e.target.files[0];
    if(file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = function(e) {
        $('#citizenship_front').attr('src', e.target.result);
      };
      reader.readAsDataURL(file);
    }
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
  // 4. Spouse Name Manupulation
  // =============================
  $(document).ready(function() {
  
  // Handle marital status change
  $('input[name="marital_status"]').on('change', function() {
    const $spouseNameInput = $('#spouse_name');
    const $spouseLabel = $spouseNameInput.closest('.mb-3').find('label');
    const $requiredStar = $spouseLabel.find('.text-danger');
    
    if ($(this).val() === 'Married') {
      // Married: Make field required and editable
      $spouseNameInput.prop('required', true);
      $spouseNameInput.prop('readonly', false);
      
      // Add * sign if not exists
      if ($requiredStar.length === 0) {
        $spouseLabel.append(' <span class="text-danger">*</span>');
      }
    } else {
      // Unmarried: Make field readonly and not required
      $spouseNameInput.prop('required', false);
      $spouseNameInput.prop('readonly', true);
      $spouseNameInput.removeClass('is-invalid');
      $spouseNameInput.val(''); // Clear the value
      
      // Remove * sign
      $requiredStar.remove();
    }
  });
  
  // Initialize on page load (if a value is already selected)
  $('input[name="marital_status"]:checked').trigger('change');
  
});




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
      // Calling Sweetalert for error message
      swalFire('Data Loading Error','Location data could not be loaded. Please refresh the page.').then((result) => {
        if (result.isConfirmed) {
          location.reload();
        }
      });
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
      const permAddress = $('input[name="perm_address"]').val();
      const permHouse = $('input[name="perm_house_number"]').val();

      $('#temp_province').val(permProvince).trigger('change');
      
      setTimeout(() => {
        $('#temp_district').val(permDistrict).trigger('change');
        mm
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
    e.preventDefault();
    
    if(!validateStep(totalSteps)) {
      return false;
    }
    debugger
    // Show confirmation dialog
      swalQuestion(
        'Submit KYC Form?', 
        '<p>के तपाईं यो फारम पेश गर्न चाहनुहुन्छ?</p><small>Do you want to submit this form?</small>',
        'Yes, Submit'
    ).then((result) => {
      if (result.isConfirmed) {
        // Re-enable disabled fields before submission
        $('#temp_province, #temp_district, #temp_muni, input[name="temp_ward"]').prop('disabled', false);
        
        // Show loading
        Swal.fire({
          title: 'Submitting...',
          html: 'कृपया पर्खनुहोस्...<br><small>Please wait...</small>',
          allowOutsideClick: false,
          allowEscapeKey: false,
          showConfirmButton: false,
          didOpen: () => {
            Swal.showLoading();
          }
        });
        
        // Submit the form
        this.submit();
      }
    });
    
    return false;
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



  // =============================
  // 9. Email  and  Ph.no Format Checker
  // =============================

$(document).ready(function() {
  
  // Email validation regex
  const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  
  // Validate email on blur and input
  $('input[name="email"]').on('blur input', function() {
    const $emailInput = $(this);
    const emailValue = $emailInput.val().trim();
    
    // Remove previous error message if exists
    $emailInput.next('.invalid-feedback').remove();
    $emailInput.removeClass('is-invalid is-valid');
    
    // Skip validation if empty (let required attribute handle it)
    if (emailValue === '') {
      return;
    }
    
    // Check email format
    if (!emailRegex.test(emailValue)) {
      // Invalid email
      $emailInput.addClass('is-invalid');
      $emailInput.after('<div class="invalid-feedback d-block">Please enter a valid email address (e.g., example@domain.com)</div>');
    } else {
      // Valid email
      $emailInput.addClass('is-valid');
    }
  });
  
  // Validate on form submit
  $('form').on('submit', function(e) {
    const $emailInput = $('input[name="email"]');
    const emailValue = $emailInput.val().trim();
    
    if (emailValue && !emailRegex.test(emailValue)) {
      e.preventDefault();
      $emailInput.focus();
      $emailInput.trigger('blur'); // Trigger validation display
      return false;
    }
  });
  
});


// Phone number checker

$(document).ready(function () {
  function setupMobileValidation($input) {
    // Allow only numbers and + symbol
    $input.on('keypress', function (e) {
      const char = String.fromCharCode(e.which);
      const allowedChars = /[0-9+]/;

      if (e.which === 8 || e.which === 0 || e.which === 9) return true;
      if (!allowedChars.test(char)) {
        e.preventDefault();
        return false;
      }
    });

    // Prevent pasting invalid characters
    $input.on('paste', function () {
      setTimeout(() => {
        let value = $(this).val();
        value = value.replace(/[^0-9+]/g, '');
        $(this).val(value);
      }, 0);
    });

    // Validate on blur and input
    $input.on('blur input', function () {
      const $el = $(this);
      const value = $el.val().trim();

      $el.next('.invalid-feedback').remove();
      $el.removeClass('is-invalid is-valid');

      if (value === '') return;

      const digitCount = value.replace(/[^0-9]/g, '').length;

      if (digitCount < 10) {
        $el.addClass('is-invalid');
        $el.after('<div class="invalid-feedback d-block">Mobile number must have at least 10 digits</div>');
      } else {
        $el.addClass('is-valid');
      }
    });
  }

  // Apply to all mobile fields
  const $mobileFields = $('#mobile, #contact_mobile');
  $mobileFields.each(function () {
    setupMobileValidation($(this));
  });

  // Validate on form submit
  $('form').on('submit', function (e) {
    let isValid = true;

    $mobileFields.each(function () {
      const $input = $(this);
      const value = $input.val().trim();
      const digitCount = value.replace(/[^0-9]/g, '').length;

      if (value && digitCount < 10) {
        isValid = false;
        $input.focus();
        $input.trigger('blur');
        return false; // break loop
      }
    });

    if (!isValid) {
      e.preventDefault();
      return false;
    }
  });
});



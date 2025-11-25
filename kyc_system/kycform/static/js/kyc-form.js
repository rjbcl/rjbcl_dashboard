$(function () {
  // =============================
  // 1. Multi-Step Form Logic
  // =============================
  let currentStep = 1;
  const totalSteps = 5;
  let highestStepReached = 1; // Track the furthest step user has reached

  function showStep(step) {
    $('.form-step').removeClass('active');
    $(`.form-step[data-step="${step}"]`).addClass('active');

    $('.nav-step').removeClass('active');
    $(`.nav-step[data-step="${step}"]`).addClass('active');

    // Mark completed steps and make them clickable
    for (let i = 1; i < step; i++) {
      $(`.nav-step[data-step="${i}"]`).addClass('completed').css('cursor', 'pointer');
    }

    // Make current step clickable
    $(`.nav-step[data-step="${step}"]`).css('cursor', 'pointer');

    // Mark steps that user has reached before as accessible
    for (let i = step + 1; i <= highestStepReached; i++) {
      $(`.nav-step[data-step="${i}"]`).addClass('completed').css('cursor', 'pointer');
    }

    // Make unreached future steps non-clickable
    for (let i = highestStepReached + 1; i <= totalSteps; i++) {
      $(`.nav-step[data-step="${i}"]`).removeClass('completed').css('cursor', 'default');
    }

    $('#currentStep').text(step);

    // Button visibility
    if (step === 1) {
      $('#prevBtn').hide();
    } else {
      $('#prevBtn').show();
    }

    if (step === totalSteps) {
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

    $currentStep.find('[required]').each(function () {
      const $field = $(this);
      const fieldLabel = $field.closest('.mb-3').find('label').first().text().replace('*', '').trim();
      if ($field.attr('type') === 'radio') {
        const name = $field.attr('name');
        if (!$(`input[name="${name}"]:checked`).length) {
          valid = false;
          $field.closest('.row, .mb-3').addClass('is-invalid-group');
          if (fieldLabel && !missingFields.includes(fieldLabel)) {
            missingFields.push(fieldLabel);
          }
        } else {
          $field.closest('.row, .mb-3').removeClass('is-invalid-group');
        }
      } else if ($field.attr('type') === 'checkbox') {
        if (!$field.is(':checked')) {
          valid = false;
          $field.addClass('is-invalid');
          if (fieldLabel && !missingFields.includes(fieldLabel)) {
            missingFields.push(fieldLabel);
          }
        } else {
          $field.removeClass('is-invalid');
        }
      }
      else if ($field.attr('type') === 'file') {
        const files = $field[0].files;
        if (!files || files.length === 0) {
          valid = false;
          $field.next('button').addClass('is-invalid');
          $field.next('#photoBtn').removeClass('is-invalid');
          $field.parent().siblings('.photo-preview').addClass('is-invalid');

          if (fieldLabel && !missingFields.includes(fieldLabel)) {
            missingFields.push(fieldLabel);
          }
        } else {
          $field.next('button').removeClass('is-invalid');
          $field.parent().siblings('.photo-preview').removeClass('is-invalid');
        }
      }
      else {
        if (!$field.val() || $field.val().trim() === '') {
          valid = false;
          $field.addClass('is-invalid');
          if (fieldLabel && !missingFields.includes(fieldLabel)) {
            missingFields.push(fieldLabel);
          }
        } else {
          $field.removeClass('is-invalid');
        }
      }
    });

    if (!valid) {
      let errorMessage = 'कृपया सबै आवश्यक विवरण भर्नुहोस्।<br><small>Please fill all required fields.</small>';

      if (missingFields.length > 0 && missingFields.length <= 5) {
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

  $('#nextBtn').on('click', function () {
    if (validateStep(currentStep)) {
      currentStep++;
      if (currentStep > highestStepReached) {
        highestStepReached = currentStep;
      }
      showStep(currentStep);
    }
  });

  $('#prevBtn').on('click', function () {
    currentStep--;
    showStep(currentStep);
  });

  // Allow navigation through sidebar
  $('.nav-step').on('click', function (e) {
    e.preventDefault();
    const targetStep = parseInt($(this).data('step'));

    // Can't click on the same step
    if (targetStep === currentStep) {
      return;
    }

    // Allow navigation to any previously reached step
    if (targetStep <= highestStepReached) {
      // If going forward, validate current step first
      if (targetStep > currentStep) {
        if (validateStep(currentStep)) {
          currentStep = targetStep;
          showStep(currentStep);
        }
      } else {
        // Going backward - no validation needed
        currentStep = targetStep;
        showStep(currentStep);
      }
    } else {
      // Trying to skip to an unreached step - show error
      swalError('Cannot Skip Steps', 'कृपया पहिले हालको पृष्ठ पूरा गर्नुहोस्।<br><small>Please complete the current page first.</small>');
    }
  });

  // Initialize first step
  showStep(1);

  // =============================
  // 2. Photo Upload Preview
  // =============================
  $('#photoUpload').on('change', function (e) {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = function (e) {
        $('#photoPreview').attr('src', e.target.result);
        // Remove is-invalid class from photo-preview div
        $('.photo-preview').removeClass('is-invalid');
      };
      reader.readAsDataURL(file);
    }
  });

  $('#removePhoto').on('click', function () {
    $('#photoUpload').val('');
    $('#photoPreview').attr('src', '/static/images/default-avatar.png');
  });

  // =============================
  // 3. Document Upload 
  // =============================

  //  Name displayer
  $(document).ready(function () {
    $('input[type="file"]').on('change', function () {
      const file = this.files[0];
      const $input = $(this);
      const fileNameTarget = $input.data('filename');

      if (file && fileNameTarget) {
        $('#' + fileNameTarget).text(file.name);
      }
    });
  });



  // DISPLAY THE IMAGE
  $(document).ready(function () {

    $('input[type="file"]').on('change', function () {
      const file = this.files[0];
      const $input = $(this);
      const $container = $input.closest('.transparent-dark-div');
      const $removeBtn = $container.find('.remove-btn');

      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();

        reader.onload = function (e) {
          // Get the preview target using a data-preview attribute
          const targetId = $input.data('preview');
          const $previewDiv = $('#' + targetId);
          $previewDiv.css({
            'background-image': `url('${e.target.result}')`,
            'background-size': 'cover',
            'background-position': 'center',
            'background-repeat': 'no-repeat'
          });

          // Show remove button
          $removeBtn.show();
        };

        $container.find('button').removeClass('is-invalid');
        // $container.find('button').addClass('is-valid');
        reader.readAsDataURL(file);
      }
    });

    // Handle remove button click
    $('.remove-btn').on('click', function () {
      const $container = $(this).closest('.transparent-dark-div');
      const $input = $container.find('input[type="file"]');
      const targetId = $input.data('preview');
      const $previewDiv = $('#' + targetId);
      const $fileName = $container.find('.file-name');

      // Clear the file input
      $input.val('');

      // Remove background image
      $previewDiv.css('background-image', '');

      // Hide remove button
      $(this).hide();

      // Reset file name text if it has a data-filename attribute
      const defaultText = $input.data('filename').replace(/([A-Z])/g, ' $1').trim();
      $fileName.text(defaultText.charAt(0).toUpperCase() + defaultText.slice(1));
    });
  });

//Nepali typing
  nepalify.interceptElementById('nep-first-name', {
    layout: 'traditional',  // Options: 'romanized' or 'traditional'
    enable: true
  });
  // ============================
  // 4. Spouse Name Manupulation
  // =============================
  $(document).ready(function () {

    // Handle marital status change
    $('input[name="marital_status"]').on('change', function () {
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

  $('#spouse_name').on('input change blur', function () {
    $(this).removeClass('is-invalid');
  });



  // =============================
  // 5. Address Cascading Dropdowns
  // =============================
  function initAddressCascade(locations) {
    function populateProvince(sel) {
      sel.html('<option value="">Select Province</option>');
      for (let province in locations) {
        sel.append(`<option value="${province}">${province}</option>`);
      }
    }

    function populateDistricts(province, districtSel, muniSel) {
      districtSel.html('<option value="">Select District</option>');
      muniSel.html('<option value="">Select Municipality</option>');

      if (locations[province]) {
        Object.keys(locations[province]).forEach(district => {
          districtSel.append(`<option value="${district}">${district}</option>`);
        });
      }
    }

    function populateMunicipalities(province, district, muniSel) {
      muniSel.html('<option value="">Select Municipality</option>');

      if (locations[province] && locations[province][district]) {
        locations[province][district].forEach(muni => {
          muniSel.append(`<option value="${muni}">${muni}</option>`);
        });
      }
    }

    // Permanent Address
    populateProvince($('#perm-province'));

    $('#perm-province').on('change', function () {
      populateDistricts($(this).val(), $('#perm-district'), $('#perm-muni'));
    });

    $('#perm-district').on('change', function () {
      populateMunicipalities($('#perm-province').val(), $(this).val(), $('#perm-muni'));
    });

    // Temporary Address
    populateProvince($('#temp-province'));

    $('#temp-province').on('change', function () {
      populateDistricts($(this).val(), $('#temp-district'), $('#temp-muni'));
    });

    $('#temp-district').on('change', function () {
      populateMunicipalities($('#temp-province').val(), $(this).val(), $('#temp-muni'));
    });
  }

  // Load Nepal locations data
  $.getJSON('/static/nepal_locations.json')
    .done(function (data) {
      console.log('✅ Loaded Nepal location data');
      initAddressCascade(data);
    })
    .fail(function () {
      console.error('⚠️ Could not load nepal_locations.json');
      // Calling Sweetalert for error message
      swalFire('Data Loading Error', 'Location data could not be loaded. Please refresh the page.').then((result) => {
        if (result.isConfirmed) {
          location.reload();
        }
      });
    });

  // =============================
  // 6. Same Address Checkbox
  // =============================
  $('#sameAddress').on('change', function () {
    if ($(this).is(':checked')) {
      const permProvince = $('#perm-province').val();
      const permDistrict = $('#perm-district').val();
      const permMuni = $('#perm-muni').val();
      const permWard = $('#perm-ward').val();
      const permAddress = $('#perm-address').val();
      const permHouse = $('#perm-house-number').val();

      $('#temp-province').val(permProvince).trigger('change');

      setTimeout(() => {
        $('#temp-district').val(permDistrict).trigger('change');

        setTimeout(() => {
          $('#temp-muni').val(permMuni);
          $('#temp-ward').val(permWard);
          $('#temp-address').val(permAddress);
          $('#temp-house-number').val(permHouse);

        }, 100);
      }, 100);

      // Disable temporary address fields
      $('#temp-province, #temp-district, #temp-muni, #temp-ward, #temp-address, #temp-house-number').prop('disabled', true);
    } else {
      // Enable temporary address fields
      $('#temp-province, #temp-district, #temp-muni, #temp-ward, #temp-address, #temp-house-number').prop('disabled', false);
    }
  });
  // =============================
  // 6. Bank Json Reader
  // =============================

  async function loadBanks() {
    try {
      const response = await fetch('/static/nepal_banks.json');
      const banks = await response.json();

      // Get the select element
      const selectElement = document.getElementById('bankSelect');

      // Sort banks alphabetically by name
      banks.sort((a, b) => a.name.localeCompare(b.name));

      // Populate the dropdown
      banks.forEach(bank => {
        const option = document.createElement('option');
        option.value = bank.name;
        option.textContent = bank.name;
        selectElement.appendChild(option);
      });

    } catch (error) {
      console.error('Error loading banks:', error);
      alert('Failed to load bank list. Please try again.');
    }
  }

  // Load banks when the page loads
  $('#bankSelect').on('click', loadBanks);

  // Optional: Listen for selection changes
  document.getElementById('bankSelect').addEventListener('change', function (e) {
    const selectedOption = e.target.selectedOptions[0];
    const snNo = selectedOption.getAttribute('data-sn-no');
  });

  // =============================
  // 6. Profession Json Reader
  // =============================

  async function loadoccupations() {
    try {
      const response = await fetch('/static/occupations.json');
      const data = await response.json();

      // Access the array
      const occupations = data.occupations;
      const selectElement = document.getElementById('occupation');

      // Sort alphabetically
      occupations.sort((a, b) => a.name.localeCompare(b.name));

      // Populate dropdown
      occupations.forEach(occupation => {
        const option = document.createElement('option');
        option.value = occupation.id;        // better to use ID as value
        option.textContent = occupation.name;
        selectElement.appendChild(option);
      });

    } catch (error) {
      console.error('Error loading Profession:', error);
      alert('Failed to load profession list. Please try again.');
    }
  }

  // Load profession when the element is clicked
  $('#occupation').on('click', loadoccupations);

  // Optional: Listen for selection changes
  document.getElementById('occupation').addEventListener('change', function (e) {
    const selectedOption = e.target.selectedOptions[0];
    console.log('Selected occupation:', e.target.value);
  });


  // =============================
  // 6. Financial Details 
  // =============================
  $(document).ready(function () {
    // Fields that should be affected
    const dependentFields = [
      { input: '#annual-income' },
      { input: '#income-mode' },
      { input: '#income-source' },
      { input: '#pan-number' },
    ];

    function updateFieldRequirements() {
      const selectedValue = $('#occupation').val();

      // Check if House Wife or Student is selected
      if (selectedValue === "244" || selectedValue === "245") {
        // Remove required attribute and make readonly
        dependentFields.forEach(field => {
          $(field.input)
            .prop('required', false)
            .prop('readonly', true)
            .removeClass('is-invalid') // Remove validation error class
            .val(''); // Optional: clear the value
          console.log(field.input)
          if (field.input === '#income-mode') {
            $(field.input).prop('disabled', true);
          }
          // Remove the asterisk from label
          $(field.input).closest('.mb-3').find('label .text-danger').hide();
        });
      } else if (selectedValue === "194") {
        $('#pan-number')
          .prop('required', false)
          .removeClass('is-invalid')
          .val('');
        $("#pan-number").closest('.mb-3').find('.text-danger').hide();
      } else if (selectedValue !== '') {
        // Restore required attribute and make editable
        dependentFields.forEach(field => {
          $(field.input)
            .prop('required', true)
            .prop('readonly', false)
            .prop('disabled', false)
            .removeClass('is-invalid'); // Remove any existing validation error
          // Show the asterisk in label
          $(field.input).closest('.mb-3').find('.text-danger').show();
        });
      }
    }


    // Run on occupation change
    $('#occupation').on('change', updateFieldRequirements);

    // Prevent validation on readonly fields
    dependentFields.forEach(field => {
      $(field.input).on('blur input change', function () {
        if ($(this).prop('readonly')) {
          $(this).removeClass('is-invalid');
        }
      });
    });

  });


  // ****************Further Occupation Description when Other*****************
  const occupationDescDiv = $('#occupation-description').closest('.mb-3');
  const occupationDescInput = $('#occupation-description');

  $('#occupation').on('change', function () {
    const selectedValue = $(this).val();

    if (selectedValue === "194") {
      // Show the div and make it required
      occupationDescDiv.show();
      occupationDescInput.prop('required', true);
      occupationDescDiv.find('.text-danger').show();
      $('#pan-number')
        .prop('required', false)
        .removeClass('is-invalid');
      $('#pan-number').closest('.mb-3').find('label .text-danger').hide();
    } else {
      // Hide the div and remove required
      occupationDescDiv.hide();
      occupationDescInput
        .prop('required', false)
        .removeClass('is-invalid')
        .val(''); // Optional: clear the value when hidden
      occupationDescDiv.find('.text-danger').hide();
    }
  });
  // Prevent validation on hidden fields
  occupationDescInput.on('blur input change', function () {
    if (occupationDescDiv.is(':hidden')) {
      $(this).removeClass('is-invalid');
    }
  });

  // =============================
  // 7. Form Submission
  // =============================
$('#submitBtn').on('click', function (e) {
  e.preventDefault();

  if (!validateStep(totalSteps)) {
    return false;
  }

  // Show confirmation dialog
  Swal.fire({
    title: 'Submit KYC Form?',
    html: '<p>के तपाईं यो फारम पेश गर्न चाहनुहुन्छ?</p><small>Do you want to submit this form?</small>',
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#28a745',
    cancelButtonColor: '#6c757d',
    confirmButtonText: 'Yes, Submit',
    cancelButtonText: 'Cancel',
    customClass: {
      popup: 'swal-nepali'
    }
  }).then((result) => {
    if (result.isConfirmed) {
      // Re-enable disabled fields before submission
      $('#temp-province, #temp-district, #temp-muni, #temp-ward, #temp-address, #temp-house-number').prop('disabled', false);

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
      $('#kycForm').submit();
    }
  });

  return false;
});

  // =============================
  // 8. Real-time Validation Feedback
  // =============================
  $('input[required], select[required], textarea[required]').on('blur', function () {
    const $field = $(this);

    if ($field.attr('type') === 'radio') {
      return; // Skip radio buttons
    }

    if (!$field.val() || $field.val().trim() === '') {
      // Don't add invalid class if field is pan-number AND occupation is 194
      if (!($field.attr('id') == 'pan-number' && $('#occupation').val() == '194')) {
        $field.addClass('is-invalid');
      }
    } else {
      $field.removeClass('is-invalid');
    }
  });

  $('input[required], select[required], textarea[required]').on('input change', function () {
    const $field = $(this);

    if ($field.val() && $field.val().trim() !== '') {
      $field.removeClass('is-invalid');
    }
  });

  console.log('✅ KYC Form initialized successfully');
});



// =============================
// 9. Email  and  Ph.no Format Checker
// =============================

$(document).ready(function () {

  // Email validation regex
  const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  // Validate email on blur and input
  $('input[name="email"]').on('blur input', function () {
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
  $('form').on('submit', function (e) {
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








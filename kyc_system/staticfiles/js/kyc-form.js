$(document).ready(function () {
  "use strict";
  // =============================
  // SECTION 0: UTILITIES & HELPERS
  // =============================
  //PREVENTS FORM SUBMISSION ON ENTER KEY PRESS
  $("#kycForm").on("keypress", function (e) {
    if (e.key === "Enter") {
      e.preventDefault(); // stop form submission
    }
  });

  const log = (...args) => console.debug.apply(console, args);
  var params = new URLSearchParams(window.location.search);
  $('#Pol_number').text(policy);


  //GET NAME FROM PREFILL DATA
  $('.step-title').text(window.user_name ? window.user_name : 'KYC Form');

  //Dashboard Btn
  $('#DashboardBtn').on('click', function (e) {
    e.preventDefault(); // prevent the default "#" link behavior
    window.location.href = window.location.origin + '/dashboard/';
  });

  //Logout Btn

  $('#logoutBtn').on('click', function (e) {
    e.preventDefault(); // prevent the default "#" link behavior
    window.location.href = window.location.origin + '/';
  });


  // ---------------------------NAV LINKS FOR LOGOUT AND DASHBOARD
  // Toggle menu on click
  $('.step-indicator .content').on('click', function (e) {
    e.preventDefault();
    toggleMenu();
  });

  function toggleMenu() {
    $('.nav-links').toggleClass('show');
    $('.collapse-menu').toggleClass('active');

    // Optional: smooth scroll into view when opened
    if ($('.nav-links').hasClass('show')) {
      setTimeout(function () {
        $('.nav-links')[0].scrollIntoView({
          behavior: 'smooth',
          block: 'nearest'
        });
      }, 100);
    }
  }

  // Close menu when clicking outside
  $(document).on('click', function (e) {
    if (!$(e.target).closest('.step-indicator').length) {
      if ($('.nav-links').hasClass('show')) {
        $('.nav-links').removeClass('show');
        $('.collapse-menu').removeClass('active');
      }
    }
  });


  function safeText(el) {
    try {
      return (el && el.textContent) ? el.textContent.trim() : "";
    } catch {
      return "";
    }
  }

  // ==================================
  // Nepali typing 
  // ==================================

  if (window.nepalify && typeof nepalify.interceptElementById === "function") {
    try {
      nepalify.interceptElementById('full_name_nep', { layout: 'traditional', enable: true });
    } catch (e) {
      console.warn("nepalify init failed", e);
    }
  }

  // Allow only Devanagari characters (U+0900–U+097F) and spaces
  $("#full_name_nep").on("input", function () {
    let value = $(this).val();
    value = value.replace(/[^\u0900-\u097F\s]/g, '');
    $(this).val(value);
  });


  // ============================
  // Section 4 — spouse name handling (marital_status)
  // ============================
  $('input[name="marital_status"]').on('change', function () {
    const $spouse = $('#spouse_name');
    const $label = $spouse.closest('.mb-3').find('label');
    const $star = $label.find('.text-danger');
    if ($(this).val() === 'Married') {
      $spouse.prop('required', true).prop('readonly', false);
      if ($star.length === 0) $label.append(' <span class="text-danger">*</span>');
    } else {
      $spouse.prop('required', false).prop('readonly', true).removeClass('is-invalid').val('');
      $star.remove();
    }
  });
  // trigger initial state
  $('input[name="marital_status"]:checked').trigger('change');


  // ---------------------------
  // Section 5 — Address
  // ---------------------------
  // Same address checkbox
  $('#sameAddress').on('change', function () {
    if ($(this).is(':checked')) {
      $('#temp_province').val($('#perm_province').val()).trigger('change');
      setTimeout(() => {
        $('#temp_district').val($('#perm_district').val()).trigger('change');
        setTimeout(() => {
          $('#temp_muni').val($('#perm_muni').val());
          $('#temp_ward').val($('#perm_ward').val());
          $('#temp_address').val($('#perm_address').val());
          $('#temp_house_number').val($('#perm_house_number').val());
        }, 120);
      }, 120);
      $('#temp_province, #temp_district, #temp_muni, #temp_ward, #temp_address, #temp_house_number').prop('disabled', true);
    } else {
      $('#temp_province, #temp_district, #temp_muni, #temp_ward, #temp_address, #temp_house_number').prop('disabled', false);
    }
  });



  // ====================================
  // Section 7 — Financial/Occupation dependent fields
  // ====================================
  (function occupationDependent() {
    const fields = {
      annualIncome: '#annual_income',
      incomeMode: '#income_mode',
      incomeSource: '#income_source',
      panNumber: '#pan_number',
      occupationDesc: '#occupation_description'
    };

    // ✅ ADD PREFILL FLAG
    let isPrefilling = false;

    function resetField($field, options = {}) {
      const { required = false, readonly = false, disabled = false, value = '', showRequired = false, preserveValue = false } = options;

      $field
        .prop('required', required)
        .prop('readonly', readonly)
        .prop('disabled', disabled)
        .removeClass('is-invalid');

      // ✅ ONLY SET VALUE IF NOT PRESERVING
      if (!preserveValue) {
        $field.val(value);
      }

      $field.closest('.mb-3').find('label .text-danger').toggle(showRequired);
    }
    function update() {
      const selected = $('#occupation').val();
      const isNoIncome = ['House Wife', 'Student'].includes(selected);
      const isOther = (selected === 'Other');

      const $annualIncome = $(fields.annualIncome);
      const $incomeMode = $(fields.incomeMode);
      const $incomeSource = $(fields.incomeSource);
      const $panNumber = $(fields.panNumber);
      const $occupationDesc = $(fields.occupationDesc);

      if (isNoIncome) {
        // No income occupations - disable fields but keep values
        resetField($annualIncome, { readonly: true, disabled: true, preserveValue: false });
        resetField($incomeMode, { disabled: true, preserveValue: false });
        resetField($incomeSource, { readonly: true, disabled: true, preserveValue: false });
        resetField($panNumber, { readonly: true, disabled: true, preserveValue: false });
        $occupationDesc.closest('.mb-3').hide();
        $occupationDesc.removeAttr('required');

      } else if (isOther) {
        // Other occupation - show description field, PAN optional, preserve values
        $occupationDesc.closest('.mb-3').show();
        resetField($occupationDesc, { required: true, showRequired: true, preserveValue: true });
        resetField($annualIncome, { required: true, showRequired: true, preserveValue: true });
        resetField($incomeMode, { required: true, showRequired: true, preserveValue: true });
        resetField($incomeSource, { required: true, showRequired: true, preserveValue: true });
        resetField($panNumber, { showRequired: false, preserveValue: true });

      } else {
        // Regular occupations - all fields required, preserve values
        $occupationDesc.closest('.mb-3').hide();
        resetField($occupationDesc, { preserveValue: true });
        resetField($annualIncome, { required: true, showRequired: true, preserveValue: true });
        resetField($incomeMode, { required: true, showRequired: true, preserveValue: true });
        resetField($incomeSource, { required: true, showRequired: true, preserveValue: true });
        resetField($panNumber, { required: true, showRequired: true, preserveValue: true });
      }
    }
    $('#occupation').on('change', update);
    update();
  })();

  // ---------------------------
  // 8.1 — Final Submit
  // ---------------------------
 $('#submitBtn').on('click', async function (e) {
    e.preventDefault();
    if (!validateStep(totalSteps)) return false;
    
    window.currentStep = 0;
    
    // First, save the progress and capture the form data
    const saved = await ajaxSaveKycProgress();
    if (!saved) return;

    // Collect the form data that was just saved
    const formArray = $("#kycForm").serializeArray();
    const previewData = {};

    formArray.forEach(item => {
        previewData[item.name] = item.value;
    });

    // Force capture addresses (same as in ajaxSaveKycProgress)
    previewData["perm_province"] = $("#perm_province").val() || null;
    previewData["perm_district"] = $("#perm_district").val() || null;
    previewData["perm_municipality"] = $("#perm_muni").val() || null;
    previewData["perm_ward"] = $("#perm_ward").val() || null;
    previewData["perm_address"] = $("#perm_address").val() || null;
    previewData["perm_house_number"] = $("#perm_house_number").val() || null;

    previewData["temp_province"] = $("#temp_province").val() || null;
    previewData["temp_district"] = $("#temp_district").val() || null;
    previewData["temp_municipality"] = $("#temp_muni").val() || null;
    previewData["temp_ward"] = $("#temp_ward").val() || null;
    previewData["temp_address"] = $("#temp_address").val() || null;
    previewData["temp_house_number"] = $("#temp_house_number").val() || null;

    // Fix radios manually
    const radioNames = ["marital_status", "gender", "is_pep", "is_aml"];
    radioNames.forEach(name => {
        const selected = $(`input[name='${name}']:checked`).val();
        if (selected !== undefined) {
            previewData[name] = selected;
        }
    });

    // Capture document URLs from the page if they exist (e.g., from img src or data attributes)
    // Adjust these selectors based on your actual HTML structure
    previewData["photo_url"] = $("#photoPreview").attr("src") || null;
    previewData["citizenship_front_url"] = $("#citizenshipFrontPreview").attr("src") || null;
    previewData["citizenship_back_url"] = $("#citizenshipBackPreview").attr("src") || null;
    previewData["signature_url"] = $("#signaturePreview").attr("src") || null;
    previewData["passport_doc_url"] = $("#passportPreview").attr("src") || null;
    previewData["nid_url"] = $("#nidPreview").attr("src") || null;

    // Show the preview modal
    showPreviewModal(previewData);

    // Handle the modal confirmation
    $('#previewModal').off('hidden.bs.modal').on('hidden.bs.modal', function () {
        // When modal is closed, ask for final confirmation
        Swal.fire({
            title: 'Submit KYC Form?',
            html: '<p>के तपाईं यो फारम पेश गर्न चाहनुहुन्छ?</p><small>Do you want to submit this form?</small>',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#28a745',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Yes, Submit',
            cancelButtonText: 'Cancel',
            customClass: { popup: 'swal-nepali' }
        }).then((result) => {
            if (!result.isConfirmed) return;
            
            // Re-enable disabled fields (if copied from permanent)
            $('#kycForm').find(':disabled').prop('disabled', false);
            
            Swal.fire({
                title: 'Submitting...',
                html: 'कृपया पर्खनुहोस्...<br><small>Please wait...</small>',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => Swal.showLoading()
            });

            $('#kycForm').submit();
        });
    });

    return false;
});


  // ======================================================================
  // 8.2 — COMMON SAVE FUNCTION (used by Save & SaveContinue)
  // ======================================================================
  async function ajaxSaveKycProgress() {

    const policyNo = $("#policyField").val();
    if (!policyNo) {
      Swal.fire("Missing Policy", "Policy number missing from form.", "error");
      return false;
    }

    // --------------------------------------
    // Collect form fields (serializeArray misses unchecked radios)
    // --------------------------------------
    const formArray = $("#kycForm").serializeArray();
    const jsonData = {};

    formArray.forEach(item => {
      jsonData[item.name] = item.value;
    });

    // --------------------------------------
    // FORCE CAPTURE OF PERMANENT ADDRESS
    // --------------------------------------
    jsonData["perm_province"] = $("#perm_province").val() || null;
    jsonData["perm_district"] = $("#perm_district").val() || null;
    jsonData["perm_municipality"] = $("#perm_muni").val() || null;
    jsonData["perm_ward"] = $("#perm_ward").val() || null;
    jsonData["perm_address"] = $("#perm_address").val() || null;
    jsonData["perm_house_number"] = $("#perm_house_number").val() || null;

    // --------------------------------------
    // FORCE CAPTURE OF TEMPORARY ADDRESS
    // --------------------------------------
    jsonData["temp_province"] = $("#temp_province").val() || null;
    jsonData["temp_district"] = $("#temp_district").val() || null;
    jsonData["temp_municipality"] = $("#temp_muni").val() || null;
    jsonData["temp_ward"] = $("#temp_ward").val() || null;
    jsonData["temp_address"] = $("#temp_address").val() || null;
    jsonData["temp_house_number"] = $("#temp_house_number").val() || null;


    // Fix radios manually (ensures marital_status, gender, is_pep, is_aml always saved)
    const radioNames = ["marital_status", "gender", "is_pep", "is_aml"];
    radioNames.forEach(name => {
      const selected = $(`input[name='${name}']:checked`).val();
      if (selected !== undefined) {
        jsonData[name] = selected;
      }
    });

    // Track progress step
    jsonData["_current_step"] = typeof currentStep !== "undefined" ? currentStep + 1 : 1;
    // --------------------------------------
    // Build multipart (FormData)
    // --------------------------------------
    const fd = new FormData();
    fd.append("policy_no", policyNo);
    fd.append("kyc_data", JSON.stringify(jsonData));
    fd.append("csrfmiddlewaretoken", $("input[name='csrfmiddlewaretoken']").val());

    // Known single-file uploads
    const fileMap = [
      { id: "#photoUpload", name: "photo" },
      { id: "#citizenshipFrontUpload", name: "citizenship-front" },
      { id: "#citizenshipBackUpload", name: "citizenship-back" },
      { id: "#signatureUpload", name: "signature" },
      { id: "#NidUpload", name: "nid" },
      { id: "#passportUpload", name: "passport_doc" }
    ];

    fileMap.forEach(item => {
      const el = $(item.id)[0];
      if (el && el.files && el.files.length > 0) {
        fd.append(item.name, el.files[0], el.files[0].name);
      }
    });
// Additional dynamic docs
$(".additional-doc-item").each(function () {
    const fileInput = $(this).find('input[type="file"]')[0];
    const nameInput = $(this).find('input[type="text"]');

    if (fileInput && fileInput.files.length > 0) {
        fd.append("additional_docs", fileInput.files[0]);
        fd.append("additional_doc_names[]", nameInput.val() || "");
    }
});


    // Show loading
    Swal.fire({
      title: "Saving...",
      html: "Saving progress, Please wait.",
      allowOutsideClick: false,
      showConfirmButton: false,
      didOpen: () => Swal.showLoading()
    });

    // --------------------------------------
    // AJAX POST
    // --------------------------------------
    return new Promise((resolve) => {
      $.ajax({
        url: "/save-progress/",
        method: "POST",
        data: fd,
        processData: false,
        contentType: false,
        success: function (resp) {
          Swal.close();
          Swal.fire({
            icon: "success",
            title: "Progress Saved",
            timer: 1200,
            showConfirmButton: false
          });
          resolve(true);
        },
        error: function (xhr) {
          Swal.close();
          Swal.fire("Error", xhr.responseJSON?.error || "Could not save progress.", "error");
          resolve(false);
        }
      });
    });
  }
  window.ajaxSaveKycProgress = ajaxSaveKycProgress;
  // ---------------------------
  // Section 9 — Realtime validations (email & phone + general blur)
  // ---------------------------
  (function validations() {
    // general blur handler for required fields
    $(document).on('blur', 'input[required], select[required], textarea[required]', function () {
      const $f = $(this);
      if ($f.is(':radio')) return;
      if (!$f.val() || $f.val().trim() === '') {
        if (!($f.attr('id') === 'pan_number' && $('#occupation').val() === '194')) {
          $f.addClass('is-invalid');
        }
      } else $f.removeClass('is-invalid');
    });

    $(document).on('input change', 'input[required], select[required], textarea[required]', function () {
      const $f = $(this);
      if ($f.val() && $f.val().trim() !== '') $f.removeClass('is-invalid');
    });

    // email
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    $(document).on('blur input', 'input[name="email"]', function () {
      const $el = $(this);
      $el.next('.invalid-feedback').remove(); $el.removeClass('is-invalid is-valid');
      const v = $el.val().trim(); if (!v) return;
      if (!emailRegex.test(v)) {
        $el.addClass('is-invalid');
        $el.after('<div class="invalid-feedback d-block">Please enter a valid email address (e.g., example@domain.com)</div>');
      } else $el.addClass('is-valid');
    });

    // phone
    function setupMobileValidation(selector) {
      const $inp = $(selector);
      $inp.on('keypress', function (e) {
        const char = String.fromCharCode(e.which);
        const allowed = /[0-9+]/;
        if (e.which === 8 || e.which === 0 || e.which === 9) return true;
        if (!allowed.test(char)) { e.preventDefault(); return false; }
      });
      $inp.on('paste', function () {
        setTimeout(() => {
          let val = $(this).val(); $(this).val(val.replace(/[^0-9+]/g, ''));
        }, 0);
      });
      $inp.on('blur input', function () {
        const $el = $(this); $el.next('.invalid-feedback').remove(); $el.removeClass('is-invalid is-valid');
        const v = $el.val().trim(); if (!v) return;
        const digits = v.replace(/[^0-9]/g, '').length;
        if (digits < 10) {
          $el.addClass('is-invalid');
          $el.after('<div class="invalid-feedback d-block">Mobile number must have at least 10 digits</div>');
        } else $el.addClass('is-valid');
      });
    }
    setupMobileValidation('#mobile'); setupMobileValidation('#contact_mobile');
  })();


  // ---------------------------
  // Section 10 — Prefill Pipeline with Loading State
  // ---------------------------

  let prefillHasRun = false;
  let loadingTimeout = null;

  /**
   * Show loading message while waiting for data
   */
  function showPrefillLoading() {
    if (typeof Swal === 'undefined') {
      console.warn("SweetAlert2 not available");
      return;
    }

    Swal.fire({
      title: 'Loading',
      html: 'Please wait while we load your information...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      didOpen: () => {
        Swal.showLoading();
      }
    });

    // Safety timeout - close after 1 minute
    loadingTimeout = setTimeout(() => {
      Swal.close();
      Swal.fire({
        icon: 'error',
        title: 'Loading Timeout',
        text: 'Form data took too long to load. Please refresh the page.',
        confirmButtonText: 'Reload Page'
      }).then(() => {
        window.location.reload();
      });
    }, 60000); // 1 minute
  }

  /**
   * Hide loading message
   */
  function hidePrefillLoading() {
    if (loadingTimeout) {
      clearTimeout(loadingTimeout);
      loadingTimeout = null;
    }
    if (typeof Swal !== 'undefined') {
      Swal.close();
    }
  }

  /**
   * Main prefill function - fills form with saved data
   */
  function runKycPrefill() {
    if (!window.prefill_data) {
      log("No prefill_data available");
      hidePrefillLoading();
      return;
    }

    if (typeof showStep !== "function") {
      console.warn("showStep not ready yet");
      return; // Don't hide loading, keep waiting
    }

    const data = window.prefill_data;
    log("=== KYC PREFILL START ===");

    // Disable occupation logic during prefill
    if (window.setOccupationPrefillMode) {
      window.setOccupationPrefillMode(true);
    }

    // Fix auto date fields
    if (data.dob_bs_auto && !data.dob_bs) data.dob_bs = data.dob_bs_auto;
    if (data.nominee_dob_bs_auto && !data.nominee_dob_bs) {
      data.nominee_dob_bs = data.nominee_dob_bs_auto;
    }

    // 1) Fill basic form inputs
    fillBasicInputs(data);

    // 2) Convert and fill BS dates
    fillBSDates(data);

    // 3) Fill radio buttons (marital status, gender, PEP, AML)
    fillRadioButtons(data);

    // 4) Fill branch name (with fallback keys)
    fillBranchName(data);

    // 5) Show saved files
    showSavedFiles(data);

    log("=== BASIC PREFILL DONE ===");

    // 6) Fill dynamic selects and addresses - these need time to populate
    fillDynamicSelectsAndAddresses(data).then(() => {
      log("=== ALL PREFILL COMPLETE ===");

      // 7) Restore step progress AFTER everything is filled
      restoreStepProgress(data);

      // Hide loading overlay
      hidePrefillLoading();
    });
  }

  /**
   * Fill basic form inputs (text, select, checkbox, radio)
   */
  function fillBasicInputs(data) {
    document.querySelectorAll('input, select, textarea').forEach(el => {
      const name = el.name;
      if (!name || !(name in data)) return;

      const value = data[name];
      if (value === null || value === undefined) return;
      if (el.type === 'file') return;

      if (el.type === 'radio') {
        if (String(el.value) === String(value)) el.checked = true;
      } else if (el.type === 'checkbox') {
        el.checked = (value === true || value === "1" || value === "true");
      } else {
        el.value = value;
      }
    });
  }

  /**
   * Convert AD dates to BS and fill date fields
   */
  function fillBSDates(data) {
    if (typeof window.adToBsString !== "function" &&
      !(window.NepaliFunctions && window.NepaliFunctions.AD2BS)) {
      console.warn("Date converter not ready");
      return;
    }

    try {
      if (data.dob_ad) {
        $('#dob_bs').val(window.adToBsString ? window.adToBsString(data.dob_ad) : "");
      }
      if (data.citizen_ad) {
        $('#citizen_bs').val(window.adToBsString ? window.adToBsString(data.citizen_ad) : "");
      }
      if (data.nominee_dob_ad) {
        $('#nominee_dob_bs').val(window.adToBsString ? window.adToBsString(data.nominee_dob_ad) : "");
      }
    } catch (e) {
      console.warn("Prefill date conversion error", e);
    }
  }

  /**
   * Fill radio buttons with proper triggering
   */
  function fillRadioButtons(data) {
    const radioFields = ['marital_status', 'gender', 'is_pep', 'is_aml'];

    radioFields.forEach(name => {
      if (data[name] === undefined || data[name] === null || String(data[name]).trim() === "") {
        return;
      }

      const val = String(data[name]).trim().toLowerCase();
      const $radio = $(`input[name="${name}"]`);

      $radio.each(function () {
        const radioVal = String($(this).val()).trim().toLowerCase();
        if (radioVal === val) {
          this.checked = true;
          $(this).trigger("change");
        }
      });
    });
  }

  /**
   * Fill a single select field with retry logic (returns Promise)
   */
  function fillSingleSelect(selector, expectedValue, label) {
    return new Promise((resolve) => {
      if (!expectedValue) {
        resolve(false);
        return;
      }

      const el = document.querySelector(selector);
      if (!el) {
        console.warn(`${label} select not found: ${selector}`);
        resolve(false);
        return;
      }

      let attempts = 0;
      const maxAttempts = 50;
      const retryInterval = 200;

      const tryFill = setInterval(() => {
        attempts++;

        if (el.options && el.options.length > 1) { // More than just placeholder
          for (let option of el.options) {
            const optVal = String(option.value).trim();
            const optText = String(option.textContent).trim();
            const expectedVal = String(expectedValue).trim();

            if (optVal === expectedVal || optText === expectedVal) {
              el.value = option.value;
              $(el).trigger('change');
              console.log(`✅ Filled ${label}: "${expectedVal}"`);
              clearInterval(tryFill);
              resolve(true);
              return;
            }
          }
        }

        if (attempts >= maxAttempts) {
          console.warn(`⚠️ Timeout filling ${label} (expected: "${expectedValue}", options: ${el.options.length})`);
          clearInterval(tryFill);
          resolve(false);
        }
      }, retryInterval);
    });
  }

  /**
   * Fill cascading address fields (province -> district -> municipality)
   */
  function fillCascadingAddress(prefix, data) {
    return new Promise(async (resolve) => {
      const provinceKey = `${prefix}_province`;
      const districtKey = `${prefix}_district`;
      const municipalityKey = `${prefix}_municipality`;
      const wardKey = `${prefix}_ward`;
      const addressKey = `${prefix}_address`;
      const houseKey = `${prefix}_house_number`;

      // Step 1: Fill province
      if (data[provinceKey]) {
        await fillSingleSelect(`#${prefix}_province`, data[provinceKey], `${prefix} Province`);
        await new Promise(r => setTimeout(r, 500)); // Wait for district options to load
      }

      // Step 2: Fill district
      if (data[districtKey]) {
        await fillSingleSelect(`#${prefix}_district`, data[districtKey], `${prefix} District`);
        await new Promise(r => setTimeout(r, 500)); // Wait for municipality options to load
      }

      // Step 3: Fill municipality
      if (data[municipalityKey]) {
        await fillSingleSelect(`#${prefix}_muni`, data[municipalityKey], `${prefix} Municipality`);
        await new Promise(r => setTimeout(r, 300));
      }

      // Step 4: Fill plain text fields
      if (data[wardKey]) $(`#${prefix}_ward`).val(data[wardKey]);
      if (data[addressKey]) $(`#${prefix}_address`).val(data[addressKey]);
      if (data[houseKey]) $(`#${prefix}_house_number`).val(data[houseKey]);

      resolve(true);
    });
  }

  /**
   * Fill all dynamic selects and addresses with Promises
   */
  async function fillDynamicSelectsAndAddresses(data) {
    const tasks = [];

    // Non-address selects
    tasks.push(fillSingleSelect("select[name='salutation']", data.salutation, "Salutation"));
    tasks.push(fillSingleSelect("select[name='nationality']", data.nationality, "Nationality"));
    tasks.push(fillSingleSelect("#bankSelect", data.bank_name, "Bank"));
    tasks.push(fillSingleSelect("select[name='account_type']", data.account_type, "Account Type"));
    tasks.push(fillSingleSelect("#occupation", data.occupation, "Occupation"));
    tasks.push(fillSingleSelect("#qualification", data.qualification, "Qualification"));
    tasks.push(fillSingleSelect("select[name='nominee_relation']", data.nominee_relation, "Nominee Relation"));

    // Fill addresses sequentially (they depend on each other)
    await fillCascadingAddress('perm', data);
    await fillCascadingAddress('temp', data);

    // Wait for all non-address tasks
    await Promise.all(tasks);

    console.log("✅ All dynamic selects and addresses filled");
  }

  /**
   * Fill branch name with fallback keys
   */
  function fillBranchName(data) {
    const branchVal = data.branch_name || data.bank_branch || data.bank_branch_name || "";
    if (!branchVal) return;

    const branchInput = document.querySelector('input[name="branch_name"]') ||
      document.getElementById('branch_name');

    if (branchInput) {
      branchInput.value = branchVal;
    }
  }

  /**
   * Restore step progress - NOW RUNS AFTER ALL DATA IS FILLED
   */
  function restoreStepProgress(data) {
    if (!data._current_step) return;
    console.log("Restored step from backend:", data._current_step);
    let targetStep = parseInt(data._current_step) || 1;
    if (targetStep < 1 || targetStep > totalSteps) targetStep = 1;
    // Validate and advance through steps
    for (let i = 1; i <= targetStep; i++) {
      currentStep = i;
      if (!validateStep(i)) {
        currentStep = i - 1;
        break;
      }
    }

    showStep(currentStep);
    window.setCurrentStep(currentStep);
    window.highestStepReached = Math.max(highestStepReached, currentStep);
    console.log(`✅ Restored to step ${currentStep}, highest reached: ${highestStepReached}`);
  }

  // ---------------------------
  // Event-based Prefill Trigger
  // ---------------------------

  const readyState = {
    locationData: false,
    bankData: false,
    occupationData: false,
    nepaliDatepicker: false
  };

  /**
   * Check if data sources are actually loaded (fallback check)
   */
  function checkDataSourcesLoaded() {
    return {
      locationData: !!(window.provincesData || window.locationDataLoaded ||
        document.querySelector('#perm_province option:nth-child(2)')),
      bankData: !!(window.banksData || window.bankDataLoaded ||
        document.querySelector('#bankSelect option:nth-child(2)')),
      occupationData: !!(window.occupationsData || window.occupationDataLoaded ||
        document.querySelector('#occupation option:nth-child(2)')),
      nepaliDatepicker: !!(typeof window.adToBsString === "function" || window.nepaliDatepickerLoaded)
    };
  }

  /**
   * Check if all required data is ready, then run prefill
   */
  function checkAllReady() {
    if (prefillHasRun) {
      return;
    }

    const allReady = Object.values(readyState).every(status => status === true);

    if (allReady) {
      console.log("✅ All events received - running prefill");
      prefillHasRun = true;
      runKycPrefill();
    }
  }

  /**
   * Force check if data is loaded even without events (fallback)
   */
  function attemptPrefillFallback() {
    if (prefillHasRun) return;

    const dataChecks = checkDataSourcesLoaded();
    const allDataPresent = Object.values(dataChecks).every(status => status === true);

    if (allDataPresent && window.prefill_data) {
      console.log("🔄 Events didn't fire but data detected - running prefill");
      prefillHasRun = true;

      // Update readyState
      Object.keys(dataChecks).forEach(key => {
        readyState[key] = dataChecks[key];
      });

      runKycPrefill();
    } else {
      console.log("⏳ Waiting for data... State:", {
        events: readyState,
        detected: dataChecks,
        hasPrefillData: !!window.prefill_data
      });
    }
  }

  // Listen for data ready events
  document.addEventListener("locationDataReady", () => {
    console.log("📍 Location data ready");
    readyState.locationData = true;
    checkAllReady();
  });

  document.addEventListener("bankDataReady", () => {
    readyState.bankData = true;
    checkAllReady();
  });

  document.addEventListener("occupationDataReady", () => {
    readyState.occupationData = true;
    checkAllReady();
  });

  document.addEventListener("NepaliDatepickerReady", () => {
    if (typeof showStep !== "function") {
      console.warn("showStep not ready - retrying");
      setTimeout(() => {
        readyState.nepaliDatepicker = true;
        checkAllReady();
      }, 500);
      return;
    }

    readyState.nepaliDatepicker = true;
    checkAllReady();
  });

  // Initialize: Show loading if prefill data exists
  if (window.prefill_data) {
    showPrefillLoading();

    // Fallback checks every 500ms
    let fallbackAttempts = 0;
    const fallbackInterval = setInterval(() => {
      if (prefillHasRun) {
        clearInterval(fallbackInterval);
        return;
      }

      fallbackAttempts++;
      attemptPrefillFallback();

      if (fallbackAttempts >= 20) { // 10 seconds
        clearInterval(fallbackInterval);
      }
    }, 500);
  } else {
    console.log("ℹ️ No prefill data - skipping prefill");
  }

  // Expose globally for manual triggering
  window.runKycPrefill = runKycPrefill;
  window.forceRunPrefill = function () {
    prefillHasRun = false;
    showPrefillLoading();

    // Force all flags to true
    Object.keys(readyState).forEach(key => readyState[key] = true);
    runKycPrefill();
  };

  console.log("✅ KYC Form script loaded");
});
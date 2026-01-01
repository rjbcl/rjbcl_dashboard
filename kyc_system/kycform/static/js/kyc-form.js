
$(document).ready(function () {
  "use strict";

  // ======================================
  // GLOBAL OTP STATE — SINGLE SOURCE OF TRUTH
  // ======================================
  (function initOtpState() {
    const el = document.getElementById('mobileOtpServerVerified');
    window.mobileOtpVerified = el && el.value === "1";
    console.log('[OTP INIT]', window.mobileOtpVerified);
  })();

  (function applyOtpLockIfVerified() {
    if (window.mobileOtpVerified === true) {
      $('#mobile')
        .prop('readonly', true)
        .addClass('is-valid');

      $('#verifyBtn')
        .prop('disabled', true)
        .text('Verified ✓');

      console.log('[OTP LOCK APPLIED]');
    }
  })();


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
  $('#Pol_number').text(POLICY_NO);


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


  // ======================================================================
  // SHARED DATA PARSING UTILITIES
  // ======================================================================

  /**
   * Collects all form data including addresses, radios, and documents
   * @returns {Object} Complete form data object
   */
  window.collectFormData = function () {
    const formArray = $("#kycForm").serializeArray();
    const formData = {};

    // Convert array to object
    formArray.forEach(item => {
      formData[item.name] = item.value;
    });

    // Force capture permanent address
    formData["perm_province"] = $("#perm_province").val() || null;
    formData["perm_district"] = $("#perm_district").val() || null;
    formData["perm_municipality"] = $("#perm_muni").val() || null;
    formData["perm_ward"] = $("#perm_ward").val() || null;
    formData["perm_address"] = $("#perm_address").val() || null;
    formData["perm_house_number"] = $("#perm_house_number").val() || null;

    // Force capture temporary address
    formData["temp_province"] = $("#temp_province").val() || null;
    formData["temp_district"] = $("#temp_district").val() || null;
    formData["temp_municipality"] = $("#temp_muni").val() || null;
    formData["temp_ward"] = $("#temp_ward").val() || null;
    formData["temp_address"] = $("#temp_address").val() || null;
    formData["temp_house_number"] = $("#temp_house_number").val() || null;

    // Explicitly force branch_name
    const branchInput = document.querySelector('input[name="branch_name"]');
    if (branchInput) {
      formData["branch_name"] = branchInput.value || null;

    }

    // Fix radio buttons manually
    const radioNames = ["marital_status", "gender", "is_pep", "is_aml"];
    radioNames.forEach(name => {
      const selected = $(`input[name='${name}']:checked`).val();
      if (selected !== undefined) {
        formData[name] = selected;
      }
    });
    // Convert yes/no strings to boolean for is_pep and is_aml
    if (formData["is_pep"]) {
      formData["is_pep"] = formData["is_pep"].toLowerCase() === "yes";
    }
    if (formData["is_aml"]) {
      formData["is_aml"] = formData["is_aml"].toLowerCase() === "yes";
    }

    return formData;
  };

  /**
   * Helper function to extract URL from background-image CSS
   * @param {string} elementId - Element selector (e.g., "#citizenship_front")
   * @returns {string|null} Extracted URL or null
   */
  function extractBackgroundImageUrl(elementId) {
    const bgImage = $(elementId).css('background-image');
    if (bgImage && bgImage !== 'none') {
      const match = bgImage.match(/url\(['"]?(.*?)['"]?\)/);
      return match ? match[1] : null;
    }
    return null;
  }

  /**
   * Collects document URLs from preview elements
   */
  window.collectDocumentUrls = function () {
    return {
      photo_url: $("#photoPreview").attr("src") || null,
      citizenship_front_url: extractBackgroundImageUrl("#citizenship_front") || null,
      citizenship_back_url: extractBackgroundImageUrl("#citizenship_back") || null,
      signature_url: extractBackgroundImageUrl("#signature") || null,
      passport_doc_url: extractBackgroundImageUrl("#passport_doc") || null,
      nid_url: extractBackgroundImageUrl("#nid_doc") || null
    };
  };

  /**
   * Creates FormData object for AJAX submission
   * @param {string} policyNo - Policy number
   * @param {Object} jsonData - Form data as JSON
   * @returns {FormData} Ready-to-submit FormData object
   */
  window.createSubmissionFormData = function (policyNo, jsonData) {
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

    return fd;
  };
  // ---------------------------
  // 8.1 — Final Submit  preview model
  // ---------------------------
  // Add this helper function to collect additional documents info
  function collectAdditionalDocsForPreview() {
    const additionalDocs = [];

    console.log('🔍 Collecting additional docs for preview...');
    console.log('Total additional-doc-item elements:', $('.additional-doc-item').length);

    $('.additional-doc-item').each(function (index) {
      const $item = $(this);
      const docIndex = $item.data('doc-index');
      const isExisting = $item.hasClass('existing-doc');

      console.log(`Document ${index + 1}: docIndex=${docIndex}, isExisting=${isExisting}`);

      if (isExisting) {
        // Existing document
        const docName = $item.find(`input[name="additional_doc_name_${docIndex}"]`).val();
        const docUrl = $item.find(`input[name="existing_doc_url_${docIndex}"]`).val();
        const fileName = $item.find('.file-name-inline').text().trim();

        console.log('  Existing doc:', { docName, docUrl, fileName });

        if (docName && docUrl) {
          additionalDocs.push({
            name: docName,
            url: docUrl,
            fileName: fileName,
            isExisting: true
          });
        }
      } else {
        // New document upload
        const docName = $item.find(`input[name="additional_doc_name_${docIndex}"]`).val();
        const fileInput = $(`#additionalDoc${docIndex}Upload`)[0];

        console.log('  New doc:', {
          docName,
          fileInputExists: !!fileInput,
          hasFiles: fileInput ? fileInput.files.length : 0
        });

        if (fileInput && fileInput.files.length > 0) {
          const file = fileInput.files[0];

          // Create a temporary URL for preview
          const fileUrl = URL.createObjectURL(file);

          console.log('  Creating preview URL for:', file.name);

          additionalDocs.push({
            name: docName || 'Unnamed Document',
            fileName: file.name,
            url: fileUrl,
            isExisting: false,
            fileType: file.type
          });
        }
      }
    });

    console.log('✅ Collected', additionalDocs.length, 'additional documents');
    return additionalDocs;
  }

  // Updated showPreviewModal function - replace the existing one
  function showPreviewModal(data) {
    console.log(data);

    function formatLabel(key) {
      return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    function createField(label, value) {
      if (value === null || value === undefined || value === '') {
        value = '---';
      }
      return `
      <div class="col-md-6 col-lg-4 mb-3">
        <strong class="text-muted small">${label}: </strong>
        <span>${value}</span>
      </div>
    `;
    }

    function createImageField(label, url) {
      if (!url) return '';
      return `
      <div class="col-md-6 col-lg-4 mb-3">
        <strong class="text-muted d-block small">${label} </strong>
        <img src="${url}" class="img-thumbnail mt-2" style="max-width: 200px; max-height: 200px;" alt="${label}">
      </div>
    `;
    }

    // NEW: Function to create additional document preview
    function createAdditionalDocField(doc) {
      const isPdf = doc.fileName && doc.fileName.toLowerCase().endsWith('.pdf');

      if (isPdf) {
        // For PDF files, show a link/button instead of image
        return `
        <div class="col-md-6 col-lg-4 mb-3">
          <strong class="text-muted d-block small">${doc.name}</strong>
          <div class="mt-2">
            <button type="button" class="btn btn-outline-primary btn-sm view-doc-preview" data-url="${doc.url}">
              <span>📄</span> ${doc.fileName}
            </button>
          </div>
        </div>
      `;
      } else {
        // For images, show thumbnail
        return `
        <div class="col-md-6 col-lg-4 mb-3">
          <strong class="text-muted d-block small">${doc.name}</strong>
          <img src="${doc.url}" class="img-thumbnail mt-2" style="max-width: 200px; max-height: 200px;" alt="${doc.name}">
          <div class="mt-1">
            <small class="text-muted">${doc.fileName}</small>
          </div>
        </div>
      `;
      }
    }

    // Personal Information
    $('#personalInfo').html(
      createField('Salutation', data.salutation) +
      createField('First Name', data.first_name) +
      createField('Middle Name', data.middle_name) +
      createField('Last Name', data.last_name) +
      createField('Full Name (Nepali)', data.full_name_nep) +
      createField('Email', data.email) +
      createField('Mobile', data.mobile) +
      createField('Gender', data.gender) +
      createField('Nationality', data.nationality) +
      createField('Marital Status', data.marital_status) +
      createField('Date of Birth (AD)', data.dob_ad) +
      createField('Date of Birth (BS)', data.dob_bs) +
      createField('Spouse Name', data.spouse_name) +
      createField('Father Name', data.father_name) +
      createField('Mother Name', data.mother_name) +
      createField('Grand Father Name', data.grand_father_name) +
      createField('Father in Law Name', data.father_in_law_name) +
      createField('Son Name', data.son_name) +
      createField('Daughter Name', data.daughter_name) +
      createField('Daughter in Law Name', data.daughter_in_law_name) +
      createField('Citizenship No', data.citizenship_no) +
      createField('Citizenship Date (BS)', data.citizen_bs) +
      createField('Citizenship Date (AD)', data.citizen_ad) +
      createField('Citizenship Place', data.citizenship_place) +
      createField('Passport No', data.passport_no) +
      createField('NID No', data.nid_no) +
      createField('PAN Number', data.pan_number) +
      createField('Qualification', data.qualification)
    );

    // Permanent Address
    $('#permAddress').html(
      createField('Province', data.perm_province) +
      createField('District', data.perm_district) +
      createField('Municipality', data.perm_municipality) +
      createField('Ward', data.perm_ward) +
      createField('Address', data.perm_address) +
      createField('House Number', data.perm_house_number)
    );

    // Temporary Address
    $('#tempAddress').html(
      createField('Province', data.temp_province) +
      createField('District', data.temp_district) +
      createField('Municipality', data.temp_municipality) +
      createField('Ward', data.temp_ward) +
      createField('Address', data.temp_address) +
      createField('House Number', data.temp_house_number)
    );

    // Bank Information
    $('#bankInfo').html(
      createField('Bank Name', data.bank_name) +
      createField('Branch Name', data.branch_name) +
      createField('Account Number', data.account_number) +
      createField('Account Type', data.account_type)
    );

    // Occupation Information
    $('#occupationInfo').html(
      createField('Occupation', data.occupation) +
      createField('Occupation Description', data.occupation_description) +
      createField('Income Mode', data.income_mode) +
      createField('Annual Income', data.annual_income ? 'Rs. ' + data.annual_income.toLocaleString() : null) +
      createField('Income Source', data.income_source) +
      createField('Employer Name', data.employer_name) +
      createField('Office Address', data.office_address) +
      createField('Is PEP', data.is_pep ? data.is_pep.toUpperCase() : null) +
      createField('Is AML', data.is_aml ? data.is_aml.toUpperCase() : null)
    );

    // Nominee Information
    $('#nomineeInfo').html(
      createField('Nominee Name', data.nominee_name) +
      createField('Relation', data.nominee_relation) +
      createField('Date of Birth (AD)', data.nominee_dob_ad) +
      createField('Date of Birth (BS)', data.nominee_dob_bs) +
      createField('Contact', data.nominee_contact) +
      createField('Guardian Name', data.guardian_name) +
      createField('Guardian Relation', data.guardian_relation)
    );

    // Main Documents
    $('#documents').html(
      createImageField('Photo', data.photo_url) +
      createImageField('Citizenship Front', data.citizenship_front_url) +
      createImageField('Citizenship Back', data.citizenship_back_url) +
      createImageField('Signature', data.signature_url) +
      createImageField('Passport', data.passport_doc_url) +
      createImageField('NID', data.nid_url)
    );

    // NEW: Additional Documents
    const additionalDocs = collectAdditionalDocsForPreview();

    if (additionalDocs.length > 0) {
      let additionalDocsHtml = '';
      additionalDocs.forEach(doc => {
        additionalDocsHtml += createAdditionalDocField(doc);
      });
      $('#additional_documents').html(additionalDocsHtml);
    } else {
      $('#additional_documents').html('<p class="text-muted">No additional documents uploaded</p>');
    }

    // Show modal
    $('#previewModal').modal('show');

    // NEW: Setup click handlers for PDF preview buttons
    setTimeout(() => {
      $('.view-doc-preview').off('click').on('click', function () {
        const url = $(this).data('url');
        window.open(url, '_blank');
      });
    }, 100);
  }

  // Make sure to expose the function globally
  window.showPreviewModal = showPreviewModal;
  // Function to handle final submission confirmation
  function proceedWithSubmission() {
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

      document.getElementById('kycForm').submit();
    });
  }

  // Make function globally accessible
  window.showPreviewModal = showPreviewModal;
  $('#submitBtn')
    .off('click') // ⛔ remove all previous bindings
    .on('click', async function (e) {

      e.preventDefault();
      e.stopImmediatePropagation();

      console.log('[OTP STATE]', window.mobileOtpVerified);

      if (!window.mobileOtpVerified) {
        Swal.fire({
          icon: 'warning',
          title: 'Mobile Not Verified',
          text: 'Please verify your mobile number before submitting.',
          confirmButtonText: 'OK'
        });
        return false;
      }

      if (!validateStep(totalSteps)) return false;

      const saved = await ajaxSaveKycProgress();
      if (!saved) return false;

      const previewData = window.collectFormData();
      Object.assign(previewData, window.collectDocumentUrls());

      showPreviewModal(previewData);

      $('#previewModal .btn-success')
        .off('click')
        .on('click', proceedWithSubmission);
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

    // Collect form data using shared function
    const jsonData = window.collectFormData();

    // Track progress step
    jsonData["_current_step"] = typeof currentStep !== "undefined" ? currentStep + 1 : 1;

    // Build FormData using shared function
    const fd = window.createSubmissionFormData(policyNo, jsonData);

    // Show loading
    Swal.fire({
      title: "Saving...",
      html: "Saving progress, Please wait.",
      allowOutsideClick: false,
      showConfirmButton: false,
      didOpen: () => Swal.showLoading()
    });

    // AJAX POST
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

    // phone - regular validation (for contact_mobile)
    function setupMobileValidation(selector) {
      const $inp = $(selector);

      // Nepali mobile number regex: (+977)?[9][6-9]\d{8}
      const nepaliMobileRegex = /^(\+977)?[9][6-9]\d{8}$/;

      $inp.on('keypress', function (e) {
        const char = String.fromCharCode(e.which);
        const allowed = /[0-9+]/;
        if (e.which === 8 || e.which === 0 || e.which === 9) return true;
        if (!allowed.test(char)) { e.preventDefault(); return false; }
      });

      $inp.on('paste', function () {
        setTimeout(() => {
          let val = $(this).val();
          $(this).val(val.replace(/[^0-9+]/g, ''));
        }, 0);
      });

      $inp.on('blur input', function () {
        const $el = $(this);
        $el.next('.invalid-feedback').remove();
        $el.removeClass('is-invalid is-valid');
        const v = $el.val().trim();
        if (!v) return;

        const digits = v.replace(/[^0-9]/g, '').length;

        // First check if it has at least 10 digits
        if (digits < 10) {
          $el.addClass('is-invalid');
          $el.after('<div class="invalid-feedback d-block">Mobile number must have at least 10 digits</div>');
        } else $el.addClass('is-valid');
      });
    }
    setupMobileValidation('#contact_mobile');

    // ===============================
    // MOBILE VALIDATION WITH REAL OTP - ENHANCED UI
    // ===============================
    function setupMobileValidationWithOTP(inputSelector, buttonSelector) {
      const $inp = $(inputSelector);
      const $btn = $(buttonSelector);
      const nepaliMobileRegex = /^(\+977)?[9][6-9]\d{8}$/;

      // Check initial verification state (from prefill or previous session)
      if (window.mobileOtpVerified) {
        console.log('[OTP] Already verified - locking field');
        lockMobileField();
        return; // Exit early if already verified
      }

      // Function to lock the mobile field
      function lockMobileField() {
        $inp.prop('readonly', true).prop('disabled', true);
        $inp.removeClass('is-invalid').addClass('is-valid');
        $btn.prop('disabled', true)
          .removeClass('verify-btn-green')
          .addClass('verify-btn-grey')
          .text('Verified ✓');
      }

      // Input restriction (only if not verified)
      $inp.on('keypress', function (e) {
        if (window.mobileOtpVerified) {
          e.preventDefault();
          return false;
        }
        const char = String.fromCharCode(e.which);
        if (!/[0-9+]/.test(char) && e.which !== 8 && e.which !== 9) {
          e.preventDefault();
        }
      });

      $inp.on('paste', function (e) {
        if (window.mobileOtpVerified) {
          e.preventDefault();
          return false;
        }
        setTimeout(() => {
          let val = $(this).val();
          $(this).val(val.replace(/[^0-9+]/g, ''));
        }, 0);
      });

      // Validate + enable button
      $inp.on('blur input', function () {
        if (window.mobileOtpVerified) return;

        const val = $inp.val().trim();
        $inp.removeClass('is-valid is-invalid');
        $inp.next('.invalid-feedback').remove();

        if (!val) {
          $btn.prop('disabled', true).removeClass('verify-btn-green').addClass('verify-btn-grey');
          return;
        }

        const digits = val.replace(/[^0-9]/g, '').length;

        if (digits < 10) {
          $inp.addClass('is-invalid')
            .after('<div class="invalid-feedback d-block">Mobile number must have at least 10 digits</div>');
          $btn.prop('disabled', true).removeClass('verify-btn-green').addClass('verify-btn-grey');
        } else if (!nepaliMobileRegex.test(val)) {
          $inp.addClass('is-invalid')
            .after('<div class="invalid-feedback d-block">Invalid Nepali mobile number format. Must start with 96-99</div>');
          $btn.prop('disabled', true).removeClass('verify-btn-green').addClass('verify-btn-grey');
        } else {
          $inp.addClass('is-valid');
          $btn.prop('disabled', false).removeClass('verify-btn-grey').addClass('verify-btn-green');
        }
      });

      // Handle resend OTP event
      document.addEventListener('otp-resend-requested', async function (e) {
        const mobile = e.detail.mobile;

        Swal.fire({
          title: 'Resending OTP...',
          didOpen: () => Swal.showLoading(),
          allowOutsideClick: false
        });

        try {
          const sendResp = await fetch('/otp/send/', {
            method: 'POST',
            headers: {
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'mobile=' + encodeURIComponent(mobile)
          });

          const sendData = await sendResp.json();
          Swal.close();

          if (!sendData.success) {
            Swal.fire('Error', sendData.error || 'OTP resend failed', 'error');
            return;
          }

          // Show new OTP input with fresh timer
          startOTPVerificationLoop(mobile);

        } catch (error) {
          Swal.close();
          Swal.fire('Error', 'Network error. Please try again.', 'error');
        }
      });

      // OTP verification loop function
      async function startOTPVerificationLoop(mobile, initialError = '') {
        let verified = false;
        let errorMsg = initialError;

        while (!verified) {
          const otpInput = await swalOTPInput(mobile, errorMsg);

          if (otpInput.isDismissed) {
            return; // User cancelled
          }

          if (otpInput.isConfirmed) {
            const enteredOTP = otpInput.value;

            // Show verifying loader
            Swal.fire({
              title: 'Verifying OTP...',
              html: 'Please wait',
              didOpen: () => Swal.showLoading(),
              allowOutsideClick: false,
              allowEscapeKey: false
            });

            try {
              const verifyResp = await fetch('/otp/verify/', {
                method: 'POST',
                headers: {
                  'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                  'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: 'otp=' + encodeURIComponent(enteredOTP)
              });

              const verifyData = await verifyResp.json();
              Swal.close();

              if (verifyData.success) {
                // SUCCESS!
                window.mobileOtpVerified = true;

                // Persist state for reloads
                const otpStateEl = document.getElementById('mobileOtpServerVerified');
                if (otpStateEl) otpStateEl.value = "1";

                await Swal.fire({
                  icon: 'success',
                  title: 'Verified!',
                  text: 'Mobile number verified successfully',
                  confirmButtonColor: '#28a745',
                  timer: 2000,
                  showConfirmButton: false
                });

                // Lock the mobile field
                lockMobileField();

                verified = true;
                return; // Exit completely

              } else {
                // Invalid OTP - show error and loop back
                errorMsg = 'Invalid OTP. Please try again.';
                // Loop continues with error message
              }
            } catch (error) {
              Swal.close();
              Swal.fire('Error', 'Network error. Please try again.', 'error');
              return; // Exit on network error
            }
          }
        }
      }

      // Verify button click handler
      $btn.on('click', async function () {
        if ($btn.prop('disabled') || window.mobileOtpVerified) return;

        const mobile = $inp.val().trim();

        // Step 1: Confirm sending OTP
        const confirm = await swalOTPConfirm(mobile);

        if (!confirm.isConfirmed) return;

        // Step 2: Send OTP to backend
        Swal.fire({
          title: 'Sending OTP...',
          html: 'Please wait',
          didOpen: () => Swal.showLoading(),
          allowOutsideClick: false
        });

        try {
          const sendResp = await fetch('/otp/send/', {
            method: 'POST',
            headers: {
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'mobile=' + encodeURIComponent(mobile)
          });

          const sendData = await sendResp.json();
          Swal.close();

          if (!sendData.success) {
            Swal.fire('Error', sendData.error || 'OTP send failed', 'error');
            return;
          }

          // Step 3: Start OTP verification loop
          startOTPVerificationLoop(mobile);

        } catch (error) {
          Swal.close();
          Swal.fire('Error', 'Network error. Please try again.', 'error');
        }
      });

      // Expose reset function globally (for testing/debugging)
      window.resetMobileVerification = function () {
        window.mobileOtpVerified = false;
        const otpStateEl = document.getElementById('mobileOtpServerVerified');
        if (otpStateEl) otpStateEl.value = "0";

        $inp.prop('readonly', false).prop('disabled', false).val('');
        $inp.removeClass('is-valid is-invalid');
        $btn.prop('disabled', true).removeClass('verify-btn-green').addClass('verify-btn-grey').text('Verify');
        $inp.siblings('.verified-badge').remove();
        $inp.siblings('.invalid-feedback').remove();

        console.log('[OTP] Verification reset');
      };
    }

    // Apply OTP validation to mobile field
    setupMobileValidationWithOTP('#mobile', '#verifyBtn');
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

      let val = String(data[name]).trim().toLowerCase();

      // Convert boolean/numeric values to yes/no for is_aml and is_pep
      if (name === 'is_aml' || name === 'is_pep') {
        if (val === 'true' || val === '1') {
          val = 'yes';
        } else if (val === 'false' || val === '0') {
          val = 'no';
        }
      }

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
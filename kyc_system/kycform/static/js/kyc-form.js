/* kyc-form.js
   FINAL unified script (single-file)
   - Single $(document).ready wrapper
   - Modular sections with clear comments
   - Exposes date converters for prefill
   - Stable prefill pipeline
*/

$(document).ready(function () {
  "use strict";

  // ---------------------------
  // Section 0 — Utilities
  // ---------------------------
  const log = (...args) => console.debug.apply(console, args);

  function safeText(el) {
    try { return (el && el.textContent) ? el.textContent.trim() : ""; } catch { return ""; }
  }

  // Small Swal helper wrappers (uses your existing sweetalert2 html)
  function swalError(title, html) {
    if (typeof Swal !== "undefined") {
      Swal.fire({ icon: "error", title: title || "Error", html: html || "" });
    } else {
      alert((title || "Error") + "\n\n" + (html || ""));
    }
  }

  function swalFire(title, html) {
    if (typeof Swal !== "undefined") {
      return Swal.fire({ title, html, icon: "warning", confirmButtonText: "OK" });
    }
    return Promise.resolve();
  }

  // ---------------------------
  // Section 1 — Nepali Date Conversion + Datepicker initialization
  // Exposes: window.adToBsString, window.bsToAdString
  // Dispatches: "NepaliDatepickerReady" once
  // ---------------------------
  (function initNepaliDatepicker() {
    log("Init Nepali date helpers");

    // Safely reference NepaliFunctions when present
    function bsToAdString(bsVal) {
      try {
        if (!bsVal) return "";
        const parts = String(bsVal).trim().split(/[-\/]/);
        if (parts.length < 3) return "";
        const [y, m, d] = parts.map(Number);
        if (!window.NepaliFunctions || !NepaliFunctions.BS2AD) {
          console.warn("NepaliFunctions.BS2AD not available");
          return "";
        }
        const ad = NepaliFunctions.BS2AD({ year: y, month: m, day: d });
        return `${ad.year}-${String(ad.month).padStart(2, "0")}-${String(ad.day).padStart(2, "0")}`;
      } catch (e) {
        console.warn("bsToAdString failed:", e);
        return "";
      }
    }

    function adToBsString(adVal) {
      try {
        if (!adVal) return "";
        const parts = String(adVal).trim().split(/[-\/]/);
        if (parts.length < 3) return "";
        const [y, m, d] = parts.map(Number);
        if (!window.NepaliFunctions || !NepaliFunctions.AD2BS) {
          console.warn("NepaliFunctions.AD2BS not available");
          return "";
        }
        const bs = NepaliFunctions.AD2BS({ year: y, month: m, day: d });
        return `${bs.year}-${String(bs.month).padStart(2, "0")}-${String(bs.day).padStart(2, "0")}`;
      } catch (e) {
        console.warn("adToBsString failed:", e);
        return "";
      }
    }

    // Expose globally for prefill and other modules
    window.adToBsString = adToBsString;
    window.bsToAdString = bsToAdString;

    // Initialize Nepali datepickers on BS inputs (one-time)
    try {
      const bsFields = "#dob_bs, #citizen_bs, #nominee_dob_bs";
      $(bsFields).each(function () {
        const input = this;
        // Only init if plugin exists
        if (typeof $(input).nepaliDatePicker === "function") {
          $(input).nepaliDatePicker({
            ndpYear: true,
            ndpMonth: true,
            ndpYearCount: 120,
            onSelect: function (bsObj) {
              const id = input.id;
              const ad = bsToAdString(bsObj.value);
              if (id === "dob_bs") $("#dob_ad").val(ad);
              if (id === "citizen_bs") $("#citizen_ad").val(ad);
              if (id === "nominee_dob_bs") $("#nominee_dob_ad").val(ad);
            },
            onChange: function () {
              const id = input.id;
              const ad = bsToAdString(input.value);
              if (id === "dob_bs") $("#dob_ad").val(ad);
              if (id === "citizen_bs") $("#citizen_ad").val(ad);
              if (id === "nominee_dob_bs") $("#nominee_dob_ad").val(ad);
            }
          });
        } else {
          log("nepaliDatePicker() not found — ensure plugin loaded");
        }
      });
    } catch (err) {
      console.warn("Failed to initialize nepali datepicker:", err);
    }

    // AD -> BS live sync (when AD inputs change)
    $("#dob_ad, #citizen_ad, #nominee_dob_ad").on("change", function () {
      const id = this.id;
      const val = $(this).val();
      const bs = adToBsString(val);
      if (id === "dob_ad") $("#dob_bs").val(bs);
      if (id === "citizen_ad") $("#citizen_bs").val(bs);
      if (id === "nominee_dob_ad") $("#nominee_dob_bs").val(bs);
    });

    // Delay dispatch to allow the plugin to fully initialize (safe guard)
    setTimeout(() => {
      document.dispatchEvent(new Event("NepaliDatepickerReady"));
      log("NepaliDatepickerReady dispatched");
    }, 150);
  })();

  // ---------------------------
  // Section 2 — Multi-step & validation
  // -- showStep, validateStep, navigation listeners
  // ---------------------------
  let currentStep = 1;
  const totalSteps = 5;
  let highestStepReached = 1;

  // showStep must be globally available (prefill requires it)
  function showStep(step) {
    // Validate args
    if (!step || typeof step !== "number") step = 1;
    step = Math.max(1, Math.min(totalSteps, step));

    $('.form-step').removeClass('active');
    $(`.form-step[data-step="${step}"]`).addClass('active');

    $('.nav-step').removeClass('active');
    $(`.nav-step[data-step="${step}"]`).addClass('active');

    // Mark completed
    for (let i = 1; i < step; i++) {
      $(`.nav-step[data-step="${i}"]`).addClass('completed').css('cursor', 'pointer');
    }

    // Mark future steps according to highestStepReached
    for (let i = step + 1; i <= highestStepReached; i++) {
      $(`.nav-step[data-step="${i}"]`).addClass('completed').css('cursor', 'pointer');
    }
    for (let i = Math.max(highestStepReached + 1, step + 1); i <= totalSteps; i++) {
      $(`.nav-step[data-step="${i}"]`).removeClass('completed').css('cursor', 'default');
    }

    $('#currentStep').text(step);

    // Buttons visibility
    if (step === 1) $('#prevBtn').hide(); else $('#prevBtn').show();
    if (step === totalSteps) { $('#nextBtn').hide(); $('#submitBtn').show(); }
    else { $('#nextBtn').show(); $('#submitBtn').hide(); }

    // scroll top
    $('html, body').scrollTop(0);
  }

  function validateStep(step) {
    let valid = true;
    const $current = $(`.form-step[data-step="${step}"]`);
    const missingFields = [];

    $current.find('[required]').each(function () {
      const $field = $(this);
      // friendly label extraction
      const label = $field.closest('.mb-3').find('label').first().text().replace('*', '').trim();

      if ($field.is(':radio')) {
        const name = $field.attr('name');
        if (!$(`input[name="${name}"]:checked`).length) {
          valid = false;
          $field.closest('.row, .mb-3').addClass('is-invalid-group');
          if (label && !missingFields.includes(label)) missingFields.push(label);
        } else {
          $field.closest('.row, .mb-3').removeClass('is-invalid-group');
        }
      } else if ($field.is(':checkbox')) {
        if (!$field.is(':checked')) {
          valid = false;
          $field.addClass('is-invalid');
          if (label && !missingFields.includes(label)) missingFields.push(label);
        } else {
          $field.removeClass('is-invalid');
        }
      } else if ($field.attr('type') === 'file') {
    const files = $field[0].files;

    // NEW: accept already-existing uploaded file
    const existingUrl = $field.data("existing");

    if ((!files || files.length === 0) && !existingUrl) {
        valid = false;
        $field.next('button').addClass('is-invalid');
        $field.closest('.transparent-dark-div').addClass('is-invalid');
        if (label && !missingFields.includes(label)) missingFields.push(label);
    } else {
        $field.next('button').removeClass('is-invalid');
        $field.closest('.transparent-dark-div').removeClass('is-invalid');
    }
}

    });

    if (!valid) {
      let msg = 'कृपया सबै आवश्यक विवरण भर्नुहोस्।<br><small>Please fill all required fields.</small>';
      if (missingFields.length && missingFields.length <= 8) {
        msg += '<br><br><div style="text-align:left;"><strong>Missing:</strong><br>';
        missingFields.forEach(f => { msg += `• ${f}<br>`; });
        msg += '</div>';
      }
      swalError('Incomplete Form', msg);
    }

    return valid;
  }

  // Navigation events
  $('#nextBtn').on('click', function () {
    if (!validateStep(currentStep)) return;
    currentStep++;
    if (currentStep > highestStepReached) highestStepReached = currentStep;
    showStep(currentStep);
  });

  $('#prevBtn').on('click', function () {
    if (currentStep > 1) currentStep--;
    showStep(currentStep);
  });

  $('.nav-step').on('click', function (e) {
    e.preventDefault();
    const target = parseInt($(this).data('step')) || 1;
    if (target === currentStep) return;
    if (target <= highestStepReached) {
      if (target > currentStep) {
        if (!validateStep(currentStep)) return;
      }
      currentStep = target;
      showStep(currentStep);
    } else {
      swalError('Cannot Skip Steps', 'कृपया पहिले हालको पृष्ठ पूरा गर्नुहोस्।<br><small>Please complete the current page first.</small>');
    }
  });

  // Initialize
  showStep(1);

  // ---------------------------
  // Section 3 — Uploads / Previews
  // ---------------------------
  // Photo preview
  $('#photoUpload').on('change', function (e) {
    const file = this.files && this.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = function (ev) {
        $('#photoPreview').attr('src', ev.target.result);
        $('.photo-preview').removeClass('is-invalid');
      };
      reader.readAsDataURL(file);
    }
  });

  $('#removePhoto').on('click', function () {
    $('#photoUpload').val('');
    $('#photoPreview').attr('src', '/static/images/default-avatar.png');
  });

  // File name displays & preview background
  $('input[type="file"]').on('change', function () {
    const file = this.files && this.files[0];
    const $input = $(this);
    const fileNameTarget = $input.data('filename');
    if (file && fileNameTarget) {
      $('#' + fileNameTarget).text(file.name);
    }

    // preview handling for transparent-dark-div style
    const $container = $input.closest('.transparent-dark-div');
    const $removeBtn = $container.find('.remove-btn');
    const previewId = $input.data('preview');
    if (file && file.type.startsWith('image/') && previewId) {
      const reader = new FileReader();
      reader.onload = function (e) {
        const $preview = $('#' + previewId);
        $preview.css({
          'background-image': `url('${e.target.result}')`,
          'background-size': 'cover',
          'background-position': 'center',
        });
        $removeBtn.show();
      };
      reader.readAsDataURL(file);
      $container.find('button').removeClass('is-invalid');
    }
  });

  // Remove uploaded doc click
  $(document).on('click', '.remove-btn', function () {
    const $container = $(this).closest('.transparent-dark-div');
    const $input = $container.find('input[type="file"]');
    const previewId = $input.data('preview');
    const $preview = $('#' + previewId);
    $input.val('');
    $preview.css('background-image', '');
    $(this).hide();

    const fileName = $container.find('.file-name');
    const defaultText = ($input.data('filename') || '').replace(/([A-Z])/g, ' $1').trim();
    if (defaultText) {
      fileName.text(defaultText.charAt(0).toUpperCase() + defaultText.slice(1));
    }
  });

  // Nepali typing (nepalify)
  if (window.nepalify && typeof nepalify.interceptElementById === "function") {
    try {
      nepalify.interceptElementById('full_name_nep', { layout: 'traditional', enable: true });
    } catch (e) {
      console.warn("nepalify init failed", e);
    }
  }

  // ---------------------------
  // Section 4 — spouse name handling (marital_status)
  // ---------------------------
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
  $('#spouse_name').on('input change blur', function () { $(this).removeClass('is-invalid'); });

  // ---------------------------
  // Section 5 — Address cascade (province -> district -> municipality)
  // ---------------------------
  function initAddressCascade(locations) {
    function populateProvince($sel) {
      $sel.html('<option value="">Select Province</option>');
      Object.keys(locations).forEach(p => $sel.append(`<option value="${p}">${p}</option>`));
    }
    function populateDistricts(province, $districtSel, $muniSel) {
      $districtSel.html('<option value="">Select District</option>');
      $muniSel.html('<option value="">Select Municipality</option>');
      if (locations[province]) {
        Object.keys(locations[province]).forEach(d => $districtSel.append(`<option value="${d}">${d}</option>`));
      }
    }
    function populateMunicipalities(province, district, $muniSel) {
      $muniSel.html('<option value="">Select Municipality</option>');
      if (locations[province] && locations[province][district]) {
        locations[province][district].forEach(m => $muniSel.append(`<option value="${m}">${m}</option>`));
      }
    }

    populateProvince($('#perm_province'));
    $('#perm_province').on('change', function () {
      populateDistricts($(this).val(), $('#perm_district'), $('#perm_muni'));
    });
    $('#perm_district').on('change', function () {
      populateMunicipalities($('#perm_province').val(), $(this).val(), $('#perm_muni'));
    });

    populateProvince($('#temp_province'));
    $('#temp_province').on('change', function () {
      populateDistricts($(this).val(), $('#temp_district'), $('#temp_muni'));
    });
    $('#temp_district').on('change', function () {
      populateMunicipalities($('#temp_province').val(), $(this).val(), $('#temp_muni'));
    });
  }

  // Load location JSON
  $.getJSON('/static/nepal_locations.json')
    .done(function (data) {
      log('✅ Loaded Nepal location data');
      initAddressCascade(data);
      document.dispatchEvent(new Event("locationDataReady"));
    })
    .fail(function () {
      console.error('⚠️ Could not load nepal_locations.json');
      swalFire('Data Loading Error', 'Location data could not be loaded. Please refresh the page.');
    });

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

  // ---------------------------
  // Section 6 — Bank & Occupation loaders
  // Dispatch "bankDataReady" and "occupationDataReady"
  // ---------------------------
  async function loadBanks() {
    try {
      const res = await fetch('/static/nepal_banks.json');
      const banks = await res.json();
      banks.sort((a, b) => a.name.localeCompare(b.name));
      const select = document.getElementById('bankSelect');
      if (!select) return;
      banks.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.name;
        opt.textContent = b.name;
        select.appendChild(opt);
      });
      document.dispatchEvent(new Event("bankDataReady"));
    } catch (e) {
      console.error('Error loading banks:', e);
      alert('Failed to load bank list. Please try again.');
    }
  }
  loadBanks();

  async function loadOccupations() {
    try {
      const res = await fetch('/static/json/occupations.json');
      const data = await res.json();
      const occupations = data.occupations || [];
      occupations.sort((a, b) => a.name.localeCompare(b.name));
      const select = document.getElementById('occupation');
      if (!select) return;
      occupations.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.name;
        opt.textContent = item.name;
        select.appendChild(opt);
      });
      document.dispatchEvent(new Event("occupationDataReady"));
    } catch (e) {
      console.error('Error loading occupations:', e);
      alert('Failed to load profession list. Please try again.');
    }
  }
  loadOccupations();

  // ---------------------------
  // Section 7 — Financial/Occupation dependent fields
  // Note: harmonize IDs to match your HTML (use underscores)
  // ---------------------------
  (function occupationDependent() {
    const dependent = ['#annual_income', '#income_mode', '#income_source', '#pan_number'];

    function update() {
      const selected = $('#occupation').val();
      const isNoIncome = (selected === "House Wife" || selected === "Student");
      const isOther = (selected === "Other");

      if (isNoIncome) {
        $('#annual_income').prop('required', false).prop('readonly', true).val("0");
        $('#income_mode').prop('required', false).prop('readonly', true).val("Monthly");
        $('#income_source').prop('required', false).prop('readonly', true).val("None");
        $('#pan_number').prop('required', false).prop('readonly', true).val("");
        dependent.forEach(sel => $(sel).closest('.mb-3').find('label .text-danger').hide());
      } else if (isOther) {
        $('#occupation_description').prop('required', true).closest('.mb-3').find('.text-danger').show();
        $('#pan_number').prop('required', false).prop('readonly', false).val("");
        $('#pan_number').closest('.mb-3').find('label .text-danger').hide();
        $('#annual_income, #income_mode, #income_source').prop('readonly', false).prop('required', true);
      } else {
        dependent.forEach(sel => {
          $(sel).prop('required', true).prop('readonly', false).removeClass('is-invalid');
          $(sel).closest('.mb-3').find('.text-danger').show();
        });
        $('#income_mode').prop('disabled', false);
      }
    }

    $('#occupation').on('change', update);
    // initial run if needed
    update();
  })();

  // occupation_description show/hide
  (function occupationDescHandler() {
    const descDiv = $('#occupation_description').closest('.mb-3');
    const descInput = $('#occupation_description');

    $('#occupation').on('change', function () {
      if ($(this).val() === "Other") {
        descDiv.show();
        descInput.prop('required', true);
        descDiv.find('.text-danger').show();
        $('#pan_number').prop('required', false).removeClass('is-invalid');
      } else {
        descDiv.hide();
        descInput.prop('required', false).removeClass('is-invalid').val('');
        descDiv.find('.text-danger').hide();
      }
    });

    descInput.on('blur input change', function () {
      if (descDiv.is(':hidden')) $(this).removeClass('is-invalid');
    });

    // hide initially if no occupation = 194
    if ($('#occupation').val() !== "194") descDiv.hide();
  })();

  // ---------------------------
// Section 8 — Submission, Save, Save & Continue
// ---------------------------

// ---------------------------
// 8.1 — Final Submit
// ---------------------------
$('#submitBtn').on('click', function (e) {
    e.preventDefault();
    if (!validateStep(totalSteps)) return false;

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

      // Build JSON of all form inputs
      const formData = {};
      $("#kycForm").serializeArray().forEach(item => {
        formData[item.name] = item.value;
      });

      // Radios need manual capture
      ["marital_status", "gender", "is_pep", "is_aml"].forEach(name => {
        const selected = $(`input[name='${name}']:checked`).val();
        if (selected !== undefined) formData[name] = selected;
      });

      // Inject JSON into hidden field
      $("#kyc_data").val(JSON.stringify(formData));


        $('#kycForm').submit();
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
jsonData["perm_province"]      = $("#perm_province").val() || null;
jsonData["perm_district"]      = $("#perm_district").val() || null;
jsonData["perm_municipality"]  = $("#perm_muni").val() || null;
jsonData["perm_ward"]          = $("#perm_ward").val() || null;
jsonData["perm_address"]       = $("#perm_address").val() || null;
jsonData["perm_house_number"]  = $("#perm_house_number").val() || null;

// --------------------------------------
// FORCE CAPTURE OF TEMPORARY ADDRESS
// --------------------------------------
jsonData["temp_province"]      = $("#temp_province").val() || null;
jsonData["temp_district"]      = $("#temp_district").val() || null;
jsonData["temp_municipality"]  = $("#temp_muni").val() || null;
jsonData["temp_ward"]          = $("#temp_ward").val() || null;
jsonData["temp_address"]       = $("#temp_address").val() || null;
jsonData["temp_house_number"]  = $("#temp_house_number").val() || null;


    // Fix radios manually (ensures marital_status, gender, is_pep, is_aml always saved)
    const radioNames = ["marital_status", "gender", "is_pep", "is_aml"];
    radioNames.forEach(name => {
        const selected = $(`input[name='${name}']:checked`).val();
        if (selected !== undefined) {
            jsonData[name] = selected;
        }
    });

    // Track progress step
    jsonData["_current_step"] = typeof currentStep !== "undefined" ? currentStep : 1;

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


// ======================================================================
// 8.3 — Save ONLY (stay on same step)
// ======================================================================
$("#saveBtn").off("click").on("click", async function (e) {
    e.preventDefault();
    await ajaxSaveKycProgress(); // does NOT validate
});


// ======================================================================
// 8.4 — Save & Continue (validate + move to next step)
// ======================================================================
$("#saveContinueBtn").off("click").on("click", async function (e) {
    e.preventDefault();

    if (!validateStep(currentStep)) return;

    const saved = await ajaxSaveKycProgress();
    if (!saved) return;

    currentStep++;
    showStep(currentStep);
});


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
  // Section 10 — Prefill pipeline (keeps old format)
  // - Listens for locationDataReady, bankDataReady, occupationDataReady, NepaliDatepickerReady
  // - Will no-op early if showStep not ready
  // ---------------------------
  function runKycPrefill() {
    if (!window.prefill_data) { log("No prefill_data"); return; }
    const data = window.prefill_data;

    if (typeof showStep !== "function") {
      console.warn("showStep not ready yet");
      return;
    }

    log("=== KYC PREFILL START ===");

    // restore step
    if (data._current_step) {
      let s = parseInt(data._current_step) || 1;
      if (s < 1 || s > totalSteps) s = 1;
      currentStep = s; highestStepReached = Math.max(highestStepReached, currentStep);
      showStep(currentStep);
    }

    // fix auto fields
    if (data.dob_bs_auto && !data.dob_bs) data.dob_bs = data.dob_bs_auto;
    if (data.nominee_dob_bs_auto && !data.nominee_dob_bs) data.nominee_dob_bs = data.nominee_dob_bs_auto;

    // 1) basic inputs
    document.querySelectorAll('input, select, textarea').forEach(el => {
      const name = el.name;
      if (!name || !(name in data)) return;
      const value = data[name];
      if (value === null || value === undefined) return;
      if (el.type === 'file') return;

      if (el.type === 'radio') {
        if (String(el.value) === String(value)) el.checked = true;
        return;
      }
      if (el.type === 'checkbox') {
        el.checked = (value === true || value === "1" || value === "true");
        return;
      }
      el.value = value;
    });

    // 2) date conversions AD -> BS (use exposed converter)
    function fillBSDates() {
      if (typeof window.adToBsString !== "function" && !(window.NepaliFunctions && window.NepaliFunctions.AD2BS)) {
        console.warn("Date converter not ready");
        return;
      }
      try {
        if (data.dob_ad) $('#dob_bs').val(window.adToBsString ? window.adToBsString(data.dob_ad) : "");
        console.log(window.adToBsString(data.dob_ad),"PREFILL BS DATA****************");
        if (data.citizen_ad) $('#citizen_bs').val(window.adToBsString ? window.adToBsString(data.citizen_ad) : "");
        if (data.nominee_dob_ad) $('#nominee_dob_bs').val(window.adToBsString ? window.adToBsString(data.nominee_dob_ad) : "");
      } catch (e) {
        console.warn("Prefill date conversion error", e);
      }
    }
    fillBSDates();
    setTimeout(fillBSDates, 300);
    setTimeout(fillBSDates, 900);

    // ------------------------
// Fix marital status radio
// ------------------------
if (data.marital_status) {
    const ms = String(data.marital_status).trim().toLowerCase();

    $("input[name='marital_status']").each(function () {
        if (String($(this).val()).trim().toLowerCase() === ms) {
            this.checked = true;
            $(this).trigger("change");
        }
    });
}



    // 3) dynamic selects (retry until options available)
    const selectMap = [
      { key: "salutation", selector: "select[name='salutation']" },
      { key: "nationality", selector: "select[name='nationality']" },

      { key: "perm_province", selector: "#perm_province" },
      { key: "perm_district", selector: "#perm_district" },
      { key: "perm_municipality", selector: "#perm_muni" },

      { key: "temp_province", selector: "#temp_province" },
      { key: "temp_district", selector: "#temp_district" },
      { key: "temp_municipality", selector: "#temp_muni" },

      { key: "bank_name", selector: "#bankSelect" },
      { key: "account_type", selector: "select[name='account_type']" },
      { key: "occupation", selector: "#occupation" },
      { key: "qualification", selector: "#qualification" },
      { key: "nominee_relation", selector: "select[name='nominee_relation']" }
    ];

    selectMap.forEach(pair => {
      const expected = data[pair.key];
      if (!expected) return;
      const el = document.querySelector(pair.selector);
      if (!el) return;

      let attempts = 0;
      const t = setInterval(() => {
        attempts++;
        if (el.options && el.options.length > 0) {
          for (let o of el.options) {
            if (String(o.value).trim() === String(expected).trim() || String(o.textContent).trim() === String(expected).trim()) {
              el.value = o.value;
              $(el).trigger('change');
              clearInterval(t);
              return;
            }
          }
        }
        if (attempts >= 30) { console.warn("Select prefill failed for", pair.selector); clearInterval(t); }
      }, 150);
    });

        // ---------- Extra prefills & fallbacks ----------
    // 1) Ensure radios (marital_status, gender, is_pep, is_aml) always get set
    (function ensureRadios() {
      ['marital_status','gender','is_pep','is_aml'].forEach(name => {
        if (data[name] !== undefined && data[name] !== null && String(data[name]).trim() !== "") {
          const val = String(data[name]).trim();
          const $r = $(`input[name="${name}"][value="${val}"]`);
          if ($r.length) {
            $r.prop('checked', true).trigger('change');
          } else {
            // some backends send booleans for is_pep/is_aml (true/false) — handle 'true'/'false'
            const alt = (val === 'true' || val === 'True') ? 'true' : (val === 'false' || val === 'False') ? 'false' : null;
            if (alt) {
              $(`input[name="${name}"][value="${alt}"]`).prop('checked', true).trigger('change');
            }
          }
        }
      });
    })();

    // 2) Branch name fallback: accept either 'branch_name' or 'bank_branch'
    (function fillBranch() {
      const branchVal = data.branch_name || data.bank_branch || data.bank_branch_name || "";
      if (branchVal && document.querySelector('input[name="branch_name"]')) {
        document.querySelector('input[name="branch_name"]').value = branchVal;
      }
      // also try a common id if you use one
      if (branchVal && document.getElementById('branch_name')) {
        document.getElementById('branch_name').value = branchVal;
      }
    })();

    // 3) Temporary address retry: if temp fields exist in data with alternate keys, copy them
    (function fixTempAddressDelayed() {
      const d = window.prefill_data;
      if (!d) return;

      // Stage 1: province
      setTimeout(() => {
        if (d.temp_province) {
          $("#temp_province").val(d.temp_province).trigger("change");
        }
      }, 300);

      // Stage 2: district (after province loads)
      setTimeout(() => {
        if (d.temp_district) {
          $("#temp_district").val(d.temp_district).trigger("change");
        }
      }, 600);

      // Stage 3: municipality (after district loads)
      setTimeout(() => {
        if (d.temp_municipality) {
          $("#temp_muni").val(d.temp_municipality).trigger("change");
        }
      }, 900);

      // Ward, address, house number (plain fields)
      setTimeout(() => {
        if (d.temp_ward) $("#temp_ward").val(d.temp_ward);
        if (d.temp_address) $("#temp_address").val(d.temp_address);
        if (d.temp_house_number) $("#temp_house_number").val(d.temp_house_number);
      }, 950);
    })();



    log("=== PREFILL DONE ===");
  }

  // ensure prefill runs after all data sources arrive
(function waitForAllData() {
  let have = { loc: false, bank: false, occ: false, date: false };
  document.addEventListener('locationDataReady', () => { have.loc = true; if (have.bank && have.occ && have.date) runKycPrefill(); });
  document.addEventListener('bankDataReady',     () => { have.bank = true; if (have.loc && have.occ && have.date) runKycPrefill(); });
  document.addEventListener('occupationDataReady',() => { have.occ = true; if (have.loc && have.bank && have.date) runKycPrefill(); });
  document.addEventListener('NepaliDatepickerReady', () => { have.date = true; if (have.loc && have.bank && have.occ) runKycPrefill(); });
})();


  // Show saved files if present in data (data === window.prefill_data)
function showSavedFiles() {
    const prefill = window.prefill_data;
    if (!prefill) return;

    // -----------------------
    // PHOTO
    // -----------------------
    if (prefill.photo_url) {
        $("#photoPreview").attr("src", prefill.photo_url);
        $("#photoBtn").text("Change");
        $("#photoUpload").data("existing", prefill.photo_url);
    }

    // -----------------------
    // CITIZENSHIP FRONT
    // -----------------------
    if (prefill.citizenship_front_url) {
        $("#citizenship_front .transparent-dark-div").css({
            "background-image": `url(${prefill.citizenship_front_url})`,
            "background-size": "cover",
            "background-position": "center"
        });
        $("#citizenshipFrontFileName")
            .text(prefill.citizenship_front_url.split("/").pop());

        $("#citizenshipFrontUpload").data("existing", prefill.citizenship_front_url);
    }

    // -----------------------
    // CITIZENSHIP BACK
    // -----------------------
    if (prefill.citizenship_back_url) {
        $("#citizenship_back .transparent-dark-div").css({
            "background-image": `url(${prefill.citizenship_back_url})`,
            "background-size": "cover",
            "background-position": "center"
        });
        $("#citizenshipBackFileName")
            .text(prefill.citizenship_back_url.split("/").pop());

        $("#citizenshipBackUpload").data("existing", prefill.citizenship_back_url);
    }

    // -----------------------
    // SIGNATURE
    // -----------------------
    if (prefill.signature_url) {
        $("#signature .transparent-dark-div").css({
            "background-image": `url(${prefill.signature_url})`,
            "background-size": "cover",
            "background-position": "center"
        });
        $("#signatureFileName")
            .text(prefill.signature_url.split("/").pop());

        $("#signatureUpload").data("existing", prefill.signature_url);
    }

    // -----------------------
    // PASSPORT DOC
    // -----------------------
    if (prefill.passport_doc_url) {
        $("#passport_doc .transparent-dark-div").css({
            "background-image": `url(${prefill.passport_doc_url})`,
            "background-size": "cover",
            "background-position": "center"
        });
        $("#passportFileName")
            .text(prefill.passport_doc_url.split("/").pop());

        $("#passport_docUpload").data("existing", prefill.passport_doc_url);
    }

    // -----------------------
    // NID DOC
    // -----------------------
    if (prefill.nid_url) {
        $("#Nid_doc .transparent-dark-div").css({
            "background-image": `url(${prefill.nid_url})`,
            "background-size": "cover",
            "background-position": "center"
        });
        $("#nidFileName")
            .text(prefill.nid_url.split("/").pop());

        $("#NidUpload").data("existing", prefill.nid_url);
    }
}


showSavedFiles(window.prefill_data);

// final delayed call (optional, stable)
setTimeout(() => {
    showSavedFiles(window.prefill_data);
}, 300);


  // Prefill attach points — listen to all readiness events
  document.addEventListener("locationDataReady", runKycPrefill);
  document.addEventListener("bankDataReady", runKycPrefill);
  document.addEventListener("occupationDataReady", runKycPrefill);
  document.addEventListener("NepaliDatepickerReady", function () {
    // ensure showStep is ready
    if (typeof showStep !== "function") {
      console.warn("showStep not ready yet - scheduling prefill");
      setTimeout(runKycPrefill, 200);
      return;
    }
    runKycPrefill();
  });

  // also expose runKycPrefill globally if you want to trigger manually
  window.runKycPrefill = runKycPrefill;

  console.log("✅ KYC Form script loaded");
});

$("#nep-first-name").on("input", function() {
    let value = $(this).val();
    // Allow only Devanagari characters (U+0900–U+097F) and spaces
    value = value.replace(/[^\u0900-\u097F\s]/g, '');
    $(this).val(value);
  });


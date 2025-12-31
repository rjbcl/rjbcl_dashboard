// =============================
// Additional Documents Handler
// Manages dynamic document upload fields
// =============================

const AdditionalDocs = {

  // Configuration
  maxDocuments: 5,
  nextDocIndex: 1, // Tracks the next unique index to assign
  maxFileSize: 500 * 1024, // 500KB
  allowedTypes: ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'],

  /**
   * Initialize the additional documents handler
   */
  init: function () {
    this.loadExistingDocuments();
    this.setupAddMoreButton();
    this.updateCounter();
    console.log('✅ Additional documents handler initialized');
  },

  /**
   * Get current document count from DOM
   */
  getCurrentDocCount: function () {
    const count = $('.additional-doc-item').length;
    console.log('📊 Current doc count:', count);
    return count;
  },

  /**
   * Load existing documents from Django template into the container
   */
  loadExistingDocuments: function () {
    const self = this;
    const $existingDocs = $('#existingAdditionalDocs');

    if ($existingDocs.length && $existingDocs.children('.existing-doc-data').length > 0) {
      console.log('📁 Loading', $existingDocs.children('.existing-doc-data').length, 'existing documents');

      $existingDocs.children('.existing-doc-data').each(function () {
        const docId = $(this).data('doc-id');
        const docName = $(this).data('doc-name');
        const docUrl = $(this).data('doc-url');
        const uploadedAt = $(this).data('uploaded-at');
        const fileName = $(this).data('file-name');

        self.addExistingDocumentField(docId, docName, docUrl, uploadedAt, fileName);
      });

      // Remove the hidden data container
      $existingDocs.remove();
    }

    // If no existing documents, add the first empty field
    if (this.getCurrentDocCount() === 0) {
      console.log('➕ No existing docs, adding first empty field');
      this.addDocumentField();
    }
  },

  /**
   * Add an existing document field to the container
   */
  addExistingDocumentField: function (docId, docName, docUrl, uploadedAt, fileName) {
    const docIndex = this.nextDocIndex++;

    console.log('➕ Adding existing doc:', docIndex, docName);

    const $docHTML = $(`
      <div class="additional-doc-item existing-doc" data-doc-index="${docIndex}" data-existing-doc-id="${docId}">
        <button type="button" class="remove-doc-btn" data-remove-doc="${docIndex}">
          ✕
        </button>
        <div class="row align-items-end mb-3">
          <div class="col-md-6">
            <label class="form-label">Document Name</label>
            <input type="text" name="additional_doc_name_${docIndex}" class="form-control" value="${docName}" readonly>
          </div>
          <div class="col-md-6">
            <label class="form-label">Attached Document</label>
            <div class="document-upload-inline" id="additionalDoc${docIndex}Container">
              <button type="button" class="btn btn-outline-success btn-sm view-file-btn">
                <span class="upload-icon-btn">🔍</span> View File
              </button>
              <span class="file-name-inline has-file">${fileName || docName}</span>
              <small class="text-muted d-block mt-1" style="font-size: 0.75rem;">
                Uploaded: ${uploadedAt}
              </small>
            </div>
            <input type="hidden" name="existing_doc_id_${docIndex}" value="${docId}">
            <input type="hidden" name="existing_doc_url_${docIndex}" value="${docUrl}">
          </div>
        </div>
      </div>
    `);

    // Setup click handler for view file button
    $docHTML.find('.view-file-btn').on('click', function () {
      window.open(docUrl, '_blank');
    });

    // Append to container
    $('#additionalDocsContainer').append($docHTML);

    console.log('✅ Existing doc added. Total docs now:', this.getCurrentDocCount());

    this.updateCounter();
    this.updateAddButton();
  },

  /**
   * Setup the "Add More" button
   */
  setupAddMoreButton: function () {
    const self = this;

    // Use event delegation for dynamically added remove buttons
    $(document).on('click', '[data-remove-doc]', function () {
      const docIndex = $(this).data('remove-doc');
      console.log('🗑️ Remove button clicked for doc:', docIndex);
      self.removeDocumentField(docIndex);
    });

    // Add more button handler
    $('#addMoreDocBtn').on('click', function () {
      const currentCount = self.getCurrentDocCount();

      console.log('➕ Add More clicked. Current count:', currentCount);

      if (currentCount < self.maxDocuments) {
        self.addDocumentField();
      } else {
        Swal.fire({
          icon: 'info',
          title: 'Maximum Limit Reached',
          text: 'You can only attach up to 5 additional documents.',
          confirmButtonText: 'Okay',
          confirmButtonColor: '#28a745',
          customClass: {
            popup: 'swal-nepali'
          }
        });
      }
    });
  },

  /**
   * Add a new document field
   */
  addDocumentField: function () {
    const self = this;
    const docIndex = this.nextDocIndex++;

    console.log('➕ Adding new doc field:', docIndex);

    const $docHTML = $(`
      <div class="additional-doc-item" data-doc-index="${docIndex}">
        <button type="button" class="remove-doc-btn" data-remove-doc="${docIndex}">
          ✕
        </button>
        <div class="row align-items-end mb-3">
          <div class="col-md-6">
            <label class="form-label">Document Name</label>
            <input type="text" name="additional_doc_name_${docIndex}" class="form-control" placeholder="e.g., Passport, License, etc.">
          </div>
          <div class="col-md-6">
            <label class="form-label">Attach Document</label>
            <div class="document-upload-inline" id="additionalDoc${docIndex}Container">
              <input type="file" id="additionalDoc${docIndex}Upload" name="additional_doc_${docIndex}" accept="image/*,application/pdf" style="display:none;">
              <button type="button" class="btn btn-outline-secondary btn-sm choose-file-btn">
                <span class="upload-icon-btn">📎</span> Choose File
              </button>
              <span class="file-name-inline" id="additionalDoc${docIndex}FileName">No file chosen</span>
            </div>
          </div>
        </div>
      </div>
    `);

    // Append to container
    $('#additionalDocsContainer').append($docHTML);

    console.log('✅ New doc field added. Total docs now:', this.getCurrentDocCount());

    // Setup click handler for choose file button
    $docHTML.find('.choose-file-btn').on('click', function () {
      console.log('📎 Choose file clicked for doc:', docIndex);
      $(`#additionalDoc${docIndex}Upload`).trigger('click');
    });

    // Setup upload handler for this document
    this.setupDocumentUpload(docIndex);

    this.updateCounter();
    this.updateAddButton();

    // Scroll to the new field
    $docHTML[0].scrollIntoView({
      behavior: 'smooth',
      block: 'nearest'
    });
  },

  /**
   * Remove a document field
   * @param {number} docIndex - Index of document to remove
   */
  removeDocumentField: function (docIndex) {
    const self = this;
    const $docItem = $(`[data-doc-index="${docIndex}"]`);

    // Check if the element exists before trying to remove it
    if (!$docItem.length) {
      console.warn('⚠️ Document item not found:', docIndex);
      return;
    }

    console.log('🗑️ Removing doc:', docIndex);

    const isExisting = $docItem.hasClass('existing-doc');
    const existingDocId = $docItem.data('existing-doc-id');

    const messageText = isExisting
      ? 'This will mark the document for deletion. You must save the form to complete the removal.'
      : 'Are you sure you want to remove this document field?';

    Swal.fire({
      title: 'Remove Document?',
      html: messageText,
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#28a745',
      cancelButtonColor: '#6c757d',
      confirmButtonText: 'Yes, Remove',
      cancelButtonText: 'Cancel',
      customClass: {
        popup: 'swal-nepali'
      }
    }).then((result) => {
      if (result.isConfirmed) {
        console.log('✅ User confirmed removal of doc:', docIndex);

        // Remove the document item
        $docItem.fadeOut(300, function () {
          if (isExisting && existingDocId) {
            // Add hidden input to track deletion
            const $hiddenInput = $(`<input type="hidden" name="delete_doc_id[]" value="${existingDocId}">`);
            $('#additionalDocsContainer').append($hiddenInput);
            console.log('🗑️ Marked existing doc for deletion:', existingDocId);
          }

          $(this).remove();
          console.log('✅ Doc removed from DOM. Total docs now:', self.getCurrentDocCount());

          // Update UI after removal
          self.updateCounter();
          self.updateAddButton();

          // If all documents removed, add an empty field
          const remainingCount = self.getCurrentDocCount();
          if (remainingCount === 0) {
            console.log('📝 No docs left, adding empty field');
            self.addDocumentField();
          }
        });
      }
    });
  },

  /**
   * Setup upload handler for a specific document
   * @param {number} docIndex - Document index
   */
  setupDocumentUpload: function (docIndex) {
    const self = this;

    $(`#additionalDoc${docIndex}Upload`).on('change', function (e) {
      const file = e.target.files[0];
      console.log('📄 File selected for doc', docIndex, ':', file ? file.name : 'none');

      if (file) {
        // Validate file
        const validation = self.validateFile(file);

        if (!validation.valid) {
          if (validation.error === 'size') {
            swalError(
              'File Too Large',
              'File size must be less than 500 KB.'
            );
          } else if (validation.error === 'type') {
            swalError(
              'Invalid File Type',
              'Please upload a valid image (JPG, JPEG, PNG) or PDF file.'
            );
          }
          // Clear the input
          $(this).val('');
          return;
        }

        console.log('✅ File validation passed for:', file.name);

        // Update filename display
        $(`#additionalDoc${docIndex}FileName`)
          .text(file.name)
          .addClass('has-file');

        // Update button style
        const $container = $(`#additionalDoc${docIndex}Container`);
        $container.find('.btn')
          .removeClass('btn-outline-secondary')
          .addClass('btn-outline-success');

        // Show remove button for this uploaded file
        self.showFileRemoveButton(docIndex);
      }
    });
  },

  /**
   * Show remove button for uploaded file
   * @param {number} docIndex - Document index
   */
  showFileRemoveButton: function (docIndex) {
    const $container = $(`#additionalDoc${docIndex}Container`);

    // Check if remove button already exists
    if ($container.find('.remove-file-btn').length === 0) {
      const $removeBtn = $(`
        <button type="button" class="btn btn-outline-danger btn-sm ms-2 remove-file-btn" data-doc-index="${docIndex}">
          <span>✕</span> Remove File
        </button>
      `);

      $container.append($removeBtn);

      // Setup click handler
      $removeBtn.on('click', function () {
        const idx = $(this).data('doc-index');
        console.log('🗑️ Remove file clicked for doc:', idx);

        $(`#additionalDoc${idx}Upload`).val('');
        $(`#additionalDoc${idx}FileName`)
          .text('No file chosen')
          .removeClass('has-file');

        $(`#additionalDoc${idx}Container .btn:first`)
          .removeClass('btn-outline-success')
          .addClass('btn-outline-secondary');

        $(this).remove();

        console.log('✅ File removed from doc:', idx);
      });
    }
  },

  /**
   * Validate uploaded file
   * @param {File} file - File to validate
   * @returns {Object} - Validation result
   */
  validateFile: function (file) {
    if (!file) {
      return { valid: false, error: 'No file selected' };
    }

    // Check file size
    if (file.size > this.maxFileSize) {
      return { valid: false, error: 'size' };
    }

    // Check file type
    if (!this.allowedTypes.includes(file.type)) {
      return { valid: false, error: 'type' };
    }

    return { valid: true };
  },

  /**
   * Update the document counter display
   */
  updateCounter: function () {
    const currentCount = this.getCurrentDocCount();
    $('#docCounter').text(`(${currentCount}/${this.maxDocuments} documents)`);
    console.log('🔄 Counter updated:', currentCount, '/', this.maxDocuments);
  },

  /**
   * Update the "Add More" button state
   */
  updateAddButton: function () {
    const currentCount = this.getCurrentDocCount();

    if (currentCount >= this.maxDocuments) {
      $('#addMoreDocBtn')
        .prop('disabled', true)
        .removeClass('btn-outline-success')
        .addClass('btn-secondary');
      console.log('🔒 Add More button disabled (max reached)');
    } else {
      $('#addMoreDocBtn')
        .prop('disabled', false)
        .removeClass('btn-secondary')
        .addClass('btn-outline-success');
      console.log('✅ Add More button enabled');
    }
  },

  /**
   * Get all uploaded additional documents info
   * @returns {Array} - Array of document info
   */
  getUploadedDocs: function () {
    const docs = [];

    $('.additional-doc-item').each(function () {
      const $item = $(this);
      const docIndex = $item.data('doc-index');
      const name = $item.find(`input[name="additional_doc_name_${docIndex}"]`).val();
      const hasFile = $(`#additionalDoc${docIndex}Upload`)[0]?.files.length > 0;
      const isExisting = $item.hasClass('existing-doc');

      if (name || hasFile || isExisting) {
        docs.push({
          index: docIndex,
          name: name,
          hasFile: hasFile,
          isExisting: isExisting
        });
      }
    });

    return docs;
  },

  /**
   * Validate that documents with files have names
   * @returns {boolean} - Validation result
   */
  validateDocs: function () {
    let valid = true;
    const missingNames = [];

    $('.additional-doc-item').each(function () {
      const $item = $(this);
      if (!$item.hasClass('existing-doc')) {
        const docIndex = $item.data('doc-index');
        const name = $item.find(`input[name="additional_doc_name_${docIndex}"]`).val();
        const hasFile = $(`#additionalDoc${docIndex}Upload`)[0]?.files.length > 0;

        // If file is uploaded but no name provided
        if (hasFile && !name.trim()) {
          valid = false;
          $item.find(`input[name="additional_doc_name_${docIndex}"]`).addClass('is-invalid');
          missingNames.push(`Document ${docIndex}`);
        } else {
          $item.find(`input[name="additional_doc_name_${docIndex}"]`).removeClass('is-invalid');
        }
      }
    });

    if (!valid) {
      swalError(
        'Missing Document Names',
        'Please provide names for all uploaded documents.'
      );
    }
    return valid;
  },

  /**
   * Reset all additional documents
   */
  resetAll: function () {
    console.log('🔄 Resetting all additional documents');

    // Remove all document items
    $('.additional-doc-item').remove();

    // Remove delete markers
    $('input[name="delete_doc_id[]"]').remove();

    this.nextDocIndex = 1;

    // Add one empty field
    this.addDocumentField();

    console.log('✅ Reset complete');
  }
};

// Initialize on document ready
$(function () {
  AdditionalDocs.init();
});

// Make it available globally
window.AdditionalDocs = AdditionalDocs;


// =======================================
// PASSPORT PHOTO UPLOAD & PREVIEW WITH VALIDATION
// =======================================

$('#photoUpload').on('change', function (e) {
  const file = this.files && this.files[0];

  if (file) {
    // File size validation (300KB limit based on your code)
    if (file.size > 300000) {
      swalError(
        'File Too Large',
        'Image size must be less than 300 KB. Please upload a smaller image.'
      );
      $('#photoUpload').val('');
      $('#photoPreview').attr('src', '/static/images/default-avatar.png');
      return;
    }

    // File type validation
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      swalError(
        'Invalid File Type',
        'Please upload a valid image file (JPG, JPEG, or PNG only).'
      );
      $('#photoUpload').val('');
      $('#photoPreview').attr('src', '/static/images/default-avatar.png');
      return;
    }

    // If validation passes, load and preview the image
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = function (ev) {
        $('#photoPreview').attr('src', ev.target.result);
        $('.photo-preview').removeClass('is-invalid');
        $('photoBtn').removeClass('is-invalid');
        $('#photoBtn').text('Change');
      };
      reader.readAsDataURL(file);
    }
  }
});

$('#removePhoto').on('click', function () {
  $('#photoUpload').val('');
  $('#photoUpload').removeData('existing'); // Clear existing photo reference
  $('.photo-preview').removeClass('is-invalid');
  $('#photoPreview').attr('src', '/static/images/default-avatar.png');
  $('#photoBtn').text('Upload');
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

// =======================================
// DOCUMENT PREUPLOAD 
// =======================================

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
    $("#citizenship_front").css({
      "background-image": `url(${prefill.citizenship_front_url})`,
      "background-size": "cover",
      "background-position": "center"
    });
    $("#citizenshipFrontUpload").closest(".transparent-dark-div").find(".remove-btn").show();
    $("#citizenshipFrontFileName")
      .text(prefill.citizenship_front_url.split("/").pop());

    $("#citizenshipFrontUpload").data("existing", prefill.citizenship_front_url);
  }

  // -----------------------
  // CITIZENSHIP BACK
  // -----------------------
  if (prefill.citizenship_back_url) {
    $("#citizenship_back").css({
      "background-image": `url(${prefill.citizenship_back_url})`,
      "background-size": "cover",
      "background-position": "center"
    });
    $("#citizenshipBackUpload").closest(".transparent-dark-div").find(".remove-btn").show();
    $("#citizenshipBackFileName")
      .text(prefill.citizenship_back_url.split("/").pop());

    $("#citizenshipBackUpload").data("existing", prefill.citizenship_back_url);
  }

  // -----------------------
  // SIGNATURE
  // -----------------------
  if (prefill.signature_url) {
    $("#signature").css({
      "background-image": `url(${prefill.signature_url})`,
      "background-size": "cover",
      "background-position": "center"
    });
    $('#signatureUpload').trigger('change');
    $("#signatureUpload").closest(".transparent-dark-div").find(".remove-btn").show();

    $("#signatureFileName")
      .text(prefill.signature_url.split("/").pop());

    $("#signatureUpload").data("existing", prefill.signature_url);
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
    $("#NidUpload").closest(".transparent-dark-div").find(".remove-btn").show();
    $("#nidFileName")
      .text(prefill.nid_url.split("/").pop());

    $("#NidUpload").data("existing", prefill.nid_url);
  }
}
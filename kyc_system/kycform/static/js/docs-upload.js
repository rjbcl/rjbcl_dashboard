// =============================
// Additional Documents Handler
// Manages dynamic document upload fields
// =============================

const AdditionalDocs = {

    // Configuration
    maxDocuments: 5,
    currentDocCount: 1,
    maxFileSize: 500 * 1024, // 500KB
    allowedTypes: ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'],

    /**
     * Initialize the additional documents handler
     */
    init: function () {
        this.setupAddMoreButton();
        this.setupFirstDocumentUpload();
        this.updateCounter();
        console.log('✅ Additional documents handler initialized');
    },

    /**
     * Setup the "Add More" button
     */
    setupAddMoreButton: function () {
        const self = this;

        // Use event delegation for dynamically added remove buttons
        $(document).on('click', '[data-remove-doc]', function () {
            const docIndex = $(this).data('remove-doc');
            self.removeDocumentField(docIndex);
        });

        // Add more button handler
        $('#addMoreDocBtn').on('click', function () {
            if (self.currentDocCount < self.maxDocuments) {
                self.addDocumentField();
            } else {
                debugger
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
     * Setup first document upload handler
     */
    setupFirstDocumentUpload: function () {
        const self = this;

        // Setup click handler for first document's choose file button
        $('#chooseFile1').on('click', function () {
            $('#additionalDoc1Upload').trigger('click');
        });

        // Setup upload handler
        this.setupDocumentUpload(1);
    },

    /**
     * Add a new document field
     */
    addDocumentField: function () {
        const self = this;
        this.currentDocCount++;
        const docIndex = this.currentDocCount;

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

        // Setup click handler for choose file button
        $docHTML.find('.choose-file-btn').on('click', function () {
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
        debugger
        Swal.fire({
            title: 'Remove Document?',
            html: 'Are you sure you want to remove this document field?',
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
                $(`[data-doc-index="${docIndex}"]`).fadeOut(300, function () {
                    $(this).remove();
                    self.currentDocCount--;
                    self.updateCounter();
                    self.updateAddButton();
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
                            'Please upload a valid image (JPG, PNG) or PDF file.'
                        );
                    }
                    // Clear the input
                    $(this).val('');
                    return;
                }

                // Update filename display
                $(`#additionalDoc${docIndex}FileName`)
                    .text(file.name)
                    .addClass('has-file');

                // Show success indicator
                $(`#additionalDoc${docIndex}Container`)
                    .find('.btn')
                    .removeClass('btn-outline-secondary')
                    .addClass('btn-outline-success');
            }
        });
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
        $('#docCounter').text(`(${this.currentDocCount}/${this.maxDocuments} documents)`);
    },

    /**
     * Update the "Add More" button state
     */
    updateAddButton: function () {
        if (this.currentDocCount >= this.maxDocuments) {
            $('#addMoreDocBtn')
                .prop('disabled', true)
                .removeClass('btn-outline-success')
                .addClass('btn-secondary');
        } else {
            $('#addMoreDocBtn')
                .prop('disabled', false)
                .removeClass('btn-secondary')
                .addClass('btn-outline-success');
        }
    },

    /**
     * Get all uploaded additional documents info
     * @returns {Array} - Array of document info
     */
    getUploadedDocs: function () {
        const docs = [];

        for (let i = 1; i <= this.currentDocCount; i++) {
            const $item = $(`[data-doc-index="${i}"]`);
            if ($item.length) {
                const name = $item.find(`input[name="additional_doc_name_${i}"]`).val();
                const hasFile = $(`#additionalDoc${i}Upload`)[0]?.files.length > 0;

                if (name || hasFile) {
                    docs.push({
                        index: i,
                        name: name,
                        hasFile: hasFile
                    });
                }
            }
        }

        return docs;
    },

    /**
     * Validate that documents with files have names
     * @returns {boolean} - Validation result
     */
    validateDocs: function () {
        let valid = true;
        const missingNames = [];

        for (let i = 1; i <= this.maxDocuments; i++) {
            const $item = $(`[data-doc-index="${i}"]`);
            if ($item.length) {
                const name = $item.find(`input[name="additional_doc_name_${i}"]`).val();
                const hasFile = $(`#additionalDoc${i}Upload`)[0]?.files.length > 0;

                // If file is uploaded but no name provided
                if (hasFile && !name.trim()) {
                    valid = false;
                    $item.find(`input[name="additional_doc_name_${i}"]`).addClass('is-invalid');
                    missingNames.push(`Document ${i}`);
                } else {
                    $item.find(`input[name="additional_doc_name_${i}"]`).removeClass('is-invalid');
                }
            }
        }

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
        // Remove all except first
        $('.additional-doc-item').not('[data-doc-index="1"]').remove();

        // Reset first document
        $('input[name="additional_doc_name_1"]').val('');
        $('#additionalDoc1Upload').val('');
        $('#additionalDoc1FileName').text('No file chosen').removeClass('has-file');
        $('#additionalDoc1Container .btn')
            .removeClass('btn-outline-success')
            .addClass('btn-outline-secondary');

        this.currentDocCount = 1;
        this.updateCounter();
        this.updateAddButton();
    }
};

// Initialize on document ready
$(function () {
    AdditionalDocs.init();
});

// Make it available globally
window.AdditionalDocs = AdditionalDocs;
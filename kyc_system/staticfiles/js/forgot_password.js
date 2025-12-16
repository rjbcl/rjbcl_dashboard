$(document).ready(function() {
    
    // ===========================
    // DJANGO MESSAGES HANDLING
    // ===========================
    $('.js-msg').each(function() {
        const msgTags = $(this).data('tags');
        const msgText = $(this).data('text');
        
        if (msgTags.includes('success')) {
            showSuccessAlert(msgText);
        } else if (msgTags.includes('error') || msgTags.includes('danger')) {
            showErrorAlert("Please enter valid credential");
        } else if (msgTags.includes('warning')) {
            showErrorAlert(msgText+"warning");
        } else {
            showErrorAlert(msgText);
        }
    });

    // ===========================
    // FORM VALIDATION
    // ===========================
    $('#forgotPasswordForm').on('submit', function(e) {
        // Clear previous errors
        clearAllErrors();
        
        const identifier = $('#identifierInput').val().trim();
        const dob = $('#dob_bs').val().trim();
        let hasError = false;
        
        // Validate identifier
        if (!identifier) {
            showFieldError('identifierError', 'This field is required');
            $('#identifierInput').addClass('is-invalid');
            hasError = true;
        }
        
        // Validate DOB
        if (!dob) {
            showFieldError('dobError', 'Date of birth is required');
            $('#dob_bs').addClass('is-invalid');
            hasError = true;
        } else {
            // Check if DOB is not in future
            const selectedDate = new Date(dob);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate > today) {
                showErrorAlert("Future date selected");
                $('#dob_bs').addClass('is-invalid');
                hasError = false;
            } 
        }
        
        // If there are errors, prevent submission
        if (hasError) {
            e.preventDefault();
            showErrorAlert('Please correct the errors below'+hasError);
            return false;
        }
        
        // Show loading state
        const submitBtn = $('#submitBtn');
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>Verifying...');
    });

    // ===========================
    // INPUT VALIDATION & CLEARING
    // ===========================
    
    // Remove error styling on input
    $('#identifierInput, #dob_bs').on('input change', function() {
        const inputId = $(this).attr('id');
        const errorId = inputId.replace('Input', 'Error');
        
        $(this).removeClass('is-invalid');
        $(`#${errorId}`).removeClass('show').text('');
        hideErrorAlert();
    });
    
    // Add focus effect
    $('.form-control').on('focus', function() {
        $(this).parent().addClass('focused');
    });
    
    $('.form-control').on('blur', function() {
        $(this).parent().removeClass('focused');
    });

    // ===========================
    // KEYBOARD SHORTCUTS
    // ===========================
    
    // Allow Enter key to submit form
    $('input').on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            $('#forgotPasswordForm').submit();
        }
    });
    
    // ESC key to go back
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            const backLink = $('.back-link a').attr('href');
            if (backLink) {
                window.location.href = backLink;
            }
        }
    });

    // ===========================
    // SECURITY ENHANCEMENTS
    // ===========================
    
    // Prevent multiple form submissions
    let isSubmitting = false;
    $('#forgotPasswordForm').on('submit', function() {
        if (isSubmitting) {
            return false;
        }
        isSubmitting = true;
        setTimeout(function() {
            isSubmitting = false;
        }, 3000);
    });

    // ===========================
    // ACCESSIBILITY IMPROVEMENTS
    // ===========================
    
    // Add aria-labels
    $('#identifierInput').attr('aria-label', 'Enter your identifier');
    $('#dob_bs').attr('aria-label', 'Select your date of birth');
    $('#submitBtn').attr('aria-label', 'Verify and reset password');

    // ===========================
    // CONSOLE INFO (Development)
    // ===========================
    console.log('%c🔐 Forgot Password Page Loaded', 'color: #00146D; font-size: 14px; font-weight: bold;');
    console.log('%cKeyboard Shortcuts:', 'color: #007A43; font-weight: bold;');
    console.log('  Enter: Submit form');
    console.log('  ESC: Go back to login');

});

// ===========================
// UTILITY FUNCTIONS
// ===========================

// Show error alert at top of form
function showErrorAlert(message) {
    const errorAlert = $('#errorAlert');
    $('#errorMessage').text(message);
    errorAlert.fadeIn(300);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        errorAlert.fadeOut(300);
    }, 5000);
}

// Hide error alert
function hideErrorAlert() {
    $('#errorAlert').fadeOut(300);
}

// Show success alert at top of form
function showSuccessAlert(message) {
    const successAlert = $('#successAlert');
    $('#successMessage').text(message);
    successAlert.fadeIn(300);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        successAlert.fadeOut(300);
    }, 5000);
}

// Hide success alert
function hideSuccessAlert() {
    $('#successAlert').fadeOut(300);
}

// Show field-specific error message
function showFieldError(errorId, message) {
    const errorEl = $(`#${errorId}`);
    errorEl.text(message);
    errorEl.addClass('show');
}

// Clear all error messages
function clearAllErrors() {
    $('.field-error').removeClass('show').text('');
    $('.form-control').removeClass('is-invalid');
    hideErrorAlert();
}

// Validate date format
function isValidDate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date);
}


// ===========================
// NEPALI DATE PICKER INITIALIZATION
// ===========================
$('#dob_bs').nepaliDatePicker({
    dateFormat: 'YYYY-MM-DD',
    closeOnDateSelect: true,
    ndpYear: true,
    ndpMonth: true,
    ndpYearCount: 100,
    disableDaysAfter: 0,  // Disable future dates
    maxDate: NepaliFunctions.BS.GetCurrentDate() // Max date is today
});
$(document).ready(function () {

  // ===========================
  // TAB SWITCHING
  // ===========================
  $('.tab-btn').on('click', function () {
    const targetTab = $(this).data('tab');

    // Update active tab button
    $('.tab-btn').removeClass('active');
    $(this).addClass('active');

    // Switch form containers
    $('.form-container').removeClass('active');
    if (targetTab === 'policy') {
      $('#policyFormWrapper').addClass('active');
    } else if (targetTab === 'agent') {
      $('#agentFormWrapper').addClass('active');
    }
  });

  // Set active tab from Django context (if provided)
  if (window.activeTab) {
    const tabButton = $(`.tab-btn[data-tab="${window.activeTab}"]`);
    if (tabButton.length) {
      tabButton.click();
    }
  }

  // ===========================
  // PASSWORD VISIBILITY TOGGLE
  // ===========================
  $('.toggle-password').on('click', function () {
    const targetId = $(this).data('target');
    const passwordInput = $(`#${targetId}`);
    const icon = $(this).find('i');

    if (passwordInput.attr('type') === 'password') {
      passwordInput.attr('type', 'text');
      icon.removeClass('bi-eye').addClass('bi-eye-slash');
    } else {
      passwordInput.attr('type', 'password');
      icon.removeClass('bi-eye-slash').addClass('bi-eye');
    }
  });

  // ===========================
  // DJANGO MESSAGES (SweetAlert2)
  // ===========================
  $('.js-msg').each(function () {
    const msgTags = $(this).data('tags');
    const msgText = $(this).data('text');

    let icon = 'info';
    let title = 'Notice';

    if (msgTags.includes('success')) {
      icon = 'success';
      title = 'Success!';
    } else if (msgTags.includes('error') || msgTags.includes('danger')) {
      icon = 'error';
      title = 'Error';
    } else if (msgTags.includes('warning')) {
      icon = 'warning';
      title = 'Warning';
    }

    Swal.fire({
      icon: icon,
      title: title,
      text: msgText,
      confirmButtonColor: '#4379F2',
      timer: 5000,
      timerProgressBar: true
    });
  });

  // ===========================
  // FORM VALIDATION ENHANCEMENT
  // ===========================
  $('form').on('submit', function (e) {
    const form = $(this);
    const submitBtn = form.find('button[type="submit"]');

    // Check if all required fields are filled
    let isValid = true;
    form.find('[required]').each(function () {
      if (!$(this).val().trim()) {
        isValid = false;
        $(this).addClass('is-invalid');
      } else {
        $(this).removeClass('is-invalid');
      }
    });

    if (!isValid) {
      e.preventDefault();
      Swal.fire({
        icon: 'warning',
        title: 'Required Fields',
        text: 'Please fill in all required fields.',
        confirmButtonColor: '#4379F2'
      });
      return false;
    }

    // Disable submit button to prevent double submission
    submitBtn.prop('disabled', true);
    submitBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>Signing in...');
  });

  // Remove invalid class on input
  $('input').on('input', function () {
    $(this).removeClass('is-invalid');
  });

  // ===========================
  // SMOOTH ANIMATIONS
  // ===========================
  // Add focus effect to form controls
  $('.form-control').on('focus', function () {
    $(this).parent().addClass('focused');
  });

  $('.form-control').on('blur', function () {
    $(this).parent().removeClass('focused');
  });

  // ===========================
  // SECURITY ENHANCEMENTS
  // ===========================
  // Prevent form autocomplete for sensitive fields
  // $('input[type="password"]').attr('autocomplete', 'new-password');

  // Clear password fields on page load (security measure)
  $('input[type="password"]').val('');

  // ===========================
  // LOADING STATE MANAGEMENT
  // ===========================
  // Show loading state when navigating away
  $('a').on('click', function (e) {
    const href = $(this).attr('href');
    if (href && !href.startsWith('#') && !$(this).hasClass('no-loading')) {
      // Show a brief loading indicator
      $('body').css('opacity', '0.7');
    }
  });

  // ===========================
  // ACCESSIBILITY IMPROVEMENTS
  // ===========================
  // Add aria-labels for screen readers
  $('.toggle-password').attr('aria-label', 'Toggle password visibility');
  $('.tab-btn').each(function () {
    const tabName = $(this).data('tab');
    $(this).attr('aria-label', `Switch to ${tabName} login`);
  });

});

// ===========================
// UTILITY FUNCTIONS
// ===========================

// Validate email format
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Show custom error message
function showError(message) {
  Swal.fire({
    icon: 'error',
    title: 'Oops...',
    text: message,
    confirmButtonColor: '#4379F2'
  });
}

// Show success message
function showSuccess(message) {
  Swal.fire({
    icon: 'success',
    title: 'Success!',
    text: message,
    confirmButtonColor: '#4379F2',
    timer: 3000,
    timerProgressBar: true
  });
}


// VALIDATION REAL TIME
$('#policy-number, #agent-code').on('blur', function () {
  const $field = $(this);
  if (!$field.val() || $field.val().trim() === '') {
    // Don't add invalid class if field is pan-number AND occupation is 194
    $field.addClass('is-invalid');

  } else {
    $field.removeClass('is-invalid');
  }
});
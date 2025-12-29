function swalError(errorTitle, errorMessage) {
  Swal.fire({
    icon: 'error',
    title: errorTitle,
    html: errorMessage,
    confirmButtonText: 'Okay',
    confirmButtonColor: '#28a745',
    customClass: {
      popup: 'swal-nepali'
    }
  });
}

function swalFire(errorTitle, errorMessage) {
  Swal.fire({
    icon: 'warning',
    title: errorTitle,
    text: errorMessage,
    confirmButtonText: 'Okay',
    confirmButtonColor: '#28a745',
    allowOutsideClick: false
  })
}



function swalQuestion(title, html, confirmButtonText) {
  Swal.fire({
    title: title,
    html: html,
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#28a745',
    cancelButtonColor: '#6c757d',
    confirmButtonText: confirmButtonText,
    cancelButtonText: 'Cancel',
    customClass: {
      popup: 'swal-nepali'
    }
  })
}


// SweetAlert helper wrappers
function swalError(title, html) {
  if (typeof Swal !== "undefined") {
    Swal.fire({
      icon: "error",
      title: title || "Error",
      html: html || ""
    });
  } else {
    alert((title || "Error") + "\n\n" + (html || ""));
  }
}

function swalFire(title, html) {
  if (typeof Swal !== "undefined") {
    return Swal.fire({
      title,
      html,
      icon: "warning",
      confirmButtonText: "OK"
    });
  }
  return Promise.resolve();
}


// New function for OTP confirmation
function swalOTPConfirm(mobileNumber) {
  return Swal.fire({
    title: 'Verify Mobile Number',
    html: `<p class="mb-3">Send OTP to:</p><h5 class="text-primary">${mobileNumber}</h5>`,
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#28a745',
    cancelButtonColor: '#6c757d',
    confirmButtonText: 'Send OTP',
    cancelButtonText: 'Cancel',
    customClass: {
      popup: 'swal-nepali'
    }
  });
}

function swalOTPInput(mobileNumber, errorMessage = '') {
      return Swal.fire({
        title: 'Enter OTP',
        html: `
          <p class="mb-3">OTP sent to: <strong>${mobileNumber}</strong></p>
          <div class="otp-container" style="display: flex; justify-content: center; gap: 8px; margin: 20px 0;">
            <input type="text" class="otp-box" maxlength="1" data-index="0" style="width: 45px; height: 50px; text-align: center; font-size: 20px; border: 2px solid #ddd; border-radius: 8px; outline: none;">
            <input type="text" class="otp-box" maxlength="1" data-index="1" style="width: 45px; height: 50px; text-align: center; font-size: 20px; border: 2px solid #ddd; border-radius: 8px; outline: none;">
            <input type="text" class="otp-box" maxlength="1" data-index="2" style="width: 45px; height: 50px; text-align: center; font-size: 20px; border: 2px solid #ddd; border-radius: 8px; outline: none;">
            <input type="text" class="otp-box" maxlength="1" data-index="3" style="width: 45px; height: 50px; text-align: center; font-size: 20px; border: 2px solid #ddd; border-radius: 8px; outline: none;">
            <input type="text" class="otp-box" maxlength="1" data-index="4" style="width: 45px; height: 50px; text-align: center; font-size: 20px; border: 2px solid #ddd; border-radius: 8px; outline: none;">
            <input type="text" class="otp-box" maxlength="1" data-index="5" style="width: 45px; height: 50px; text-align: center; font-size: 20px; border: 2px solid #ddd; border-radius: 8px; outline: none;">
          </div>
          <div id="otpError" style="color: #dc3545; font-size: 14px; margin-top: 10px; font-weight: bold; ${errorMessage ? 'display: block;' : 'display: none;'}">${errorMessage}</div>
          <div style="margin-top: 20px;">
            <button id="resendBtn" class="btn btn-link" style="color: #6c757d; text-decoration: none; cursor: not-allowed; font-size: 14px;" disabled>
              Resend OTP in <span id="timer">02:00</span>
            </button>
          </div>
        `,
        icon: 'info',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Verify OTP',
        cancelButtonText: 'Cancel',
        allowOutsideClick: false,
        allowEscapeKey: false,
        customClass: {
          popup: 'swal-nepali'
        },
        preConfirm: () => {
          const boxes = document.querySelectorAll('.otp-box');
          let otp = '';
          boxes.forEach(box => otp += box.value);
          
          const errorDiv = document.getElementById('otpError');
          
          if (!otp || otp.length === 0) {
            errorDiv.textContent = 'Please enter OTP';
            errorDiv.style.display = 'block';
            return false;
          }
          if (otp.length !== 6) {
            errorDiv.textContent = 'Please enter all 6 digits';
            errorDiv.style.display = 'block';
            return false;
          }
          
          errorDiv.style.display = 'none';
          return otp;
        },
        didOpen: () => {
          const boxes = document.querySelectorAll('.otp-box');
          const errorDiv = document.getElementById('otpError');
          const resendBtn = document.getElementById('resendBtn');
          const timerSpan = document.getElementById('timer');
          
          // Focus first box
          boxes[0].focus();
          
          // Start countdown timer (2 minutes = 120 seconds)
          let timeLeft = 120;
          const countdown = setInterval(() => {
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerSpan.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
              clearInterval(countdown);
              resendBtn.disabled = false;
              resendBtn.style.cursor = 'pointer';
              resendBtn.style.color = '#28a745';
              resendBtn.innerHTML = 'Resend OTP';
            }
          }, 1000);
          
          // Resend OTP functionality
          resendBtn.addEventListener('click', function() {
            if (!this.disabled) {
              // Clear all boxes
              boxes.forEach(box => box.value = '');
              boxes[0].focus();
              
              // Show sending message
              Swal.fire({
                title: 'Resending OTP...',
                html: 'Please wait',
                allowOutsideClick: false,
                didOpen: () => {
                  Swal.showLoading();
                }
              });
              
              // Simulate API call
              setTimeout(() => {
                Swal.close();
                // Reopen the OTP input with fresh timer
                swalOTPInput(mobileNumber, '');
              }, 1500);
            }
          });
          
          // OTP box navigation logic
          boxes.forEach((box, index) => {
            // Clear error on input
            box.addEventListener('input', () => {
              const currentError = errorDiv.textContent;
              if (currentError !== 'Invalid OTP. Please try again.') {
                errorDiv.style.display = 'none';
              }
              
              // Only allow digits
              box.value = box.value.replace(/[^0-9]/g, '');
              
              // Auto-focus next box
              if (box.value && index < boxes.length - 1) {
                boxes[index + 1].focus();
              }
            });
            
            // Handle backspace
            box.addEventListener('keydown', (e) => {
              if (e.key === 'Backspace' && !box.value && index > 0) {
                boxes[index - 1].focus();
              }
            });
            
            // Handle paste
            box.addEventListener('paste', (e) => {
              e.preventDefault();
              const pastedData = e.clipboardData.getData('text').replace(/[^0-9]/g, '');
              
              for (let i = 0; i < pastedData.length && index + i < boxes.length; i++) {
                boxes[index + i].value = pastedData[i];
              }
              
              // Focus the next empty box or last box
              const nextEmpty = Array.from(boxes).findIndex((b, i) => i >= index && !b.value);
              if (nextEmpty !== -1) {
                boxes[nextEmpty].focus();
              } else {
                boxes[boxes.length - 1].focus();
              }
            });
            
            // Prevent non-numeric input
            box.addEventListener('keypress', (e) => {
              if (!/^\d$/.test(e.key)) {
                e.preventDefault();
              }
            });
          });
        }
      });
    }

    // Mobile validation setup with OTP integration
    function setupMobileValidation(inputSelector, buttonSelector) {
      const $inp = $(inputSelector);
      const $btn = $(buttonSelector);
      let isVerified = false;

      // Existing keypress validation
      $inp.on('keypress', function (e) {
        const char = String.fromCharCode(e.which);
        const allowed = /[0-9+]/;
        if (e.which === 8 || e.which === 0 || e.which === 9) return true;
        if (!allowed.test(char)) { 
          e.preventDefault(); 
          return false; 
        }
      });

      // Existing paste validation
      $inp.on('paste', function () {
        setTimeout(() => {
          let val = $(this).val(); 
          $(this).val(val.replace(/[^0-9+]/g, ''));
        }, 0);
      });

      // Enhanced blur/input validation with button state management
      $inp.on('blur input', function () {
        // Don't validate if already verified
        if (isVerified) return;

        const $el = $(this); 
        $el.next('.invalid-feedback').remove(); 
        $el.removeClass('is-invalid is-valid');
        
        const v = $el.val().trim(); 
        
        if (!v) {
          $btn.removeClass('verify-btn-green').addClass('verify-btn-grey').prop('disabled', true);
          return;
        }
        
        const digits = v.replace(/[^0-9]/g, '').length;
        
        if (digits < 10) {
          $el.addClass('is-invalid');
          $el.after('<div class="invalid-feedback d-block">Mobile number must have at least 10 digits</div>');
          $btn.removeClass('verify-btn-green').addClass('verify-btn-grey').prop('disabled', true);
        } else {
          $el.addClass('is-valid');
          $btn.removeClass('verify-btn-grey').addClass('verify-btn-green').prop('disabled', false);
        }
      });

      // Verify button click handler
      $btn.on('click', async function() {
        if ($(this).prop('disabled') || isVerified) return;

        const mobileNumber = $inp.val().trim();
        
        // Step 1: Confirm sending OTP
        const confirmResult = await swalOTPConfirm(mobileNumber);
        
        if (confirmResult.isConfirmed) {
          // Simulate sending OTP (here you would make an API call)
          Swal.fire({
            title: 'Sending OTP...',
            html: 'Please wait',
            allowOutsideClick: false,
            didOpen: () => {
              Swal.showLoading();
            }
          });

          // Simulate API delay
          setTimeout(async () => {
            Swal.close();
            
            // Step 2: Get OTP from user
            const otpResult = await swalOTPInput(mobileNumber);
            
            if (otpResult.isConfirmed) {
              const enteredOTP = otpResult.value;
              
              // Simulate OTP verification (replace with actual API call)
              // For demo purposes, accept "123456" as valid OTP
              if (enteredOTP === '123456') {
                // Success!
                isVerified = true;
                
                Swal.fire({
                  icon: 'success',
                  title: 'Verified!',
                  text: 'Mobile number verified successfully',
                  confirmButtonColor: '#28a745',
                  timer: 2000,
                  showConfirmButton: false
                });

                // Update UI
                $inp.prop('readonly', true).prop('disabled', true);
                $inp.removeClass('is-valid').addClass('is-valid');
                $btn.prop('disabled', true).removeClass('verify-btn-green').addClass('verify-btn-grey').text('Verified ✓');
                
                // Add verified badge
                if (!$inp.siblings('.verified-badge').length) {
                  $inp.parent().css('position', 'relative');
                  $inp.after('<span class="verified-badge">✓ Verified</span>');
                }
              } else {
                // Invalid OTP
                swalError('Invalid OTP', 'The OTP you entered is incorrect. Please try again.');
              }
            }
          }, 1500);
        }
      });

      return {
        isVerified: () => isVerified,
        reset: () => {
          isVerified = false;
          $inp.prop('readonly', false).prop('disabled', false).val('');
          $inp.removeClass('is-valid is-invalid');
          $btn.prop('disabled', true).removeClass('verify-btn-green').addClass('verify-btn-grey').text('Verify');
          $inp.siblings('.verified-badge').remove();
          $inp.siblings('.invalid-feedback').remove();
        }
      };
    }

    // Initialize validation for both mobile fields
    $(document).ready(function() {
      const mobileValidation = setupMobileValidation('#mobile', '#verifyBtn');
      const contactMobileValidation = setupMobileValidation('#contact_mobile', '#contactVerifyBtn');

      // Form submission example
      $('form').on('submit', function(e) {
        e.preventDefault();
        
        if (!mobileValidation.isVerified()) {
          swalError('Verification Required', 'Please verify your mobile number before submitting.');
          return false;
        }
        
        if (!contactMobileValidation.isVerified()) {
          swalError('Verification Required', 'Please verify your contact mobile number before submitting.');
          return false;
        }

        Swal.fire({
          icon: 'success',
          title: 'Form Submitted!',
          text: 'All mobile numbers verified successfully',
          confirmButtonColor: '#28a745'
        });
      });
    });
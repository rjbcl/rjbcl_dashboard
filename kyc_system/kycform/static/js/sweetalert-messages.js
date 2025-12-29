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
          
          // Close current popup and trigger resend
          Swal.clickConfirm();
          
          // Trigger resend via custom event
          const resendEvent = new CustomEvent('otp-resend-requested', {
            detail: { mobile: mobileNumber }
          });
          document.dispatchEvent(resendEvent);
        }
      });
      
      // OTP box navigation logic
      boxes.forEach((box, index) => {
        // Clear error on input
        box.addEventListener('input', () => {
          const currentError = errorDiv.textContent;
          if (currentError !== errorMessage) {
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
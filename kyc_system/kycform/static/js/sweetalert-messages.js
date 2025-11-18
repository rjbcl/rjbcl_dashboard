function swalError(errorTitle, errorMessage)
  {
     Swal.fire({
        icon: 'warning',
        title: errorTitle,
        html: errorMessage,
        confirmButtonText: 'OK',
        confirmButtonColor: '#28a745',
        customClass: {
          popup: 'swal-nepali'
        }
      });
  }

function swalFire(errorTitle, errorMessage)
  {
    Swal.fire({
        icon: 'error',
        title: errorTitle,
        text: errorMessage,
        confirmButtonText: 'Refresh Page',
        confirmButtonColor: '#28a745',
        allowOutsideClick: false
      })
  }

  

function swalQuestion(title, html, confirmButtonText)
  {
      Swalfire({
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
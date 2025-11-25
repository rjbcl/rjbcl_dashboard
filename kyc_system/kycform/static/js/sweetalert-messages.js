function swalError(errorTitle, errorMessage)
  {
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

function swalFire(errorTitle, errorMessage)
  {
    Swal.fire({
        icon: 'warning',
        title: errorTitle,
        text: errorMessage,
        confirmButtonText: 'Okay',
        confirmButtonColor: '#28a745',
        allowOutsideClick: false
      })
  }

  

function swalQuestion(title, html, confirmButtonText)
  {
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
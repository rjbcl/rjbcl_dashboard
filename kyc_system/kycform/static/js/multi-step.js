$(document).ready(function () {
    window.currentStep = 1;
    const totalSteps = 5;
    let highestStepReached = 1;

    function showStep(step) {
        if (step < 1 || step > 5) step = 1
        currentStep = step
        $('.form-step').removeClass('active');
        $(`.form-step[data-step="${step}"]`).addClass('active');

        $('.nav-step').removeClass('active');
        $(`.nav-step[data-step="${step}"]`).addClass('active');

        // Mark completed steps and make them clickable
        for (let i = 1; i < step; i++) {
            $(`.nav-step[data-step="${i}"]`).addClass('completed').css('cursor', 'pointer');
        }

        // Make current step clickable
        $(`.nav-step[data-step="${step}"]`).css('cursor', 'pointer');

        // Mark steps that user has reached before as accessible
        for (let i = step + 1; i <= highestStepReached; i++) {
            $(`.nav-step[data-step="${i}"]`).addClass('completed').css('cursor', 'pointer');
        }

        // Make unreached future steps non-clickable
        for (let i = highestStepReached + 1; i <= totalSteps; i++) {
            $(`.nav-step[data-step="${i}"]`).css('cursor', 'default');
        }

        $('#currentStep').text(step);

        // Button visibility
        if (step === 1) {
            $('#prevBtn').hide();
        } else {
            $('#prevBtn').show();
        }

        if (step === totalSteps) {
            $('#saveContinueBtn').hide();
            $('#submitBtn').show();
            $('#previewBtn').show();

        } else {
            $('#saveContinueBtn').show();
            $('#submitBtn').hide();
            $('#previewBtn').hide();
        }

        // Scroll to top
        $('html, body').scrollTop(0);
    }

    function validateStep(step, updateHighest = false) {
        let valid = true;
        const $current = $(`.form-step[data-step="${step}"]`);
        const missingFields = [];

        $current.find('[required]').each(function () {
            const $field = $(this);
            // friendly label extraction
            const label = getFieldLabel($field);

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
                    $field.next('#photoBtn').removeClass('is-invalid');
                    $field.parent().siblings('.photo-preview').addClass('is-invalid');
                    if (label && !missingFields.includes(label)) {
                        missingFields.push(label);
                    }
                } else {
                    $field.next('button').removeClass('is-invalid');
                    $field.parent().siblings('.photo-preview').removeClass('is-invalid');
                }
            }
            else {
                if (!$field.val() || $field.val().trim() === '') {
                    valid = false;
                    $field.addClass('is-invalid');
                    if (label && !missingFields.includes(label)) {
                        missingFields.push(label);
                    }
                } else {
                    $field.removeClass('is-invalid');
                }
            }
        });

        // Check if mobile number (#mobile) is verified via OTP
        const $mobileField = $current.find('#mobile');
        if ($mobileField.length > 0 && $mobileField.attr('required')) {
            // Check if the mobile validation object exists and if it's verified
            if (window.mobileValidation && !window.mobileValidation.isVerified()) {
                valid = false;
                const mobileLabel = getFieldLabel($mobileField) || 'Mobile Number';
                if (!missingFields.includes(mobileLabel + ' (Not Verified)')) {
                    missingFields.push(mobileLabel + ' (Not Verified)');
                }
                // Add visual indicator
                $mobileField.addClass('is-invalid');
            }
        }

        if (!valid) {
            let errorMessage = 'कृपया सबै आवश्यक विवरण भर्नुहोस्।<br><small>Please fill all required fields.</small>';
            highestStepReached = step;  //anush
            if (missingFields.length > 0 && missingFields.length <= 5) {
                errorMessage += '<br><br><div style="text-align: left; font-size: 13px;"><strong>Missing:</strong><br>';
                missingFields.forEach(field => {
                    errorMessage += `• ${field}<br>`;
                });
                errorMessage += '</div>';
            }
            swalError('Incomplete Form', errorMessage);

            // Remove completed class from this step and all steps ahead
            for (var i = totalSteps; i >= step; i--) {
                $(`.nav-step[data-step="${i}"]`).removeClass('completed');
            }
        }

        // Only update highestStepReached when explicitly told to (when moving forward)
        if (updateHighest && valid && step > highestStepReached) {
            highestStepReached = step;
        }

        // Mark as completed only if valid and we're updating
        if (valid && updateHighest) {
            $(`.nav-step[data-step="${step}"]`).addClass('completed');
        }

        return valid;
    }

    
    $('#saveContinueBtn').off('click').on('click', async function (e) {
        e.preventDefault();
        if (!validateStep(currentStep, true)) return;
        const saved = await ajaxSaveKycProgress();
        if (!saved) return;
        currentStep++;
        if (currentStep > highestStepReached) {
            highestStepReached = currentStep;
        }
        showStep(currentStep);
    });

    $('#prevBtn').on('click', function () {
        currentStep--;
        showStep(currentStep);
    });

    // Allow navigation through sidebar
    $('.nav-step').on('click', function (e) {
        e.preventDefault();
        const targetStep = parseInt($(this).data('step'));

        // Can't click on the same step
        if (targetStep === currentStep) {
            return;
        }

        // Allow navigation to any previously reached step
        if (targetStep <= highestStepReached) {
            // If going forward, validate current step first
            if (targetStep > currentStep) {
                let allValid = true;

                // validate every step from current up to targetStep (but don't update highest)
                for (let step = currentStep; step < targetStep; step++) {
                    if (!validateStep(step, false)) {
                        allValid = false;
                        break;
                    }
                }

                // only move if all steps are valid
                if (allValid) {
                    currentStep = targetStep;
                    showStep(currentStep);
                }
            }
            else {
                // Going backward - no validation needed
                currentStep = targetStep;
                showStep(currentStep);
            }
        } else {
            // Trying to skip to an unreached step - show error
            swalError('Cannot Skip Steps', 'कृपया पहिले हालको पृष्ठ पूरा गर्नुहोस्।<br><small>Please complete the current page first.</small>');
        }
    });

    // Initialize first step
    showStep(1);

    // ⭐ EXPOSE GLOBALLY - Add these lines at the end
    window.showStep = showStep;
    window.validateStep = validateStep;
    window.currentStep = currentStep;
    window.totalSteps = totalSteps;
    window.highestStepReached = highestStepReached;

    // Expose getter/setter for currentStep since it's a primitive
    window.getCurrentStep = () => currentStep;
    window.setCurrentStep = (step) => {
        currentStep = step;
        if (step > highestStepReached) {
            highestStepReached = step;
            window.highestStepReached = highestStepReached;
        }
        window.currentStep = currentStep;
    };

    function getFieldLabel($field) {
        let label = '';

        // Try multiple strategies to find the label

        // Strategy 1: Standard form-label in same parent
        label = $field.closest('.mb-3, .col-md-6, .photo-upload-controls, .document-upload')
            .find('label.form-label').first().text();

        // Strategy 2: Label with 'for' attribute matching field ID
        if (!label && $field.attr('id')) {
            label = $(`label[for="${$field.attr('id')}"]`).text();
        }

        // Strategy 3: Previous sibling label
        if (!label) {
            label = $field.prev('label').text();
        }

        // Strategy 4: Any label in parent container
        if (!label) {
            label = $field.parent().find('label').first().text();
        }

        // Strategy 5: Check data-filename span (for document uploads)
        if (!label && $field.attr('data-filename')) {
            const fileNameSpan = $(`#${$field.attr('data-filename')}`);
            if (fileNameSpan.length) {
                label = fileNameSpan.text();
            }
        }

        // Strategy 6: Use the field name as fallback
        if (!label) {
            label = $field.attr('name') || 'Field';
            // Convert snake_case or kebab-case to Title Case
            label = label.replace(/[-_]/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());
        }

        // Clean up the label
        label = label.replace(/\*/g, '').trim();

        return label || 'Field';
    }

    // Usage examples:
    // const label = getFieldLabel($('#photoUpload')); // "Passport Size Photo"
    // const label = getFieldLabel($('#citizenshipFrontUpload')); // "Citizenship Front"
    // const label = getFieldLabel($('input[name="first_name"]')); // "First Name"
});
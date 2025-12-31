$(document).ready(function() {
function showPreviewModal(data) {
    
            function formatLabel(key) {
                return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            }

            function createField(label, value) {
                if (value === null || value === undefined || value === '') {
                    return '';
                }
                return `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <strong class="text-muted d-block small">${label}</strong>
                        <span>${value}</span>
                    </div>
                `;
            }

            function createImageField(label, url) {
                if (!url) return '';
                return `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <strong class="text-muted d-block small">${label}</strong>
                        <img src="${url}" class="img-thumbnail mt-2" style="max-width: 200px; max-height: 200px;" alt="${label}">
                    </div>
                `;
            }

            // Personal Information
            $('#personalInfo').html(
                createField('Salutation', data.salutation) +
                createField('First Name', data.first_name) +
                createField('Middle Name', data.middle_name) +
                createField('Last Name', data.last_name) +
                createField('Full Name (Nepali)', data.full_name_nep) +
                createField('Email', data.email) +
                createField('Mobile', data.mobile) +
                createField('Gender', data.gender) +
                createField('Nationality', data.nationality) +
                createField('Marital Status', data.marital_status) +
                createField('Date of Birth (AD)', data.dob_ad) +
                createField('Date of Birth (BS)', data.dob_bs) +
                createField('Spouse Name', data.spouse_name) +
                createField('Father Name', data.father_name) +
                createField('Mother Name', data.mother_name) +
                createField('Grand Father Name', data.grand_father_name) +
                createField('Father in Law Name', data.father_in_law_name) +
                createField('Son Name', data.son_name) +
                createField('Daughter Name', data.daughter_name) +
                createField('Daughter in Law Name', data.daughter_in_law_name) +
                createField('Citizenship No', data.citizenship_no) +
                createField('Citizenship Date (BS)', data.citizen_bs) +
                createField('Citizenship Date (AD)', data.citizen_ad) +
                createField('Citizenship Place', data.citizenship_place) +
                createField('Passport No', data.passport_no) +
                createField('NID No', data.nid_no) +
                createField('PAN Number', data.pan_number) +
                createField('Qualification', data.qualification)
            );

            // Permanent Address
            $('#permAddress').html(
                createField('Province', data.perm_province) +
                createField('District', data.perm_district) +
                createField('Municipality', data.perm_municipality) +
                createField('Ward', data.perm_ward) +
                createField('Address', data.perm_address) +
                createField('House Number', data.perm_house_number)
            );

            // Temporary Address
            $('#tempAddress').html(
                createField('Province', data.temp_province) +
                createField('District', data.temp_district) +
                createField('Municipality', data.temp_municipality) +
                createField('Ward', data.temp_ward) +
                createField('Address', data.temp_address) +
                createField('House Number', data.temp_house_number)
            );

            // Bank Information
            $('#bankInfo').html(
                createField('Bank Name', data.bank_name) +
                createField('Bank Branch', data.bank_branch) +
                createField('Branch Name', data.branch_name) +
                createField('Account Number', data.account_number) +
                createField('Account Type', data.account_type)
            );

            // Occupation Information
            $('#occupationInfo').html(
                createField('Occupation', data.occupation) +
                createField('Occupation Description', data.occupation_description) +
                createField('Income Mode', data.income_mode) +
                createField('Annual Income', data.annual_income ? 'Rs. ' + data.annual_income.toLocaleString() : null) +
                createField('Income Source', data.income_source) +
                createField('Employer Name', data.employer_name) +
                createField('Office Address', data.office_address) +
                createField('Is PEP', data.is_pep ? data.is_pep.toUpperCase() : null) +
                createField('Is AML', data.is_aml ? data.is_aml.toUpperCase() : null)
            );

            // Nominee Information
            $('#nomineeInfo').html(
                createField('Nominee Name', data.nominee_name) +
                createField('Relation', data.nominee_relation) +
                createField('Date of Birth (AD)', data.nominee_dob_ad) +
                createField('Date of Birth (BS)', data.nominee_dob_bs) +
                createField('Contact', data.nominee_contact) +
                createField('Guardian Name', data.guardian_name) +
                createField('Guardian Relation', data.guardian_relation)
            );

            // Documents
            $('#documents').html(
                createImageField('Photo', data.photo_url) +
                createImageField('Citizenship Front', data.citizenship_front_url) +
                createImageField('Citizenship Back', data.citizenship_back_url) +
                createImageField('Signature', data.signature_url) +
                createImageField('Passport', data.passport_doc_url) +
                createImageField('NID', data.nid_url)
            );

            // Show modal
            $('#previewModal').modal('show');
        }

        // Make function globally accessible
        window.showPreviewModal = showPreviewModal;
    });
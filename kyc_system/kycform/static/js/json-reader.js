// Load location JSON
$.getJSON('/static/json/nepal_locations.json')
    .done(function (data) {
        console.log('✅ Loaded Nepal location data from json reader');
        initAddressCascade(data);
        document.dispatchEvent(new Event("locationDataReady"));
    })
    .fail(function () {
        console.error('⚠️ Could not load nepal_locations.json');
        swalFire('Data Loading Error', 'Location data could not be loaded. Please refresh the page.').then((result) => {
            if (result.isConfirmed) {
                location.reload();
            }
        });
    });

// Section 5 — Address cascade (province -> district -> municipality)
function initAddressCascade(locations) {
    function populateProvince($sel) {
        $sel.html('<option value="">Select Province</option>');
        Object.keys(locations).forEach(p => $sel.append(`<option value="${p}">${p}</option>`));
    }
    function populateDistricts(province, $districtSel, $muniSel) {
        $districtSel.html('<option value="">Select District</option>');
        $muniSel.html('<option value="">Select Municipality</option>');
        if (locations[province]) {
            Object.keys(locations[province]).forEach(d => $districtSel.append(`<option value="${d}">${d}</option>`));
        }
    }
    function populateMunicipalities(province, district, $muniSel) {
        $muniSel.html('<option value="">Select Municipality</option>');
        if (locations[province] && locations[province][district]) {
            locations[province][district].forEach(m => $muniSel.append(`<option value="${m}">${m}</option>`));
        }
    }

    populateProvince($('#perm_province'));
    $('#perm_province').on('change', function () {
        populateDistricts($(this).val(), $('#perm_district'), $('#perm_muni'));
    });
    $('#perm_district').on('change', function () {
        populateMunicipalities($('#perm_province').val(), $(this).val(), $('#perm_muni'));
    });

    populateProvince($('#temp_province'));
    $('#temp_province').on('change', function () {
        populateDistricts($(this).val(), $('#temp_district'), $('#temp_muni'));
    });
    $('#temp_district').on('change', function () {
        populateMunicipalities($('#temp_province').val(), $(this).val(), $('#temp_muni'));
    });
}


// ---------------------------
// Section 6 — Bank & Occupation loaders
// Dispatch "bankDataReady" and "occupationDataReady"
// ---------------------------
async function loadBanks() {
    try {
        const res = await fetch('/static/json/nepal_banks.json');
        const banks = await res.json();
        banks.sort((a, b) => a.name.localeCompare(b.name));
        const select = document.getElementById('bankSelect');
        if (!select) return;
        banks.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b.name;
            opt.textContent = b.name;
            select.appendChild(opt);
        });
        document.dispatchEvent(new Event("bankDataReady"));
    } catch (e) {
        console.error('Error loading banks:', e);
        alert('Failed to load bank list. Please try again.');
    }
}


async function loadOccupations() {
    try {
        const res = await fetch('/static/json/occupations.json');
        const data = await res.json();
        const occupations = data.occupations || [];
        occupations.sort((a, b) => a.name.localeCompare(b.name));
        const select = document.getElementById('occupation');
        if (!select) return;
        occupations.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.name;
            opt.textContent = item.name;
            select.appendChild(opt);
        });
        document.dispatchEvent(new Event("occupationDataReady"));
    } catch (e) {
        console.error('Error loading occupations:', e);
        alert('Failed to load profession list. Please try again.');
    }
}

loadBanks();
loadOccupations();

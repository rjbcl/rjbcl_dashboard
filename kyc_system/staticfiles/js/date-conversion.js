/**************************************************
 * INTEGRATED DATE CONVERSION SCRIPT
 * With bindBsAdSync logic for prefill
 **************************************************/

$(document).ready(function () {

    /**************************************************
     * SweetAlert Helper
     **************************************************/
    function swalFire(title, text) {
        Swal.fire({
            icon: 'error',
            title: title,
            text: text,
            confirmButtonColor: '#d33'
        });
    }

    /**************************************************
     * Nepali Digits → Latin Digits
     **************************************************/
    function nepaliToLatin(str) {
        if (!str) return "";
        return str.replace(/[०-९]/g, d => String.fromCharCode(d.charCodeAt(0) - 2406));
    }

    /**************************************************
     * Normalize BS String
     **************************************************/
    function normalizeBS(raw) {
        if (!raw) return "";

        let s = nepaliToLatin(String(raw).trim())
            .replace(/\s+/g, "")
            .replace(/[^\d\-\/]/g, "")
            .replace(/\//g, "-");

        if (/^\d{8}$/.test(s)) {
            return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
        }

        const p = s.split("-");
        if (p.length === 3) {
            return `${p[0]}-${p[1].padStart(2, "0")}-${p[2].padStart(2, "0")}`;
        }
        return "";
    }

    /**************************************************
     * BS → AD
     **************************************************/
    function bsToAd(bsInput) {
        try {
            if (typeof bsInput === "object" && bsInput.year) {
                const ad = NepaliFunctions.BS2AD({
                    year: Number(bsInput.year),
                    month: Number(bsInput.month),
                    day: Number(bsInput.day)
                });
                return `${ad.year}-${String(ad.month).padStart(2, "0")}-${String(ad.day).padStart(2, "0")}`;
            }

            const normalized = normalizeBS(bsInput);
            if (!normalized) return "";

            const [y, m, d] = normalized.split("-").map(Number);
            const ad = NepaliFunctions.BS2AD({ year: y, month: m, day: d });

            return `${ad.year}-${String(ad.month).padStart(2, "0")}-${String(ad.day).padStart(2, "0")}`;
        } catch (e) {
            console.error("BS → AD error:", e);
            return "";
        }
    }

    /**************************************************
     * AD → BS
     **************************************************/
    function adToBs(adRaw) {
        try {
            if (!adRaw) return "";

            const [y, m, d] = adRaw.split("-").map(Number);
            const bs = NepaliFunctions.AD2BS({ year: y, month: m, day: d });

            return `${bs.year}-${String(bs.month).padStart(2, "0")}-${String(bs.day).padStart(2, "0")}`;
        } catch (e) {
            console.error("AD → BS error:", e);
            return "";
        }
    }

    /**************************************************
     * Expose globally for prefill and other modules
     **************************************************/
    window.adToBsString = adToBs;
    window.bsToAdString = bsToAd;

    /**************************************************
     * Datepicker Binding
     **************************************************/
    const bsFields = "#dob_bs, #citizen_bs, #nominee_dob_bs";

    $(bsFields).each(function () {
        const input = this;

        $(input).nepaliDatePicker({
            ndpYear: true,
            ndpMonth: true,
            ndpYearCount: 120,

            onSelect: function (bsObj) {
                const id = input.id;
                const ad = bsToAd(bsObj.value);

                if (id === "dob_bs") $("#dob_ad").val(ad);
                if (id === "citizen_bs") $("#citizen_ad").val(ad);
                if (id === "nominee_dob_bs") $("#nominee_dob_ad").val(ad);
            },

            onChange: function () {
                const id = input.id;
                const ad = bsToAd(input.value);

                if (id === "dob_bs") $("#dob_ad").val(ad);
                if (id === "citizen_bs") $("#citizen_ad").val(ad);
                if (id === "nominee_dob_bs") $("#nominee_dob_ad").val(ad);
            }
        });
    });

    /**************************************************
     * BIND BS-AD SYNC WITH VALIDATION
     **************************************************/
    function bindBsAdSync(bsSelector, adSelector) {
        const today = new Date();
        
        // BS input changes → update AD
        $(bsSelector).on('input change blur', function () {
            const ad = bsToAd($(this).val());
            if (!ad) return;
            
            const adDate = new Date(ad);
            if (adDate <= today) {
                $(adSelector).val(ad);
                $(adSelector).removeClass('is-invalid');
            } else {
                swalFire("Wrong Date", "Future Date Selected");
                $(bsSelector + ', ' + adSelector).val('');
            }
        });
        
        // AD input changes → update BS
        $(adSelector).on('input change blur', function () {
            const ad = $(this).val();
            if (!ad) return;
            
            const adDate = new Date(ad);
            const bs = adToBs(ad);
            
            if (adDate <= today) {
                $(bsSelector).val(bs);
                $(bsSelector).removeClass('is-invalid');
            } else {
                swalFire("Wrong Date", "Future Date Selected");
                $(bsSelector + ', ' + adSelector).val('');
            }
        });
    }

    // Apply binding to all date field pairs
    bindBsAdSync('#dob_bs', '#dob_ad');
    bindBsAdSync('#user_dob_bs', '#user_dob_ad');
    bindBsAdSync('#citizen_bs', '#citizen_ad');
    bindBsAdSync('#nominee_dob_bs', '#nominee_dob_ad');

    /**************************************************
     * READY EVENT DISPATCH
     **************************************************/
    setTimeout(() => {
        document.dispatchEvent(new Event("NepaliDatepickerReady"));
        console.log("✅ NepaliDatepickerReady dispatched");
    }, 150);

    /**************************************************
     * PREFILL LISTENER WITH BIND LOGIC
     **************************************************/
    document.addEventListener("NepaliDatepickerReady", () => {
        console.log("📅 NepaliDatepickerReady received - applying prefill");

        if (!window.prefill_data) {
            console.log("No prefill_data available");
            return;
        }

        const data = window.prefill_data;

        // Prefill AD dates first, then trigger change to sync BS
        // The bindBsAdSync handlers will automatically convert AD→BS
        
        if (data.dob_ad) {
            $("#dob_ad").val(data.dob_ad).trigger('change');
        }

        if (data.citizen_ad) {
            $("#citizen_ad").val(data.citizen_ad).trigger('change');
        }

        if (data.nominee_dob_ad) {
            $("#nominee_dob_ad").val(data.nominee_dob_ad).trigger('change');
        }

        // Fallback: if BS dates exist in prefill but AD doesn't
        if (data.dob_bs && !data.dob_ad) {
            $("#dob_bs").val(data.dob_bs).trigger('change');
        }

        if (data.citizen_bs && !data.citizen_ad) {
            $("#citizen_bs").val(data.citizen_bs).trigger('change');
        }

        if (data.nominee_dob_bs && !data.nominee_dob_ad) {
            $("#nominee_dob_bs").val(data.nominee_dob_bs).trigger('change');
        }

    });

    console.log("✅ Date conversion script loaded");
});
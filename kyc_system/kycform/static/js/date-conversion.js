/**************************************************
 * FINAL DATE CONVERSION SCRIPT (Stable Version)
 **************************************************/

console.log("date-conversion.js loaded");

$(document).ready(function () {

    console.log("date-conversion.js initialized");

    /**************************************************
     * Nepali Digits → Latin Digits
     **************************************************/
    function nepaliToLatin(str) {
        if (!str) return "";
        return str.replace(/[०-९]/g, d => String.fromCharCode(d.charCodeAt(0) - 2406));
    }

    /**************************************************
     * Normalize BS String (fallback for manual input)
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

        const parts = s.split("-");
        if (parts.length === 3) {
            return `${parts[0]}-${parts[1].padStart(2, "0")}-${parts[2].padStart(2, "0")}`;
        }

        return "";
    }

    /**************************************************
     * BS → AD (Supports object + string inputs)
     **************************************************/
    function bsToAd(bsInput) {
        try {

            // Case 1: BS object from datepicker {value, year, month, day}
            if (typeof bsInput === "object" && bsInput.year) {
                const ad = NepaliFunctions.BS2AD({
                    year: Number(bsInput.year),
                    month: Number(bsInput.month),
                    day: Number(bsInput.day)
                });

                return `${ad.year}-${String(ad.month).padStart(2, "0")}-${String(ad.day).padStart(2, "0")}`;
            }

            // Case 2: plain string
            const normalized = normalizeBS(bsInput);
            if (!normalized) return "";

            const [y, m, d] = normalized.split("-").map(Number);
            const ad = NepaliFunctions.BS2AD({ year: y, month: m, day: d });

            return `${ad.year}-${String(ad.month).padStart(2, "0")}-${String(ad.day).padStart(2, "0")}`;

        } catch (e) {
            console.error("BS → AD conversion error:", e);
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
            console.error("AD → BS conversion error:", e);
            return "";
        }
    }

    /**************************************************
     * BS Input Fields
     **************************************************/
    const bsFields = "#dob_bs, #citizen_bs, #nominee_dob_bs";
    console.log("Nepali datepicker initialized on:", bsFields);

   /**************************************************
 * FIXED NEPALI DATE PICKER BINDING (V5.0.6 BUG FIX)
 **************************************************/
$(bsFields).each(function () {

    const input = this;   // Capture real input element

    $(input).nepaliDatePicker({

        ndpYear: true,
        ndpMonth: true,
        ndpYearCount: 120,

        onSelect: function (bsObj) {

            const fieldId = input.id;         // FIX: use captured element
            const bsValue = bsObj.value;

            console.log("onSelect fired:", fieldId, bsObj);

            const ad = bsToAd(bsObj.value);   // Always use string

            if (fieldId === "dob_bs") $("#dob_ad").val(ad);
            if (fieldId === "citizen_bs") $("#citizen_ad").val(ad);
            if (fieldId === "nominee_dob_bs") $("#nominee_dob_ad").val(ad);
        },

        onChange: function () {

            const fieldId = input.id;         // FIX: use captured element
            const bsValue = input.value;

            console.log("onChange fired:", fieldId, bsValue);

            const ad = bsToAd(bsValue);

            if (fieldId === "dob_bs") $("#dob_ad").val(ad);
            if (fieldId === "citizen_bs") $("#citizen_ad").val(ad);
            if (fieldId === "nominee_dob_bs") $("#nominee_dob_ad").val(ad);
        }
    });

});

    /**************************************************
     * AD → BS Sync
     **************************************************/
    $("#dob_ad, #citizen_ad, #nominee_dob_ad").on("change", function () {

        const id = this.id;
        const adValue = $(this).val();
        const bs = adToBs(adValue);

        console.log("AD selected:", id, adValue, "→ BS:", bs);

        if (id === "dob_ad") $("#dob_bs").val(bs);
        else if (id === "citizen_ad") $("#citizen_bs").val(bs);
        else if (id === "nominee_dob_ad") $("#nominee_dob_bs").val(bs);
    });

});

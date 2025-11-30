/**************************************************
 * FINAL DATE CONVERSION SCRIPT (Corrected)
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
     * AD → BS Sync
     **************************************************/
    $("#dob_ad, #citizen_ad, #nominee_dob_ad").on("change", function () {
        const id = this.id;
        const bs = adToBs($(this).val());

        if (id === "dob_ad") $("#dob_bs").val(bs);
        if (id === "citizen_ad") $("#citizen_bs").val(bs);
        if (id === "nominee_dob_ad") $("#nominee_dob_bs").val(bs);
    });

    /**************************************************
     * READY EVENT
     **************************************************/
    console.log("Dispatching NepaliDatepickerReady...");
    document.dispatchEvent(new Event("NepaliDatepickerReady"));

    /**************************************************
 * PREFILL LISTENER
 **************************************************/
document.addEventListener("NepaliDatepickerReady", () => {
    console.log("NepaliDatepickerReady received in prefill block");

    if (!window.prefill_data) return;

    if (window.prefill_data.dob_ad)
        $("#dob_bs").val(adToBs(window.prefill_data.dob_ad));

    if (window.prefill_data.citizen_ad)
        $("#citizen_bs").val(adToBs(window.prefill_data.citizen_ad));

    if (window.prefill_data.nominee_dob_ad)
        $("#nominee_dob_bs").val(adToBs(window.prefill_data.nominee_dob_ad));
});

console.log("Dispatching NepaliDatepickerReady…");
document.dispatchEvent(new Event("NepaliDatepickerReady"));

});



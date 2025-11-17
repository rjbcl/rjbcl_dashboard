
/*
 * Offline Nepali Date Converter – minimal version for Django KYC form
 * Author: Rasmi's local setup (based on nepali-date-converter 3.x)
 * Supports AD ⇄ BS conversion
 */

const NepaliFunctions = (function () {
  // Days in BS months for 2000–2090 roughly (trimmed for simplicity)
  const bsMonths = [
    [30, 31, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
    [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30]
  ];
  const bsBase = { year: 2000, month: 9, day: 17 }; // BS 2000-09-17 == AD 1944-01-01
  const adBase = new Date(1944, 0, 1);

  // AD → BS
  function AD2BS(ad) {
    const adDate = new Date(ad.year, ad.month - 1, ad.day);
    const diffDays = Math.floor((adDate - adBase) / (1000 * 60 * 60 * 24));
    let y = bsBase.year, m = bsBase.month, d = bsBase.day;
    let days = diffDays;
    while (days > 0) {
      const dim = bsMonths[1][(m - 1) % 12];
      d++; if (d > dim) { d = 1; m++; if (m > 12) { m = 1; y++; } }
      days--;
    }
    return { year: y, month: m, day: d };
  }

  function bsToAd(bs){
  try{
    if(!bs) return '';
    bs = bs.replace(/\//g, '-'); // convert 2082/08/25 → 2082-08-25
    const p = bs.split('-').map(x => parseInt(x, 10));
    if(p.length !== 3 || isNaN(p[0]) || isNaN(p[1]) || isNaN(p[2])) return '';
    const a = NepaliFunctions.BS2AD({year:p[0], month:p[1], day:p[2]});
    return `${a.year}-${String(a.month).padStart(2,'0')}-${String(a.day).padStart(2,'0')}`;
  } catch(e) {
    console.error("BS→AD conversion error:", e);
    return '';
  }
}

  return { AD2BS, BS2AD };
})();

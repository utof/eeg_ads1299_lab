/* Offline learning calculator, not a board-power or patient-safety check. */
function headroom(gain, offsetMv, commonV) {
  if (![1, 2, 4, 6, 8, 12, 24].includes(gain) ||
      !Number.isFinite(offsetMv) || !Number.isFinite(commonV)) {
    throw new Error('Invalid educational calculator input');
  }
  const diff = offsetMv / 1000;
  const fullScale = 4.5 / gain;
  const lower = 0.2 + gain * Math.abs(diff) / 2;
  const upper = 4.8 - gain * Math.abs(diff) / 2;
  return {
    fullScaleMv: fullScale * 1000,
    lsbUv: 4.5 / (gain * 8388608) * 1000000,
    lower, upper,
    differentialOK: Math.abs(diff) < fullScale,
    commonOK: commonV > lower && commonV < upper,
    valid: Math.abs(diff) < fullScale && commonV > lower && commonV < upper
  };
}
if (typeof module !== 'undefined') module.exports = {headroom};
if (typeof document !== 'undefined') {
  function update() {
    const gain = Number(document.getElementById('gain').value);
    const offset = Number(document.getElementById('offset').value);
    const common = Number(document.getElementById('common').value);
    const h = headroom(gain, offset, common);
    document.getElementById('offsetValue').textContent = offset + ' mV';
    document.getElementById('commonValue').textContent = common.toFixed(2) + ' V';
    document.getElementById('rangeResult').textContent = '±' + h.fullScaleMv.toFixed(2) + ' mV';
    document.getElementById('stepResult').textContent = h.lsbUv.toFixed(5) + ' µV / code';
    document.getElementById('cmResult').textContent = h.lower.toFixed(3) + ' < Vcm < ' + h.upper.toFixed(3) + ' V';
    const status = document.getElementById('rangeStatus');
    status.textContent = h.valid ? 'Within this simplified operating-range example. This is NOT a safety check.' :
      'Outside the modeled operating range. Filtering after capture cannot restore clipped information.';
    status.className = h.valid ? 'callout info' : 'callout warning';
    document.getElementById('whyResult').textContent = 'Differential range: ' + (h.differentialOK ? 'within limit' : 'EXCEEDED') +
      ' · Common-mode range: ' + (h.commonOK ? 'within limit' : 'EXCEEDED');
  }
  document.addEventListener('DOMContentLoaded', () => {
    for (const id of ['gain','offset','common']) document.getElementById(id).addEventListener('input', update);
    update();
    for (const button of document.querySelectorAll('[data-lesson]')) {
      button.addEventListener('click', () => {
        for (const b of document.querySelectorAll('[data-lesson]')) b.setAttribute('aria-pressed','false');
        button.setAttribute('aria-pressed','true');
        for (const panel of document.querySelectorAll('.lesson')) panel.hidden = panel.id !== button.dataset.lesson;
      });
    }
  });
}

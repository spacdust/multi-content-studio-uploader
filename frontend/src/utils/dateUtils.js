// Local Date & Time Utility Functions (24-Hour Format)

export function getLocalTodayDate() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function getLocalNowIso() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const mins = String(d.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${mins}:00`;
}

export function formatDateDisplay(isoString) {
  if (!isoString) return '-';
  try {
    const [datePart] = isoString.split('T');
    const [year, month, day] = datePart.split('-');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
    return `${parseInt(day, 10)} ${months[parseInt(month, 10) - 1]} ${year}`;
  } catch {
    return isoString;
  }
}

export function formatTimeDisplay(isoString) {
  if (!isoString) return '-';
  try {
    const timePart = isoString.split('T')[1] || '';
    const [hours, mins] = timePart.split(':');
    return `${hours || '00'}:${mins || '00'}`;
  } catch {
    return isoString;
  }
}

export function formatScheduleIsoForHuman(isoString) {
  if (!isoString) return null;
  try {
    const dateDisplay = formatDateDisplay(isoString);
    const timeDisplay = formatTimeDisplay(isoString);
    return `${dateDisplay} pukul ${timeDisplay} WIB`;
  } catch {
    return isoString;
  }
}

export function toLocalDatetimeLocalValue(isoString) {
  if (!isoString) return '';
  return isoString.slice(0, 16);
}

export function parseLocalDatetimeLocalValue(datetimeLocalVal) {
  if (!datetimeLocalVal) return '';
  return `${datetimeLocalVal}:00`;
}

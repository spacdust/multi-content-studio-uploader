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

export function addMinutesToIso(isoString, minutes) {
  if (!isoString) return '';
  try {
    const [dPart, tPart] = isoString.split('T');
    const [year, month, day] = dPart.split('-').map(Number);
    const [hours, mins] = (tPart || '00:00').split(':').map(Number);
    const date = new Date(year, month - 1, day, hours, mins + (Number(minutes) || 0), 0);
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    const h = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${d}T${h}:${min}:00`;
  } catch {
    return isoString;
  }
}

export function formatScheduleShort(isoString) {
  if (!isoString) return '-';
  try {
    const today = getLocalTodayDate();
    const [datePart, timePart] = isoString.split('T');
    const [hours, mins] = (timePart || '00:00').split(':');
    const timeStr = `${hours}:${mins} WIB`;
    if (datePart === today) {
      return `Hari Ini, ${timeStr}`;
    }
    
    const d = new Date();
    d.setDate(d.getDate() + 1);
    const tomorrowStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    if (datePart === tomorrowStr) {
      return `Besok, ${timeStr}`;
    }

    const [year, month, day] = datePart.split('-');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
    return `${parseInt(day, 10)} ${months[parseInt(month, 10) - 1]}, ${timeStr}`;
  } catch {
    return isoString;
  }
}

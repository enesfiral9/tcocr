export async function scanDocument(file) {
  const body = new FormData(); body.append('file', file);
  const response = await fetch('/api/scan', { method: 'POST', body });
  if (!response.ok) throw new Error((await response.json()).detail || 'Tarama başarısız.');
  return response.json();
}
export async function checkHealth() { return (await fetch('/api/health')).json(); }
export async function exportExcel(records) {
  const response = await fetch('/api/export', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({records})});
  if (!response.ok) throw new Error('Excel oluşturulamadı.');
  const blob = await response.blob(); const disposition = response.headers.get('content-disposition') || '';
  const filename = disposition.match(/filename="([^"]+)"/)?.[1] || 'kimlik_ocr.xlsx';
  const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href=url; link.download=filename; link.click(); URL.revokeObjectURL(url);
}

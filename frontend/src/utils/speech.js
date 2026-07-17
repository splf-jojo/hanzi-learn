export function speakChinese(term) {
  if (!term || !window.speechSynthesis) {
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(term);
  utterance.lang = 'zh-CN';
  utterance.rate = 0.82;
  window.speechSynthesis.speak(utterance);
}

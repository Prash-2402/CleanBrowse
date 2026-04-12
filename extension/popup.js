const { SAFETY_MODES, DEFAULT_MODE_ID } = globalThis.CLEAN_BROWSE_CONFIG;
const extAPI = globalThis.extAPI;

const modeList = document.getElementById('modeList');

function renderModes(activeModeId) {
  modeList.innerHTML = '';
  
  Object.values(SAFETY_MODES).forEach(mode => {
    const card = document.createElement('div');
    card.className = `mode-card ${mode.id === activeModeId ? 'active' : ''}`;
    card.dataset.id = mode.id;

    card.innerHTML = `
      <div class="mode-header">
        <span class="mode-name">${mode.label}</span>
        <span class="active-badge">Active</span>
      </div>
      <div class="mode-desc">${mode.description}</div>
    `;

    card.addEventListener('click', () => {
      saveMode(mode.id);
    });

    modeList.appendChild(card);
  });
}

function saveMode(modeId) {
  extAPI.storage.local.set({ activeModeId: modeId }, () => {
    renderModes(modeId);
  });
}

// Initialize the UI
extAPI.storage.local.get('activeModeId', (data) => {
  const currentModeId = data.activeModeId || DEFAULT_MODE_ID;
  renderModes(currentModeId);
});

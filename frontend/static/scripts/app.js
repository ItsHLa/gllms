const { createApp, ref, computed, onMounted } = Vue;

/**
 * Parse the raw stdout into structured metrics.
 * Returns { metrics, rawOutput }
 */
function parseMetrics(raw) {
  if (!raw) return { metrics: {}, rawOutput: '' };

  const metrics = {};

  // Execution mode
  const modeMatch = raw.match(/===\s*EXECUTION MODE:\s*(\w+)\s*===/);
  metrics.mode = modeMatch ? modeMatch[1] : '';

  // Injection detected
  metrics.injectionDetected = /DIRECT PROMPT INJECTION DETECTED/.test(raw) ? 'Yes' : 'No';

  // Attack type
  const attackTypeMatch = raw.match(/Attack Type:\s*(.+)/);
  metrics.attackType = attackTypeMatch ? attackTypeMatch[1].trim() : '';

  // Source
  const sourceMatch = raw.match(/Source:\s*(.+)/);
  metrics.source = sourceMatch ? sourceMatch[1].trim() : '';

  // Risk
  const riskMatch = raw.match(/Risk:\s*(.+)/);
  metrics.risk = riskMatch ? riskMatch[1].trim() : '';

  // LLM Followed Injection
  const llmFollowedMatch = raw.match(/LLM Followed Injection:\s*(YES|NO)/i);
  metrics.llmFollowed = llmFollowedMatch ? llmFollowedMatch[1] : '';

  // System Prompt Disclosed
  const disclosedMatch = raw.match(/System Prompt Disclosed:\s*(YES|NO)/i);
  metrics.systemDisclosed = disclosedMatch ? disclosedMatch[1] : '';

  // Final Result
  const resultMatch = raw.match(/Final Result:\s*(.+)/);
  metrics.resultStatus = resultMatch ? resultMatch[1].trim() : '';

  // Retrieved docs count
  const docsSection = raw.match(/RETRIEVED DOCUMENTS\n-{10,}\n([\s\S]*?)(?=\n[A-Z])/);
  metrics.retrievedDocs = docsSection
    ? docsSection[1].split('\n').filter(l => l.trim().startsWith('-')).length
    : 0;

  return { metrics, rawOutput: raw };
}

/**
 * Lightweight syntax-highlighter for terminal output.
 */
function highlightOutput(raw) {
  if (!raw) return '';
  let text = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const lines = text.split('\n');
  const out = [];

  for (const line of lines) {
    const trimmed = line.trimStart();

    // Section headers
    if (/^={3,}\s/.test(trimmed) && trimmed.endsWith('===')) {
      out.push('<span class="tok-header">' + line + '</span>');
      continue;
    }

    // Separator lines
    if (/^-{4,}$/.test(trimmed)) {
      out.push('<span class="tok-separator">' + line + '</span>');
      continue;
    }

    // PASS
    if (/\bPASS\b/.test(line) && !/\bFAIL\b/.test(line)) {
      out.push(line.replace(/\bPASS\b/g, '<span class="tok-success">PASS</span>'));
      continue;
    }
    // FAIL
    if (/\bFAIL\b/.test(line)) {
      out.push(line.replace(/\bFAIL\b/g, '<span class="tok-fail">FAIL</span>'));
      continue;
    }

    // Boolean values
    if (/\bTrue\b/.test(line)) {
      out.push(line.replace(/\bTrue\b/g, '<span class="tok-value-true">True</span>'));
      continue;
    }
    if (/\bFalse\b/.test(line)) {
      out.push(line.replace(/\bFalse\b/g, '<span class="tok-value-false">False</span>'));
      continue;
    }

    // Pass through
    out.push(line);
  }

  return out.join('\n');
}

const app = createApp({
  setup() {
    const scenarios = ref([]);
    const scenario = ref(null);
    const selectedId = ref(null);
    const result = ref(null);
    const errorMessage = ref("");
    const running = ref(false);
    const loading = ref(true);
    const activeTab = ref("describe");
    const selectedMode = ref("protected");

    // Parsed output
    const parsed = computed(() => {
      if (!result.value?.stdout) return { metrics: {}, rawOutput: '' };
      return parseMetrics(result.value.stdout);
    });

    const renderedArticle = computed(() =>
      marked.parse(scenario.value?.article || "")
    );

    function isBusy() {
      return running.value;
    }

    async function loadScenarios() {
      try {
        scenarios.value = await Api.listScenarios();
        const saved = localStorage.getItem("gllms:scenario") || null;
        const target = saved && scenarios.value.some((s) => s.id === saved)
          ? saved
          : scenarios.value[0]?.id;
        if (target) await selectScenario(target);
      } catch (err) {
        errorMessage.value = err.message;
      } finally {
        loading.value = false;
      }
    }

    async function selectScenario(id) {
      if (isBusy()) return;
      selectedId.value = id;
      activeTab.value = "describe";
      try {
        const detail = await Api.getScenario(id);
        scenario.value = detail;
        selectedMode.value = detail.modes[0];
        result.value = null;
        errorMessage.value = "";
        localStorage.setItem("gllms:scenario", id);
      } catch (err) {
        errorMessage.value = err.message;
      }
    }

    async function run() {
      if (!scenario.value || running.value) return;
      running.value = true;
      result.value = null;
      errorMessage.value = "";
      try {
        result.value = await Api.runScenario(scenario.value.id, { mode: selectedMode.value });
      } catch (err) {
        errorMessage.value = err.message;
      } finally {
        running.value = false;
      }
    }

    async function copyPrompt() {
      if (!scenario.value) return;
      try {
        await navigator.clipboard.writeText(scenario.value.attacker_prompt);
      } catch (err) {
        errorMessage.value = err.message;
      }
    }

    onMounted(loadScenarios);

    return {
      scenarios,
      scenario,
      selectedId,
      result,
      errorMessage,
      running,
      loading,
      activeTab,
      selectedMode,
      parsed,
      renderedArticle,
      selectScenario,
      run,
      copyPrompt,
      highlightOutput,
    };
  },
});

app.mount("#app");

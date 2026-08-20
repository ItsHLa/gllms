const { createApp, ref, computed, onMounted } = Vue;

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
      renderedArticle,
      selectScenario,
      run,
      copyPrompt,
    };
  },
});

app.mount("#app");

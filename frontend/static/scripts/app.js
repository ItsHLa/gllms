const { createApp, ref, computed, watch, onMounted } = Vue;

const app = createApp({
  setup() {
    const scenarios = ref([]);
    const scenario = ref(null);
    const selectedId = ref(null);
    const code = ref("");
    const result = ref(null);
    const errorMessage = ref("");
    const running = ref(false);
    const loading = ref(true);
    const activeTab = ref("describe");

    const renderedArticle = computed(() =>
      marked.parse(scenario.value?.article || "")
    );

    const codeLines = computed(() => code.value.split("\n"));

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
        code.value = detail.code;
        result.value = null;
        errorMessage.value = "";
        localStorage.setItem("gllms:scenario", id);
      } catch (err) {
        errorMessage.value = err.message;
      }
    }

    function resetCode() {
      if (scenario.value) code.value = scenario.value.code;
      result.value = null;
      errorMessage.value = "";
    }

    async function run() {
      if (!scenario.value || running.value) return;
      running.value = true;
      result.value = null;
      errorMessage.value = "";
      try {
        result.value = await Api.runScenario(scenario.value.id, code.value);
      } catch (err) {
        errorMessage.value = err.message;
      } finally {
        running.value = false;
      }
    }

    watch(code, () => {
      if (result.value) result.value = null;
    });

    onMounted(loadScenarios);

    return {
      scenarios,
      scenario,
      selectedId,
      code,
      result,
      errorMessage,
      running,
      loading,
      activeTab,
      renderedArticle,
      codeLines,
      selectScenario,
      resetCode,
      run,
    };
  },
});

app.mount("#app");

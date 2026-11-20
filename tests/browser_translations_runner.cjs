// Portal regression against a local API with synthetic data and inference.
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const { spawn } = require('node:child_process');
const { once } = require('node:events');

const root = path.resolve(__dirname, '..');
// BROWSER_FIXTURE_URL lets a remote browser reach the fixture API (for example
// http://10.0.3.2:8769 from a Playwright server in a container).
const fixtureURL = process.env.BROWSER_FIXTURE_URL || 'http://127.0.0.1:8769';
const artifactRoot = path.resolve(process.env.BROWSER_ARTIFACTS || '/tmp/setupsurvie-browser-results');
const playwright = createRequire(process.env.BROWSER_PLAYWRIGHT || '/tmp/setupsurvie-browser/package.json')('playwright');

const portalRecipes = [
  'browser_video_origin.js',
  'browser_translation.js',
  'browser_sources.js',
  'browser_learning.js',
  'browser_documents.js',
  'browser_translation_quality.js',
  'browser_profiles.js',
  'browser_collection_filter.js',
  'browser_chat_comfort.js',
  'browser_search_core.js',
  'browser_search_progress.js',
  'browser_search_tools.js',
  'browser_catalogue.js',
  'browser_assistant_diagnostics.js',
  'browser_startup_diagnostic.js',
  'browser_request_lifecycle.js',
  'browser_performance.js',
  'browser_local_videos.js',
  'browser_archive_videos.js',
  'browser_archive_audio.js',
  'browser_caption_preparation.js',
  'browser_audio_transcription.js',
  'browser_caption_acquisition.js',
  'browser_translation_benchmark.js',
  'browser_translation_progressive.js',
  'browser_translation_controls.js',
  'browser_translation_terms.js',
  'browser_search_experiment.js',
  'browser_practical.js',
  'browser_usage_recipe.js',
  'browser_settings_ux.js',
  'browser_documentary_evidence.js',
  'browser_model_switch.js',
  'browser_document_choices.js',
  'browser_long_summaries.js',
  'browser_french_lifecycle.js',
  'browser_figure_lifecycle.js',
  'browser_figure_worker_start.js',
  'browser_source_figures.js',
  'browser_procedure_review.js',
  'browser_bilingual_reader.js',
  'browser_next_portal.js',
  'browser_work_queue.js',
  'browser_memory_translation_comfort.js',
  'browser_motion_resilience.js',
  'browser_motion_and_drag.js',
  'browser_ux_foundations.js',
  'browser_assistant_workspace.js',
  'browser_reader_work.js',
  'browser_ui_finish.js',
  'browser_map_fallback.js',
];
const firefoxRecipes = [
  'browser_translation_progressive.js',
  'browser_motion_resilience.js',
  'browser_motion_and_drag.js',
  'browser_ui_finish.js',
  'browser_assistant_workspace.js',
  'browser_chat_comfort.js',
  'browser_reader_work.js',
  'browser_settings_ux.js',
  'browser_map_fallback.js',
];

async function waitForFixture(server) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (server.exitCode !== null || server.signalCode !== null) {
      throw Error('Portal fixture server exited');
    }
    try {
      if ((await fetch(fixtureURL + '/api/health', { signal: AbortSignal.timeout(500) })).ok) return;
    } catch {
      // The fixture is still starting.
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw Error('Portal fixture API is unavailable');
}

async function runRecipe(browser, engine, file) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const directory = path.join(artifactRoot, engine, path.basename(file, '.js'));
  fs.mkdirSync(directory, { recursive: true });
  const started = Date.now();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const label = '[' + engine + '] ' + file;
  console.log('START ' + label);
  try {
    const source = fs.readFileSync(path.join(__dirname, file), 'utf8')
      .replaceAll(/http:\/\/10\.0\.3\.2:87(?:69|72)/g, fixtureURL)
      .replaceAll('/artifacts/', directory + '/');
    // Existing recipes are function expressions shared with the manual harness.
    const recipe = eval('(' + source + '\n)\n//# sourceURL=' + file);
    const result = await recipe(page);
    if (errors.length) throw Error(errors.join('\n'));
    console.log(JSON.stringify({ engine, recipe: file, status: 'passed', ms: Date.now() - started, ...result }));
    return true;
  } catch (error) {
    console.error('FAIL ' + label + ' after ' + (Date.now() - started) + ' ms', error);
    try {
      await page.screenshot({ path: path.join(directory, 'failure.png'), timeout: 5000 });
    } catch (screenshotError) {
      console.error('Could not capture ' + label + ': ' + screenshotError.message);
    }
    return false;
  } finally {
    await page.unrouteAll({ behavior: 'ignoreErrors' });
    await context.close();
  }
}

async function main() {
  const engines = ['chromium', 'webkit', 'firefox'];
  const targetEngine = process.env.BROWSER_ENGINE;
  if (targetEngine && !engines.includes(targetEngine)) throw Error('Invalid BROWSER_ENGINE: ' + targetEngine);
  const requested = process.argv.slice(2);
  const unknown = requested.filter(file => !portalRecipes.includes(file) && !firefoxRecipes.includes(file));
  if (unknown.length) throw Error('Unknown portal recipe: ' + unknown.join(', '));
  const server = spawn(process.env.BROWSER_PYTHON || 'python', ['tests/browser_translation_server.py'], {
    cwd: root,
    stdio: ['ignore', 'ignore', 'inherit'],
  });
  const exited = once(server, 'exit');
  const failures = [];
  try {
    await Promise.race([waitForFixture(server), exited.then(() => { throw Error('Portal fixture server exited'); })]);
    for (const engine of targetEngine ? [targetEngine] : engines) {
      const files = requested.length ? requested : engine === 'firefox' ? firefoxRecipes : portalRecipes;
      // BROWSER_WS connects to an existing Playwright server instead of launching
      // a local browser (runner without the system libraries of the browsers).
      const browser = process.env.BROWSER_WS
        ? await playwright[engine].connect(process.env.BROWSER_WS, { headers: { 'x-playwright-launch-options': JSON.stringify(engine === 'chromium' ? { channel: 'chromium' } : {}) } })
        : await playwright[engine].launch({ headless: true });
      try {
        for (const file of files) {
          if (!await runRecipe(browser, engine, file)) failures.push(engine + '/' + file);
        }
      } finally {
        await browser.close();
      }
    }
  } finally {
    server.kill();
    await exited;
  }
  if (failures.length) throw Error('Failed portal recipes: ' + failures.join(', '));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

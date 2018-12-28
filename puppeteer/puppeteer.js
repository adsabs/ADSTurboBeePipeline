const puppeteer = require("puppeteer");
const {TimeoutError} = require('puppeteer/Errors');

const runner = {

  browser: null,
  page: null,

  init: async options => {
    console.log("Opening browser");
    runner.browser = await puppeteer.launch({
      headless: false,
      args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    runner.page = await runner.browser.newPage();
    runner.options = options || {};
  },

  cleanup: async () => {
    try {
      console.log("Cleaning up instances");
      if (runner.browser !== null) {
        await runner.page.close();
        await runner.browser.close();
        runner.page = null;
        runner.browser = null;
      }
    } catch (e) {
      console.log("Cannot cleanup istances", e);
    }
  },

  scrape: async url => {
    let data = '';
    
    // with this wrapper you can await for specific timeStamp
    function getMetric(page, name) {
        return new Promise((resolve, reject) => page.on('metrics', ({ title }) => {
            if (name === title) {
                resolve();
            }
        }));
    }
    
    if (runner.browser === null) {
      await runner.init();
      const detectChange = 'window.addEventListener("page-rendered", () => console.timeStamp("page-rendered"));';
      await runner.page.addScriptTag({ content: detectChange });
    }

    const page = runner.page;
    const pageChange = getMetric(page, 'page-rendered');
    
    try {
      console.log("Navigating to url: " + url);
      await page.goto(url, { waitUntil: ['load', "networkidle0", 'domcontentloaded']});
      //await pageChange; // wait for page-rendered metric event
      await page.waitFor(1000);
      data = await page.evaluate(() =>
           window.__PREPARE_STATIC_PAGE__()
         );

    } catch (e) {
      console.log("Error happened", e);
      if (e instanceof TimeoutError) {
        throw e;
      }
      else if (e.message.indexOf('invalid URL') > -1) {
        throw e;
      }
      await page.screenshot({ path: "error.png" });
      await cleanup();
      throw e;
    }
    return data;
  }
};

module.exports = runner;

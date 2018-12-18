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

    if (runner.browser === null)
      await runner.init();

    const page = runner.page;
    
    try {
      console.log("Navigating to url: " + url);
      await page.goto(url, { waitUntil: ['load', "networkidle0", 'domcontentloaded']});
      await page.waitFor(runner.options['pageWait'] || 1000);
      //await page.waitFor(url => !!document.location.href === url);

      data = await page.evaluate(() =>
          document.documentElement.outerHTML
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

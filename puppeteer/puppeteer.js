const puppeteer = require("puppeteer");
const {TimeoutError} = require('puppeteer/Errors');
const fs = require('fs');

const runner = {

  browser: null,
  page: null,

  init: async options => {
    console.log("Opening browser");
    runner.browser = await puppeteer.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-dev-shm-usage']
    });
    runner.page = await runner.browser.newPage();
    runner.options = options || {};
    //await runner.page.evaluate(fs.readFileSync('./require.min.js', 'utf8'));
    //await runner.page.evaluate(fs.readFileSync('./persist.js', 'utf8'));
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
    // we must instruct browser to call console.timeStamp('page-rendered')
    // currently bbb doesn't have a good place for it
    function getMetric(page, name) {
        return new Promise((resolve, reject) => page.once('metrics', ({ title }) => {
            if (name === title) {
                resolve();
            }
        }));
    }
    
    if (runner.browser === null) {
      await runner.init();
    }

    const page = runner.page;
    
    try {
      console.log("Navigating to url: " + url);
      //const pageChange = getMetric(page, 'page-rendered');
      await page.goto(url, { waitUntil: ['load', "networkidle0", 'domcontentloaded']});
      
      // include our own way of persisting a bbb page
      await runner.page.evaluate(fs.readFileSync('./persist.js', 'utf8'));
      

      //await pageChange; // wait for page-rendered metric event
      await page.waitFor(100);
      data = await page.evaluate(() =>
           window.__PERSIST()
         );

      if (data && data.length < 20000) {
        // force page reload on next scrape
        await page.goto('http://www.google.com', { waitUntil: ['load', "networkidle0", 'domcontentloaded']});
        throw Error('Page too small: ' + data.length);
      }

    } catch (e) {
      console.log("Error happened", e);
      if (e instanceof TimeoutError) {
        throw e;
      }
      else if (e.message.indexOf('invalid URL') > -1) {
        throw e;
      }
      await page.screenshot({ path: "error.png" });
      await runner.cleanup();
      throw e;
    }
    return data;
  }
};

module.exports = runner;

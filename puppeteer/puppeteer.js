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
    await runner.pageReset();
    
    //await runner.page.evaluate(fs.readFileSync('./require.min.js', 'utf8'));
    //await runner.page.evaluate(fs.readFileSync('./persist.js', 'utf8'));
  },

  pageReset: async() => {
    if (runner.page !== null)
      await runner.page.close();
    runner.page = await runner.browser.newPage();
    runner.page.on('error', err=> {
      console.log('error happen at the page: ', err.toString());
    });

    runner.page.on('pageerror', pageerr=> {
      console.log('pageerror occurred: ', pageerr.toString());
    })

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
    
    var waitMore = false;
    if (runner.browser === null) {
      await runner.init();
      waitMore = true;
    }

    const page = runner.page;
    
    try {
      console.log("Navigating to url: " + url);
      //const pageChange = getMetric(page, 'page-rendered');
      await page.goto(url, { waitUntil: ['load', "networkidle2", 'domcontentloaded']});
      
      // include our own way of persisting a bbb page
      await runner.page.evaluate(fs.readFileSync('./persist.js', 'utf8'));
      

      //await pageChange; // wait for page-rendered metric event
      if (waitMore) {
        await page.waitFor(3000);
      }
      else {
        await page.waitFor(500);
      }
      data = await page.evaluate(() =>
           window.__PERSIST()
         );

      if (data && data.length < 15000) {
        throw Error('Page too small: ' + data.length);
      }

    } catch (e) {
      console.log("Error happened", e);
      if (e instanceof TimeoutError) {
        await runner.pageReset();
        throw e;
      }
      else if (e.message.indexOf('invalid URL') > -1) {
        throw e;
      }
      else if (e.message.indexOf('too small') > -1) {
        runner.pageReset();
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

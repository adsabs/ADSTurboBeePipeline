const express = require("express");
const app = express();
const bodyParser = require("body-parser");
const runner = require("./puppeteer");
const port = process.env.PORT || 3000;
const maxReqsPerSession = process.env.MAX_REQS || 100;
var counter = 0;
var errCounter = 0;
var pageCounter = 0;
var maxErr = 3;
var maxPagePerSession = 10;

var sys = require('sys')
var exec = require('child_process').exec;

runner.init();
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies
app.get("/", (req, res) => res.send("Hello World!"));
app.get("/restart", async (req, res) => {
  try {
    await runner.cleanup();
    return res.json( {message: "Restarted browser"} );
  } catch (error) {
    return res.json( {message: error})
  }
});
app.post("/scrape", async (req, res) => {
  
  //console.log(req.body, req.body.length);
  const data = {};
  for (var idx in req.body) {
    var url = req.body[idx];
    console.log(url)
    try {
      data[url] = await runner.scrape(url);
      console.log('Harvested # chars', data[url].length);
      errCounter = 0;
      pageCounter += 1;
      if (pageCounter % maxPagePerSession === 0) {
        console.log("Cleaning up/closing page at: " + pageCounter);
        await runner.pageReset();
      }
    }
    catch (error) {
      data[url] = error;
      res.status(500);
      console.log(error);
      errCounter += 1;
      if (errCounter >= maxErr) {
        console.error("Internal err counter breached");
        process.exit();
      }
    }
  };

  counter += 1;
  if (counter > maxReqsPerSession) {
    console.log("Restarting browser after " + counter + " reqs");
    await runner.cleanup();
    counter = 0;
  }
  return res.json( data );
  
});

app.listen(port, () =>
  console.log(`Scraper listening on port ${port}!`)
);

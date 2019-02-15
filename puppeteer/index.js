const express = require("express");
const app = express();
const bodyParser = require("body-parser");
const runner = require("./puppeteer");
const port = process.env.PORT || 3000;
const maxReqsPerSession = process.env.MAX_REQS || 500;
var counter = 0;

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
    }
    catch (error) {
      data[url] = error;
      res.status(500);
      console.log(error)
    }
  };

  counter += 1;
  if (counter > maxReqsPerSession) {
    console.log("Restarting browser after " + counter + " reqs");
    runner.cleanup();
    counter = 0;
  }
  return res.json( data );
  
});

app.listen(port, () =>
  console.log(`Scraper listening on port ${port}!`)
);
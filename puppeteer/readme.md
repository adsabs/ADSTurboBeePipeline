This docker container will deploy both python and node js components.

# Chromium

A daemon will be started with `pm start process.json`; which in turn stars (n) instances of an express
server; each with its own chromium browser. The instances are load balanced and are accessible through
port 3000 (locally).

endpoints:

    /scrape - accepts POST request with a list of urls; each url will be loaded by chromium and we'll
              return the following structure:

              {
                  url1: 'html content',
                  url2: 'html content'
              }

Since we are running multiple instances of the service; it is recommended that you contant /scrape
endpoint with just one url - the load will be distributed across browsers.

You can test it with:

```curl 'localhost:3001/scrape' -X POST -d '["https://dev.adsabs.harvard.edu/#abs/2019LRR....22....1I/abstract"]' -H 'Content-Type: application/json'```

## To restart

    `docker exec <name> restart process.json





# PM2 Process Manager
It will take care of concurrency and fallback problems. It will run Xvfb for you, with a fake display, so headless:false can be run perfectly. There are some dependencies needed, check the dockerfile for those.

- You can install it using `npm i -g pm2`, 
- and then run with `pm2 start process.json` on this folder.

# Dockerfile
If you run the dockerfile with `sh start.sh`, it will install all dependencies, run xvfb, script, and remove once it is exited. You can edit that file and change behavior to --restart always to make sure it restarts on error.


# Credits

Inspiration for the js part of code: https://github.com/nsourov/Puppeteer-with-xvfb.git

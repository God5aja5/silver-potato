import express from "express";
import axios from "axios";

const app = express();

const url = `https://silver-potato-mudw.onrender.com`;
const interval = 30000;

function reloadWebsite() {
  axios
    .get(url)
    .then((response) => {
      console.log("website reloaded");
    })
    .catch((error) => {
      console.error(`Error : ${error.message}`);
    });
}

setInterval(reloadWebsite, interval);

app.get("/", (req, res) => {
  res.send("hello world");
});

const port = 4000;

app.listen(port, () => {
  console.log(`server is running on port ${port}`);
});

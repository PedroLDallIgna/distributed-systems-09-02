const express = require("express");
const mysql = require("mysql2");
const morgan = require("morgan");

const con = mysql.createConnection({
  host: "mysql",
  user: "user",
  password: "password",
  database: "messages",
});

const CREATE_EVENT_QUERY = "INSERT INTO Events (id) VALUES (?)";
const GET_ALL_EVENTS = "SELECT id, valor FROM Events";
const GET_EVENT_BY_ID = "SELECT valor FROM Events WHERE id = ?";
const GET_STATUS_ID = "SELECT * FROM DBStatus";
const UPDATE_STATUS_ID = "UPDATE DBStatus SET id = ?";

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan("combined"));

app.use((req, res, next) => {
  res.set({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers":
      "Origin, X-Requested-With, Content-Type, Accept",
    "x-service-language": "nodejs",
  });
  next();
});

app.get("/", (req, res) => {
  // get all events
  con.query(GET_STATUS_ID, (err, results) => {
    if (err) throw err;
    return res.json({ events: results[0] });
  });
});

app.get("/:id", (req, res) => {
  // get event by id
  const { id } = req.params;
  con.query(GET_EVENT_BY_ID, [id], (err, results) => {
    if (err) throw err;
    return res.json({ valor: results[0] });
  });
});

const createEvent = () => {
  return new Promise((resolve, reject) => {
    con.query(GET_STATUS_ID, (err, results) => {
      if (err) throw err;
      const lastId = results[0]?.id;
      const newId = lastId + 1;

      con.query(CREATE_EVENT_QUERY, [newId], (err, results) => {
        if (err) reject(err);

        con.query(UPDATE_STATUS_ID, [newId], (err, results) => {
          if (err) reject(err);
          resolve(newId);
        });
      });
    });
  });
};

app.post("/create-sync", (req, res) => {
  // create a new event synchronously
  createEvent()
    .then((result) => {
      const interval = setInterval(() => {
        con.query(GET_EVENT_BY_ID, [result], (err, results) => {
          if (err) {
            clearInterval(interval);
            return res.status(500).json({ error: err.message });
          }
          const event = results[0];
          if (event && event.valor && event.valor !== "") {
            clearInterval(interval);
            return res.json({ valor: event.valor });
          }
        });
      }, 100);
    })
    .catch((err) => {
      return res.status(500).json({ error: err.message });
    });
});

app.post("/create-async", (req, res) => {
  // create a new event asynchronously
  createEvent()
    .then((result) => {
      res.status(202).json({ message: "Event created on demand", id: result });
    })
    .catch((err) => {
      return res.header().status(500).json({ error: err.message });
    });
});

app.listen(5000, () => {
  con.connect((err) => {
    if (err) throw err;
    console.log("Connected to database");
  });

  console.log("Running on port 5000");
});

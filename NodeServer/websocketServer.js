// // Node.js socket server script
// const net = require('net');
// // Create a server object
// const server = net.createServer((socket) => {
//   socket.on('data', (data) => {
//     console.log(data.toString());
//   });
//   socket.write('SERVER: Hello! This is server speaking.<br>');
//   socket.end('SERVER: Closing connection now.<br>');
// }).on('error', (err) => {
//   console.error(err);
// });
// // Open server on port 9898
// server.listen(9898, () => {
//   console.log('opened server on', server.address().port);
// });


// const webSocketsServerPort = 9898;
// const webSocketServer = require('websocket').server;
// const http = require('http');
// // Spinning the http server and the websocket server.
// const server = http.createServer();
// server.listen(webSocketsServerPort);
// const wsServer = new webSocketServer({
//   httpServer: server
// });
//
// // I'm maintaining all active connections in this object
// const clients = {};
//
// // This code generates unique userid for everyuser.
// const getUniqueID = () => {
//   const s4 = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
//   return s4() + s4() + '-' + s4();
// };
//
// wsServer.on('request', function(request) {
//   var userID = getUniqueID();
//   console.log((new Date()) + ' Recieved a new connection from origin ' + request.origin + '.');
//   // You can rewrite this part of the code to accept only the requests from allowed origin
//   const connection = request.accept(null, request.origin);
//   clients[userID] = connection;
//   console.log('connected: ' + userID + ' in ' + Object.getOwnPropertyNames(clients))
//
// });
//
// wsServer.on('connection', ws => {
//   ws.on('message', message => {
//     console.log(`Received message => ${message}`)
//   })
//   ws.send('ho!')
// });

var MongoClient = require('mongodb').MongoClient;
//var url = "mongodb://localhost:27017/";
var url = "mongodb+srv://pchwalek:jOn2Ufkv6k0WBW0F@captivates.jopky.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
const struct = require('python-struct');


const captivateHeaderSizes = {'blink_data': '100s',
                          'blink_tick_ms': 'I',
                          'blink_payload_ID': 'I',

                          'temple_temp': 'H',
                          'temple_therm': 'H',
                          'temple_tick_ms': 'I',
                          'nose_temp': 'H',
                          'nose_therm': 'H',
                          'nose_tick_ms': 'I',
                          'temp_sec_tick_ms': 'I',
                          'temp_sec_epoch': 'I',

                          'quatI': 'f',
                          'quatJ': 'f',
                          'quatK': 'f',
                          'quatReal': 'f',
                          'quatRadianAccuracy': 'f',
                          'rot_tick_ms': 'I',
                          'activityConfidence': '9s',
                          'tick_ms_activity': 'I',

                          'pos_x': 'f',
                          'pos_y': 'f',
                          'pos_z': 'f',
                          'pos_accuracy': 'f',
                          'tick_ms_pos': 'I',
                          'pos_epoch': 'I',

                          'packet_tick_ms': 'I',
                          'packet_epoch': 'I'}

      // const captivateHeaderSizes = {'packet_epoch': 'I',
      //                               'packet_tick_ms': 'I',
      //
      //                               'pos_epoch': 'I',
      //                               'tick_ms_pos': 'I',
      //                               'pos_accuracy': 'f',
      //                               'pos_z': 'f',
      //                               'pos_y': 'f',
      //                               'pos_x': 'f',
      //
      //                               'tick_ms_activity': 'I',
      //                               'activityConfidence': '9s',
      //                               'rot_tick_ms': 'I',
      //                               'quatRadianAccuracy': 'f',
      //                               'quatReal': 'f',
      //                               'quatK': 'f',
      //                               'quatJ': 'f',
      //                               'quatI': 'f',
      //
      //                               'temp_sec_epoch': 'I',
      //                               'temp_sec_tick_ms': 'I',
      //                               'nose_tick_ms': 'I',
      //                               'nose_therm': 'H',
      //                               'nose_temp': 'H',
      //                               'temple_tick_ms': 'I',
      //                               'temple_therm': 'H',
      //                               'temple_temp': 'H',
      //
      //                               'blink_payload_ID': 'I',
      //                               'blink_tick_ms': 'I',
      //                               'blink_data': '100s'}

const captivateKeys = Object.keys(captivateHeaderSizes)

var structSizeString = ""
for (const [key, value] of Object.entries(captivateHeaderSizes)) {
  structSizeString += value
}
const structSize = struct.sizeOf(structSizeString);

// console.log(structSize)

const zipObject = (props, values) => {
  return props.reduce((prev, prop, i) => {
    return Object.assign(prev, { [prop]: values[i] });
  }, {});
};

function captivateFilter(clientAddr, serverTimestamp, packetRaw){
  serverData = {source: clientAddr,
                    serverTimestamp: serverTimestamp}
  parsedPayload = struct.unpack(structSizeString, Buffer.from(packetRaw, 'hex'))
  mergedPayload = zipObject(captivateKeys, parsedPayload)

  packetFiltered = {...serverData, ...mergedPayload}
  return packetFiltered
}

MongoClient.connect(url, {useNewUrlParser: true, useUnifiedTopology: true}, function(err, db) {
  if (err) throw err;


  const WebSocket = require('ws');

  const wss = new WebSocket.Server({ port: 9898 });

  var packetTracker = 0;

  function noop() {}

  function heartbeat() {
    this.isAlive = true;
  }

  wss.on('connection', function connection(ws) {
    var dbo = db.db("captivateServer");
    var clientAddr = ws._socket.remoteAddress
    var timeInMs;

    ws.on('message', function incoming(message) {


      packetFiltered = captivateFilter(clientAddr, Date.now(), message)
      dbo.collection("captivateFiltered").insertOne(packetFiltered, function(err, res) {
        if (err) throw err;
      packetTracker += 1
      console.log(packetTracker)
      // console.log(message.length)
      // console.log(message)
      // console.log(packetFiltered.nose_temp)
        //console.log("1 document inserted");

      });

  //     var myobj = { source: clientAddr, serverTimestamp: Date.now(), payload: message };
  //     dbo.collection("captivateRaw").insertOne(myobj, function(err, res) {
  //       if (err) throw err;
 	// packetTracker += 1
 	// console.log(packetTracker)
  //       //console.log("1 document inserted");
  //
  //     });

    });
    ws.on('close', function close() {
      // db.close();
      console.log('disconnected')
    });
    ws.isAlive = true;
    ws.on('pong', heartbeat);
  });

  const interval = setInterval(function ping() {
    wss.clients.forEach(function each(ws) {
      if (ws.isAlive === false)  {
        return ws.terminate()
      }
      ws.isAlive = false;
      ws.ping(noop);
    });
  }, 30000);

  wss.on('close', function close() {
    clearInterval(interval);
    db.close();
    console.log('closing connection entirely')
  });



  // var myobj = { payload: message };
  // dbo.collection("customers").insertOne(myobj, function(err, res) {
  //   if (err) throw err;
  //   console.log("1 document inserted");
  //   db.close();
  // });
});

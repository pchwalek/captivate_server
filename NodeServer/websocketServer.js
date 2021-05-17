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


/*const inertialHeaderSizes = {
    'x_1': 'H',
    'y_1': 'H',
    'z_1': 'H',
    'imu_tick_1': 'H',
    'tick_1': 'I',
    'accuracy_1': 'f',

    'x_2': 'H',
    'y_2': 'H',
    'z_2': 'H',
    'imu_tick_2': 'H',
    'tick_2': 'I',
    'accuracy_2': 'f',

    'x_3': 'H',
    'y_3': 'H',
    'z_3': 'H',
    'imu_tick_3': 'H',
    'tick_3': 'I',
    'accuracy_3': 'f',

    'x_4': 'H',
    'y_4': 'H',
    'z_4': 'H',
    'imu_tick_4': 'H',
    'tick_4': 'I',
    'accuracy_4': 'f',

    'x_5': 'H',
    'y_5': 'H',
    'z_5': 'H',
    'imu_tick_5': 'H',
    'tick_5': 'I',
    'accuracy_5': 'f',

    'x_6': 'H',
    'y_6': 'H',
    'z_6': 'H',
    'imu_tick_6': 'H',
    'tick_6': 'I',
    'accuracy_6': 'f',

    'x_7': 'H',
    'y_7': 'H',
    'z_7': 'H',
    'imu_tick_7': 'H',
    'tick_7': 'I',
    'accuracy_7': 'f',

    'x_8': 'H',
    'y_8': 'H',
    'z_8': 'H',
    'imu_tick_8': 'H',
    'tick_8': 'I',
    'accuracy_8': 'f',

    'x_9': 'H',
    'y_9': 'H',
    'z_9': 'H',
    'imu_tick_9': 'H',
    'tick_9': 'I',
    'accuracy_9': 'f',

    'x_10': 'H',
    'y_10': 'H',
    'z_10': 'H',
    'imu_tick_10': 'H',
    'tick_10': 'I',
    'accuracy_10': 'f',

    'x_11': 'H',
    'y_11': 'H',
    'z_11': 'H',
    'imu_tick_11': 'H',
    'tick_11': 'I',
    'accuracy_11': 'f',

    'x_12': 'H',
    'y_12': 'H',
    'z_12': 'H',
    'imu_tick_12': 'H',
    'tick_12': 'I',
    'accuracy_12': 'f',

    'x_13': 'H',
    'y_13': 'H',
    'z_13': 'H',
    'imu_tick_13': 'H',
    'tick_13': 'I',
    'accuracy_13': 'f',

    'x_14': 'H',
    'y_14': 'H',
    'z_14': 'H',
    'imu_tick_14': 'H',
    'tick_14': 'I',
    'accuracy_14': 'f',
}*/

const metadataSizes = {
    'desc': 'I',
    'packetIdx': 'I'
}

const inertialPayloadSizes = {
    'x': 'H',
    'y': 'H',
    'z': 'H',
    'imu_tick': 'H',
    'tick': 'I',
    'accuracy': 'f',
}


/*const inertialHeaderSizes = {
    'desc': 'I',
    'packetIdx': 'I',
    'data': '224s',

}*/

//const inertialHeaderSizes = {
//    'pos_x': 'H',
//    'pos_y': 'H',
//    'pos_z': 'H',
//    'IMU_tick': 'H',
//    'accuracy': 'f',
//}

const captivateKeys = Object.keys(captivateHeaderSizes)
var structSizeString = ""
for (const [key, value] of Object.entries(captivateHeaderSizes)) {
  structSizeString += value
}
const structSize = struct.sizeOf(structSizeString);
console.log("Original packet size: ");
console.log(structSize);

// Meatadata
const metadatalKeys = Object.keys(metadataSizes)
var structMetadataSizeString = ""
for (const [key, value] of Object.entries(metadataSizes)) {
    structMetadataSizeString += value
}
const structMetadataSize = struct.sizeOf(structMetadataSizeString);
console.log("Metadata size: ");
console.log(structMetadataSize);

// Inertial Payload
const inertialPayloadKeys = Object.keys(inertialPayloadSizes)
var structInertialPayloadSizeString = ""
for (const [key, value] of Object.entries(inertialPayloadSizes)) {
    structInertialPayloadSizeString += value
}
const structInertialPayloadSize = struct.sizeOf(structInertialPayloadSizeString);
console.log("Inertial payload size: ");
console.log(structInertialPayloadSize);

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

function inertialData(clientAddr, serverTimestamp, packetRaw) {
    serverData = {
        source: clientAddr,
        serverTimestamp: serverTimestamp
    }

    //console.log(Buffer.from(packetRaw, 'hex'))
    //parsedPayload = struct.unpack('IIHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIfHHHHIf', Buffer.from(packetRaw, 'hex'))
   // console.log(parsedPayload);


    // grab header
    parsedPayload = struct.unpack(structMetadataSizeString, Buffer.from(packetRaw, 'hex'))

    //populate payload fields
    payload = packetRaw.substring(16)
    numOfElements = payload.length / structInertialPayloadSize / 2 //divide by 2 since the hex is represented as string so 1 bytes = 2 characters

    payloadElements = { }
    for (i = 0; i < numOfElements; i++) {
        payloadElement = struct.unpack(structInertialPayloadSizeString, Buffer.from(payload, 'hex'))
        mergedPayloadElement = zipObject(inertialPayloadKeys, payloadElement)
        payloadElements[i.toString()] = mergedPayloadElement
        payload = payload.substring(structInertialPayloadSize * 2)
    }

   // structInertialPayloadSizeString
   //  structInertialPayloadSize

/*    console.log(parsedPayload);
    console.log(Buffer.from(packetRaw, 'hex'));
    console.log(packetRaw.substring(16).length)
    console.log(typeof packetRaw)*/

    //console.log(Buffer.from(parsedPayload.data,'hex'));

    //for (const [key, value] of Object.entries(Buffer.from(packetRaw, 'hex'))) {
    //    console.log(value)
    //}

    mergedPayload = zipObject(metadatalKeys, parsedPayload)
    packetFiltered = { ...serverData, ...mergedPayload }
    packetFiltered.payload = payloadElements

    //packetFiltered.payload = packetRaw.substring(16);
    //console.log(packetFiltered.data.length);

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


     // packetFiltered = captivateFilter(clientAddr, Date.now(), message)
     // dbo.collection("captivateFiltered").insertOne(packetFiltered, function(err, res) {
     //     if (err) throw err;

      packetFiltered = inertialData(clientAddr, Date.now(), message)
      dbo.collection("inertialMeas").insertOne(packetFiltered, function (err, res) {
          if (err) throw err;

      packetTracker += 1
      console.log(packetTracker)
      // console.log(message.length)
      // console.log(message)
      //console.log(packetFiltered.data)
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

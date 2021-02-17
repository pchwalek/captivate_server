var MongoClient = require('mongodb').MongoClient;
const struct = require('python-struct');
const url = "mongodb://localhost:27017/";

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

const captivateKeys = Object.keys(captivateHeaderSizes)

var structSizeString = ""
for (const [key, value] of Object.entries(captivateHeaderSizes)) {
  structSizeString += value
}
const structSize = struct.sizeOf(structSizeString);

const zipObject = (props, values) => {
  return props.reduce((prev, prop, i) => {
    return Object.assign(prev, { [prop]: values[i] });
  }, {});
};

function captivateFilter(packetRaw){
  serverData = {source: packetRaw.source,
                    serverTimestamp: packetRaw.serverTimestamp}
  console.log(packetRaw)
  console.log(packetRaw.payload)
  parsedPayload = struct.unpack(structSizeString, Buffer.from(packetRaw.payload))
  mergedPayload = zipObject(captivateKeys, parsedPayload)

  packetFiltered = {...serverData, ...mergedPayload}
  return packetFiltered
}

function resolveAfter2Seconds() {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve('resolved');
    }, 2000);
  });
}


MongoClient.connect(url, function(err, db) {
  if (err) throw error;
  var dbo = db.db("captivateServer");


  dbo.collection("captivateRaw").findOneAndDelete({}, function(err, result) {
    if (err) throw err
    // console.log(result.source);
    // console.log(result.payload);
    // parsedPacket = struct.unpack(structSizeString, Buffer.from(result.payload))
    // const merged = zipObject(captivateKeys, parsedPacket)
    packetFiltered = captivateFilter(result.value)
    console.log(packetFiltered)

    dbo.collection("captivateRaw").find({}).toArray(function(err, result) {
        if (err) throw err;
        console.log(result);
      });
      db.close();
  });




//   dbo.collection("captivateRaw").findOne({}, function(err, result) {
//     if (err) throw err;
//     // console.log(result.source);
//     // console.log(result.payload);
//     // parsedPacket = struct.unpack(structSizeString, Buffer.from(result.payload))
//     // const merged = zipObject(captivateKeys, parsedPacket)
//     packetFiltered = captivateFilter(result)
//     console.log(packetFiltered)
// //     dbo.collection("captivateFiltered").insertOne(packedFiltered, function(err, res) {
// //       if (err) throw err;
// // packetTracker += 1
// // console.log(packetTracker)
// //       //console.log("1 document inserted");
// //
// //     });
//       dbo.collection("captivateRaw").deleteOne(result, function(err, obj) {
//       if (err) throw err;
//       console.log("1 document deleted");
//     });
//     db.close();
//   });

});

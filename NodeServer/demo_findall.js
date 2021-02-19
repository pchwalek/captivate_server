var MongoClient = require('mongodb').MongoClient;

var MongoClient_2 = require('mongodb').MongoClient;

var url = "mongodb://localhost:27017/";

var url_2 = "mongodb+srv://pchwalek:jOn2Ufkv6k0WBW0F@captivates.jopky.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

MongoClient_2.connect(url_2, {useNewUrlParser: true, useUnifiedTopology: true}, function(err, db_2) {
    if (err) {
      console.log(err)
      throw err;
    }
    MongoClient.connect(url, {useNewUrlParser: true, useUnifiedTopology: true}, function(err, db) {
      if (err) throw err;
      var dbo = db.db("captivateServer");
      dbo.collection("captivateFiltered").find({}).toArray(function(err, result) {
        if (err) throw err;
        console.log(result);

        var dbo_2 = db_2.db("captivateServer");
        dbo_2.collection("captivateFiltered").insertMany(result, function(err, res) {
          if (err) throw err;
          console.log("Number of documents inserted: " + res.insertedCount);
          db_2.close();
          db.close();
        });

      });
    });

})


const uid = document.cookie.split("=")[1];
const keepaliveinterval = 10;
const params = (window.location.search).split("magnet=")[1].split("&nyaaid=");
const magnet = params[0];
const nyaaid = params[1];
var srcset = false;
var subsarray = [];

function socks(message) {
   var blob = JSON.stringify({"message":message,"uid":uid,"magnet":magnet,"nyaaid":nyaaid})

   if (ws) {
      ws.send(blob);
   }
   ws.onclose = function() {
      console.log("Closed");            
   }
   
}

window.addEventListener('load',function(){
   ws = new WebSocket("ws://"+window.location.hostname+":8080/ws");
   if (ws) {
      ws.onopen = function() {
         console.log("Connected to Server");
         socks("started");
         socks("keepalive");
      }

      ws.onclose = function(e) {
         console.log("Connection closed (wasClean = " + e.wasClean + ", code = " + e.code + ", reason = '" + e.reason + "')");
         
      }

      ws.onmessage = function(e) {
         var data = JSON.parse(e.data);
         console.log("Got echo: " + e.data);
         if (data.message==="ready"){
           var addr = "http://"+window.location.hostname+":"+data.port+"/"+data.addr[0];
           setplayer(addr,data.subtitles,0);
           }
        }

   }
})


function subsload(subs,index){
   console.log(subs,index,)
   var player = videojs("#player");
   for (var tracks in subs[1]){
      subsarray.push(tracks)
   }   
   if (subsarray.length > 0){
      var subdir = subsarray[index];
      var track = subs[1][subdir];
   }
   var url = '/subs/subtitles/'+subdir+"/"+track
   console.log(url)

   player.ready(function () {

      var video = this.tech_.el_;
      window.SubtitlesOctopusOnLoad = function () {
          var options = {
              video: video,
              subUrl: url,
              //onReady: onReadyFunction,
              debug: true,
              workerUrl: '/static/subtitles-octopus-worker.js',
              legacyWorkerUrl: '/static/libassjs-worker-legacy.js' 
          };
          window.octopusInstance = new SubtitlesOctopus(options); // You can experiment in console
      };
      if (SubtitlesOctopus) {
          SubtitlesOctopusOnLoad();
      }
  });

   

}

function setplayer(addr,subtitles,currindex) {
   var player = videojs("#player");
   if (srcset != true){
      player.src({
         type: 'video/webm',
         src: addr
      })
      player.load();
      srcset = true;
      subsload(subtitles,currindex)
      
   }

}



keepalivetimer = setInterval(function() {

   socks("keepalive")

},keepaliveinterval*1000)
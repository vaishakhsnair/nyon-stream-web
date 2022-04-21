
const uid = document.cookie.split("=")[1];
const keepaliveinterval = 10;
const params = new URLSearchParams(window.location.search);
const magnet = params.get("magnet");
var srcset = false;

function socks(message) {
   var blob = JSON.stringify({"message":message,"uid":uid,"magnet":magnet})

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
           setplayer(addr);
           }
        }

   }
})




function setplayer(addr) {
   var player = document.getElementById("player");
   var playersrc = document.getElementById("playersrc");
   playersrc.setAttribute("src",addr);
   if (srcset != true){
      player.load();
      srcset = true;
   }

}



keepalivetimer = setInterval(function() {

   socks("keepalive")

},keepaliveinterval*1000)
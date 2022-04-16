
      window.addEventListener('load',function(){
        socks("open");
       } )


      function socks(message) {
         var ws = new WebSocket("ws://localhost:8080/ws");
         var blob = new Blob([JSON.stringify({"message":message,"uid":uid,"thread":threadid})],{type:'application/json; charset=UTF-8'});

         ws.onopen = function() {
            ws.send(blob);
         }
         ws.onmessage = function(event) {
            var cont = event.data;
            console.log(cont);          
           // ws.close();
         
         }
         ws.onclose = function() {
            console.log("Closed");            
         }
         
      }

      keepalivetimer = setInterval(function() {

         socks("keepalive")

      },keepaliveinterval*1000)
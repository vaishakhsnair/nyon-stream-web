function statsmonitor(){
    var statspace = document.getElementById("stats");
    statspace.innerHTML = "";

    window.addEventListener('load',function(){
        wstat = new WebSocket("ws://"+window.location.hostname+":8070/ws");
        if (wstat){
            ws.onopen = function(){
                console.log("Statistics server loaded");
                ws.send(uid);
            }
            wstat.onmessage = function(event){
                statspace.innerHTML = ""
                statspace.innerHTML += event.data; 
            }
            wstat.onclose = function(e){
                console.log("Connection closed (wasClean = " + e.wasClean + ", code = " + e.code + ", reason = '" + e.reason + "')");
            }
        }

    })
}
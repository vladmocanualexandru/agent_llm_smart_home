function renderDevices(){
    fetch('/devices')
        .then(response => response.json())
        .then(devices => {
            let room = document.getElementById("room");
            let sensorsTable = document.getElementById("sensorsTable");

            for (let prop in devices) {
                if (devices.hasOwnProperty(prop)) {
                    let device = devices[prop];

                    if (device.type === "control") {
                        let control = document.createElement("div");
                        control.className = "control";
                        control.classList.add(device.ui.icon);
                        if (device.activated) {
                            control.classList.add("activated");
                        }
                        control.style.left = device.ui.x + "%";
                        control.style.top = device.ui.y + "%";
                        control.id = "control_" + prop;

                        control.addEventListener("click", function(a,b,c) {
                            fetch(`/device/${prop}/toggle`, { method: "GET" });
                            $(this).toggleClass("activated");
                        });

                        room.appendChild(control);
                    } else if (device.type === "sensor") {
                        let sensor = document.createElement("tr");
                        sensor.className = "sensor";
                        sensor.id = "sensor_" + prop;
                        sensor.innerHTML = `<td>${prop}</td><td>${Number(device.data.value).toFixed(2)}</td><td>${device.data.unit}</td>`;
                        sensorsTable.appendChild(sensor);
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error fetching devices:', error);
        });
}


function updateRoom() {
    let sensors = document.querySelectorAll(".sensor");
    sensors.forEach(sensor => sensor.classList.add("old"));

    fetch('/devices')
        .then(response => response.json())
        .then(devices => {
            let room = document.getElementById("room");
            let sensorsTable = document.getElementById("sensorsTable");

            for (let prop in devices) {
                if (devices.hasOwnProperty(prop)) {
                    let device = devices[prop];

                    if (device.type === "control") {
                        let control = $("#control_"+prop)
                        
                        if (device.activated) {
                            control.addClass("activated");
                        } else {
                            control.removeClass("activated")
                        }
                    } else if (device.type === "sensor") {
                        let sensor = document.createElement("tr");
                        sensor.className = "sensor";
                        sensor.id = "sensor_" + prop;
                        sensor.innerHTML = `<td>${prop}</td><td>${Number(device.data.value).toFixed(2)}</td><td>${device.data.unit}</td>`;
                        sensorsTable.appendChild(sensor);
                    }
                }
            }

            let old_stuff = document.querySelectorAll(".old");
            old_stuff.forEach(old_stuff => old_stuff.remove());
        })
        .catch(error => {
            console.error('Error fetching devices:', error);
        });
}

document.addEventListener("DOMContentLoaded", function() {
    
    renderDevices();
    setInterval(updateRoom, 1000);

});
document.addEventListener("DOMContentLoaded", function() {
            
    fetch('/devices')
        .then(response => response.json())
        .then(devices => {
            let room = document.getElementById("room")
            let sensorsTable = document.getElementById("sensorsTable")

            for (let prop in devices) {
                if (devices.hasOwnProperty(prop)) {
                    let device = devices[prop]

                    if (device.type === "control") {

                        let control = document.createElement("div");
                        control.className = "control";
                        control.classList.add(device.ui.icon);
                        control.style.left = device.ui.x + "%";
                        control.style.top = device.ui.y + "%";
                        control.id = "control_" + prop;

                        room.appendChild(control);
                    } else if (device.type === "sensor") {
                        //create a tr element with prop, device.data.value, device.data.unit as td elements
                        let sensor = document.createElement("tr");
                        sensor.id = "sensor_" + prop;
                        sensor.innerHTML = "<td>" + prop + "</td><td>" + device.data.value + "</td><td>" + device.data.unit + "</td>";
                        sensorsTable.appendChild(sensor);
                    }
                }
            }

        })
        .catch(error => {
            console.error('Error fetching devices:', error);
        });
});